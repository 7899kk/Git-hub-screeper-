"""Isolated UI-test fixture server. Never run this as the release service."""

from datetime import timedelta
from tempfile import TemporaryDirectory

from pulse_api.app import create_app
from pulse_api.collectors import SingleObservation
from pulse_api.domain import utcnow
from pulse_api.providers import ingest
from pulse_api.storage import Base
from pulse_api.tests.test_service import fixture

_temporary = TemporaryDirectory(prefix="pulse-browser-qa-")
app = create_app("sqlite:///" + _temporary.name + "/test.db")
Base.metadata.create_all(app.state.sessions.kw["bind"])
for listing_id, retailer, price in [
    ("fixture", "fixture-store", 800000),
    ("second", "other-fixture-store", 700000),
]:
    for i in range(6):
        row = fixture(
            id=listing_id,
            retailer=retailer,
            retailer_name=retailer,
            title="TEST FIXTURE handset - not a real product",
            price=price if i == 5 else 1200000,
            timestamp=utcnow() - timedelta(days=10 - i * 2, seconds=5),
        )
        ingest(app.state.sessions, SingleObservation(row))
ingest(
    app.state.sessions,
    SingleObservation(fixture(id="different", variant={"storage": "128gb", "colour": "blue"})),
)
