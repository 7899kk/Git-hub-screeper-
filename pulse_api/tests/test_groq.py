"""Mock provider responses verify grounding; no live-price claims or released fixtures."""

import json

import httpx
import pytest
from backend.connectors.amazon import PlatformConnector
from backend.models import CollectionError
from fastapi.testclient import TestClient
from pulse_api.app import create_app
from pulse_api.collectors import convert, with_groq
from pulse_api.domain import match
from pulse_api.groq import ENDPOINT, extract
from pulse_api.storage import Base

URL = "https://www.amazon.in/dp/B000000001"
HTML = """<h1>Test Brand Phone 256GB</h1><div>Brand: Test Brand</div>
<p>Model: T1</p><p>Storage: 256GB</p><p>Seller: Test Seller</p>
<p>Selling price: ₹12,345.67</p><p>Shipping: INR 50.00</p>
<p>10% bank offer subject to eligibility</p>"""
DETAILS = {
    "title": "Test Brand Phone 256GB",
    "price_quote": "Selling price: ₹12,345.67",
    "brand": "Test Brand",
    "model": "T1",
    "variant": {"storage": "256GB"},
    "seller": "Test Seller",
    "shipping_quote": "Shipping: INR 50.00",
    "offers": ["10% bank offer subject to eligibility"],
}


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setenv("PULSE_GROQ_KEY", "test-key-not-a-credential")


def mock_response(data=None, status=200, finish="stop"):
    def handle(request):
        assert str(request.url) == ENDPOINT
        assert request.headers["authorization"] == "Bearer test-key-not-a-credential"
        payload = json.loads(request.content)
        assert payload["response_format"] == {"type": "json_object"}
        evidence = json.loads(payload["messages"][1]["content"])
        assert evidence["selling_price_quote"] == DETAILS["price_quote"]
        assert "test-key" not in payload["messages"][1]["content"]
        return httpx.Response(
            status,
            json={
                "choices": [
                    {
                        "finish_reason": finish,
                        "message": {"content": json.dumps(DETAILS if data is None else data)},
                    }
                ]
            },
        )

    return httpx.MockTransport(handle)


def test_price_from_page_and_details_separate():
    row = extract(PlatformConnector(), HTML, URL, mock_response())
    assert row.price == 1234567
    assert row.shipping == 5000
    assert row.price_evidence == DETAILS["price_quote"]
    assert row.offers == DETAILS["offers"]
    assert row.condition == "unknown" and row.availability == "unknown"
    assert row.timestamp.tzinfo is not None
    assert match(row.model_dump(), row.model_dump())["status"] == "unverified"


@pytest.mark.parametrize(
    "changes",
    [
        {"price_quote": "Selling price: ₹9,999"},
        {"title": "Other product"},
        {"price": 999900},
        {"brand": "Invented Brand"},
        {"variant": {"storage": "128GB"}},
        {"variant": {"imaginary": "256GB"}},
        {"offers": ["10% bank offer"]},
        {"shipping_quote": "Shipping: INR 0.00"},
    ],
)
def test_hallucinated_or_altered_fields_rejected(changes):
    with pytest.raises(CollectionError):
        extract(PlatformConnector(), HTML, URL, mock_response({**DETAILS, **changes}))


@pytest.mark.parametrize(
    "html",
    [
        HTML.replace("Selling price", "MRP"),
        HTML.replace("₹12,345.67", "12345.67"),
        HTML + "<p>Sale price: INR 9999</p>",
        HTML + "<h1>Related product</h1>",
        HTML.replace("<p>Selling price", "<p hidden>Selling price"),
        "<h1>Test product</h1><script>Selling price: INR 12</script>",
    ],
)
def test_unsupported_page_never_calls_model(html):
    def forbidden(request):
        pytest.fail("No model call is permitted without unambiguous source evidence")

    with pytest.raises(CollectionError, match="one product heading"):
        extract(PlatformConnector(), html, URL, httpx.MockTransport(forbidden))


@pytest.mark.parametrize("status", [401, 429, 500, 302])
def test_errors_and_redirects_do_not_expose_provider_body(status):
    with pytest.raises(CollectionError, match=f"HTTP {status}") as exc:
        extract(PlatformConnector(), HTML, URL, mock_response(status=status))
    assert "test-key" not in str(exc.value)


def test_truncated_response_rejected():
    with pytest.raises(CollectionError, match="valid complete"):
        extract(PlatformConnector(), HTML, URL, mock_response(finish="length"))


def test_free_shipping_and_oversized_provider_response():
    page = HTML.replace("Shipping: INR 50.00", "Shipping: INR 0.00")
    row = extract(
        PlatformConnector(),
        page,
        URL,
        mock_response({**DETAILS, "shipping_quote": "Shipping: INR 0.00"}),
    )
    assert row.shipping == 0
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=b"x" * 65537))
    with pytest.raises(CollectionError, match="response exceeds"):
        extract(PlatformConnector(), HTML, URL, transport)


def test_invalid_json_and_network_error_are_sanitized():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=b"{bad"))
    with pytest.raises(CollectionError, match="valid complete"):
        extract(PlatformConnector(), HTML, URL, transport)

    def failed(request):
        raise httpx.ConnectError("sensitive-provider-body", request=request)

    with pytest.raises(CollectionError, match="request failed") as exc:
        extract(PlatformConnector(), HTML, URL, httpx.MockTransport(failed))
    assert "sensitive-provider-body" not in str(exc.value)


def test_ambiguous_structured_offers_never_reach_groq(monkeypatch):
    import pulse_api.groq as groq

    monkeypatch.setattr(
        groq, "extract", lambda *args: pytest.fail("Ambiguous offers must not reach Groq")
    )
    html = (
        HTML
        + '<script type="application/ld+json">'
        + json.dumps(
            {
                "@type": "Product",
                "name": "Test Brand Phone 256GB",
                "offers": [
                    {"@type": "Offer", "price": 12, "priceCurrency": "INR"},
                    {"@type": "Offer", "price": 13, "priceCurrency": "INR"},
                ],
            }
        )
        + "</script>"
    )
    connector = with_groq(PlatformConnector())
    with pytest.raises(CollectionError, match="Multiple offers"):
        connector.parse(html, URL)


def test_missing_key_no_model_call(monkeypatch):
    monkeypatch.delenv("PULSE_GROQ_KEY")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(CollectionError, match="securely configured"):
        extract(PlatformConnector(), HTML, URL, mock_response())


def test_supported_connector_uses_same_permitted_page(monkeypatch):
    import pulse_api.groq as groq

    original = groq.extract
    monkeypatch.setattr(
        groq,
        "extract",
        lambda connector, html, url: original(connector, html, url, mock_response()),
    )
    requests = []

    def transport(url):
        requests.append(url)
        return "User-agent: *\nAllow: /" if url.endswith("robots.txt") else HTML

    connector = with_groq(PlatformConnector(transport=transport))
    row = convert(connector, connector.collect(URL))
    assert row.price == 1234567
    assert len(requests) == 2  # one robots check, one page; no second retailer fetch


def test_robots_and_challenges_never_reach_groq(monkeypatch):
    import pulse_api.groq as groq

    monkeypatch.setattr(
        groq, "extract", lambda *args: pytest.fail("blocked pages must not reach Groq")
    )
    denied = with_groq(PlatformConnector(transport=lambda url: "User-agent: *\nDisallow: /"))
    with pytest.raises(CollectionError, match="disallows"):
        denied.collect(URL)
    challenge = with_groq(
        PlatformConnector(
            transport=lambda url: (
                "User-agent: *\nAllow: /" if url.endswith("robots.txt") else HTML + "captcha"
            )
        )
    )
    with pytest.raises(CollectionError, match="Challenge"):
        challenge.collect(URL)


def test_status_is_configuration_not_live_verification(tmp_path, monkeypatch):
    app = create_app("sqlite:///" + str(tmp_path / "status.db"))
    Base.metadata.create_all(app.state.sessions.kw["bind"])
    with TestClient(app) as client:
        assert client.get("/providers/status").status_code == 401
        token = client.post("/sessions").json()["token"]
        client.headers["Authorization"] = "Bearer " + token
        response = client.get("/providers/status")
        assert response.json()["groq"]["configured"] is True
        assert "not been checked" in response.json()["groq"]["message"]
        assert "test-key" not in response.text
        monkeypatch.delenv("PULSE_GROQ_KEY")
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        assert client.get("/providers/status").json()["groq"]["configured"] is False
