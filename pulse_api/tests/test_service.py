"""Synthetic fixtures are confined to tests; the application has no demo mode."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from pulse_api.app import create_app
from pulse_api.collectors import SingleObservation, process_jobs
from pulse_api.domain import ListingInput, analyze, match, safe_url, statistics, utcnow
from pulse_api.providers import LicensedFeed, ingest, outbound
from pulse_api.storage import Base, Listing, Observation
from sqlalchemy import select


def fixture(**changes):
    data = dict(
        id="fixture",
        retailer="test",
        retailer_name="Test retailer",
        title="TEST ONLY handset",
        url="https://fixture.example/product",
        brand="Test",
        model="T1",
        gtin="1234567890123",
        variant={"storage": "256gb", "colour": "black"},
        condition="new",
        price=1000000,
        timestamp=utcnow() - timedelta(seconds=1),
        source="TEST FIXTURE",
        availability="in_stock",
    )
    data.update(changes)
    return ListingInput(**data)


@pytest.fixture
def client(tmp_path):
    app = create_app("sqlite:///" + str(tmp_path / "test.db"))
    Base.metadata.create_all(app.state.sessions.kw["bind"])
    with TestClient(app) as c:
        c.headers["Authorization"] = "Bearer " + c.post("/sessions").json()["token"]
        yield c


@pytest.mark.parametrize(
    "url",
    [
        "http://store.example/p",
        "https://localhost/p",
        "https://127.0.0.1/p",
        "https://a.local/p",
        "https://user:password@store.example/p",
        "https://store.example:8080/p",
        "https://0x7f000001/p",
        "https://store.example/p\n",
        "file:///etc/passwd",
    ],
)
def test_invalid_urls(url):
    with pytest.raises(ValueError):
        safe_url(url)


def test_safe_tracking_parameters():
    assert (
        safe_url("https://STORE.example/p?variant=blue&utm_source=x&sku=12#details")
        == "https://store.example/p?variant=blue&sku=12"
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"price": 0},
        {"price": 100.5},
        {"price": True},
        {"currency": "USD"},
        {"timestamp": utcnow() + timedelta(days=1)},
        {"timestamp": utcnow().replace(tzinfo=None)},
    ],
)
def test_bad_observations(changes):
    with pytest.raises(ValueError):
        fixture(**changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"variant": {"storage": "128gb", "colour": "black"}},
        {"variant": {"storage": "256gb", "colour": "blue"}},
        {"condition": "refurbished"},
        {"brand": "Other"},
        {"model": "Other"},
    ],
)
def test_conflicting_variants(changes):
    a = fixture().model_dump(mode="json")
    b = fixture(**changes).model_dump(mode="json")
    assert match(a, b)["status"] == "similar"


def test_incomplete_variant_and_condition():
    a = fixture().model_dump(mode="json")
    b = fixture(variant={}).model_dump(mode="json")
    assert match(a, b)["status"] == "likely"
    assert match(a, fixture(condition="unknown").model_dump(mode="json"))["status"] == "unverified"
    assert match(a, a)["status"] == "exact"


def test_stats_and_insufficient_history():
    assert statistics([]) == dict(count=0, minimum=None, maximum=None, average=None, median=None)
    assert statistics([{"price": 100}, {"price": 200}, {"price": 300}])["median"] == 200
    data = fixture().model_dump(mode="json")
    data["match"] = match(data, data)
    assert analyze(data, [])["label"] == "Insufficient data"


def test_analysis_freshness_and_cheaper_offer():
    data = fixture(price=800000).model_dump(mode="json")
    data["match"] = match(data, data)
    points = [
        {"price": 1000000, "timestamp": (utcnow() - timedelta(days=10 - i * 2)).isoformat()}
        for i in range(6)
    ]
    assert analyze(data, points)["label"] == "Good time to buy"
    assert analyze(data, points, 700000)["label"] == "Consider waiting"
    data["timestamp"] = (utcnow() - timedelta(days=2)).isoformat()
    assert analyze(data, points)["label"] == "Insufficient data"


def test_default_is_live_only_and_empty(client):
    assert client.get("/health").json()["mode"] == "live_only"
    assert client.get("/products").json() == []
    assert all(r["status"] == "Setup required" for r in client.get("/retailers").json())
    assert LicensedFeed().observations() == []


def test_unknown_url_records_candidate_and_no_price(client):
    r = client.post("/resolve", json={"url": "https://unknown.example/p"}).json()
    assert r["status"] == "unsupported"
    assert client.get("/products").json() == []
    assert any(r["id"] == "unknown.example" for r in client.get("/retailers").json())
    assert client.post("/resolve", json={"url": "https://127.0.0.1/p"}).status_code == 422


def test_history_immutable_deduplicated_and_separate(client):
    sessions = client.app.state.sessions
    a = fixture()
    assert ingest(sessions, SingleObservation(a)) == 1
    assert ingest(sessions, SingleObservation(a)) == 0
    with pytest.raises(ValueError):
        ingest(sessions, SingleObservation(a.model_copy(update={"price": 2000000})))
    b = fixture(id="second", retailer="other", price=3000000)
    ingest(sessions, SingleObservation(b))
    h = client.get("/products/fixture/history?days=0").json()
    assert h["statistics"]["count"] == 1 and h["statistics"]["minimum"] == a.price
    assert client.get("/products/fixture/history?days=1").status_code == 422
    assert client.get("/products/no-such-id").status_code == 404
    assert client.get("/products/fixture/comparison").json()["listings"][0]["id"] == "fixture"


def test_private_watchlist_and_alerts(client):
    ingest(client.app.state.sessions, SingleObservation(fixture()))
    assert client.put("/watchlist/fixture").status_code == 204
    assert client.put("/watchlist/fixture").status_code == 204
    assert len(client.get("/watchlist").json()) == 1
    assert (
        client.put("/alerts", json={"listing_id": "fixture", "target": 1200000}).status_code == 204
    )
    assert client.get("/alerts").json()[0]["triggered"]
    first = client.headers["Authorization"]
    client.headers["Authorization"] = "Bearer " + client.post("/sessions").json()["token"]
    assert client.get("/watchlist").json() == [] and client.get("/alerts").json() == []
    client.headers["Authorization"] = first
    assert client.delete("/sessions").status_code == 204
    assert client.get("/watchlist").status_code == 401


def test_queued_collector_and_failures(client):
    response = client.post("/resolve", json={"url": "https://www.amazon.in/dp/B012345678"}).json()
    assert response["status"] == "pending"
    assert process_jobs(client.app.state.sessions, collector=lambda url: fixture()) == 1
    result = client.get("/collection/" + response["job_id"]).json()
    assert result["status"] == "complete" and result["listing"]["id"] == "fixture"
    second = client.post("/resolve", json={"url": "https://www.amazon.in/dp/B112345678"}).json()

    def fail(url):
        raise ValueError("Source access denied")

    process_jobs(client.app.state.sessions, collector=fail)
    assert client.get("/collection/" + second["job_id"]).json()["message"] == "Source access denied"


def test_affiliate_fallback_and_invalid_destination():
    class BadProvider:
        def generate(self, url):
            return "https://unrelated.example/p"

    data = fixture().model_dump(mode="json")
    assert outbound(data)["affiliate"] is False
    assert outbound(data, BadProvider(), ["approved.example"])["url"] == data["url"]


def test_old_observation_does_not_replace_current(client):
    sessions = client.app.state.sessions
    current = fixture()
    ingest(sessions, SingleObservation(current))
    older = current.model_copy(update={"price": 2000000, "timestamp": utcnow() - timedelta(days=2)})
    ingest(sessions, SingleObservation(older))
    with sessions() as s:
        assert s.get(Listing, "fixture").data["price"] == current.price
        assert len(list(s.scalars(select(Observation)))) == 2


def test_delivery_area_cannot_prove_equivalent_price():
    a = fixture().model_dump(mode="json")
    b = fixture(market="other-area").model_dump(mode="json")
    assert match(a, b)["status"] == "similar"


def test_discovery_preserves_source_failures(client, monkeypatch):
    import pulse_api.collectors as collectors
    from backend.models import CollectionError

    ingest(client.app.state.sessions, SingleObservation(fixture()))

    class Failed:
        key = "not-test"

        def search(self, query, limit):
            raise CollectionError("blocked", "TEST source blocked")

    monkeypatch.setattr(collectors, "REGISTRY", {"failed": Failed})
    response = client.post("/products/fixture/discover").json()
    assert collectors.process_jobs(client.app.state.sessions) == 1
    result = client.get("/collection/" + response["job_id"]).json()
    assert result["status"] == "complete"
    assert result["result"]["sources"][0]["status"] == "unavailable"
    assert result["result"]["sources"][0]["message"] == "TEST source blocked"


def test_quickcommerce_without_schema_returns_actionable_error(client):
    response = client.post(
        "/providers/quickcommerce/search",
        json={"q": "milk", "platform": "BlinkIt", "lat": 12.9, "lon": 77.66},
    )
    assert response.status_code == 503 and "documentation" in response.json()["detail"]
    assert (
        client.post(
            "/providers/quickcommerce/search",
            json={"q": "milk", "platform": "unknown", "lat": 120, "lon": 77.66},
        ).status_code
        == 422
    )


def test_quickcommerce_documented_request_and_explicit_mapping(monkeypatch):
    import httpx
    from pulse_api.quickcommerce import GrocerySearch, map_results, search

    monkeypatch.setenv("PULSE_QUICKCOMMERCE_KEY", "TEST ONLY, NOT A REAL KEY")

    def handle(request):
        assert request.url.host == "api.quickcommerceapi.com"
        assert request.url.path == "/v1/search"
        assert request.url.params["platform"] == "BlinkIt"
        assert request.headers["X-API-Key"] == "TEST ONLY, NOT A REAL KEY"
        return httpx.Response(
            200,
            json={
                "test_rows": [
                    {
                        "test_id": "a",
                        "test_title": "TEST ONLY milk",
                        "test_url": "https://blinkit.com/prn/test/prid/1",
                        "test_price": "25.99",
                    }
                ]
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        raw = search(GrocerySearch(q="milk", lat=12.9, lon=77.66), client)
    schema = {
        "results_path": "test_rows",
        "fields": {
            "id": "test_id",
            "title": "test_title",
            "url": "test_url",
            "price": "test_price",
        },
        "price_unit": "rupees",
        "currency": "INR",
    }
    rows = map_results(raw, schema, "test-area")
    assert rows[0].price == 2599 and rows[0].condition == "unknown"
    assert rows[0].market == "test-area"


def test_large_price_and_stale_alert(client):
    data = fixture(price=10**10, timestamp=utcnow() - timedelta(days=2))
    ingest(client.app.state.sessions, SingleObservation(data))
    client.put("/alerts", json={"listing_id": data.id, "target": 10**11})
    assert client.get("/alerts").json()[0]["triggered"] is False


def test_unknown_empty_attributes_never_make_exact():
    a = fixture(variant={"size": ""}).model_dump(mode="json")
    assert match(a, a)["status"] == "likely"
