"""No user URL is fetched. Only operator-configured licensed feeds are read."""

import json
import os
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit

import httpx
from sqlalchemy import select

from .domain import ListingInput, safe_url, utcnow
from .storage import Alert, Listing, Observation


class ProductProvider(Protocol):
    def observations(self) -> list[ListingInput]: ...


class LicensedFeed:
    def observations(self):
        license_note = os.getenv("PULSE_FEED_LICENSE", "")
        location = os.getenv("PULSE_FEED_PATH", "")
        endpoint = os.getenv("PULSE_FEED_URL", "")
        if not license_note or not (location or endpoint):
            return []
        if endpoint:
            endpoint = safe_url(endpoint)
            # Fixed operator endpoint; redirects cannot switch credential destinations.
            headers = (
                {"Authorization": "Bearer " + os.environ["PULSE_FEED_TOKEN"]}
                if os.getenv("PULSE_FEED_TOKEN")
                else {}
            )
            with httpx.Client(timeout=30, follow_redirects=False) as client:
                r = client.get(endpoint, headers=headers)
                r.raise_for_status()
                raw = r.json()
        else:
            raw = json.loads(Path(location).read_text())
        if not isinstance(raw, list) or len(raw) > 10000:
            raise ValueError("Feed must be a JSON list with at most 10,000 observations")
        # Validation is atomic: malformed data never partially enters storage.
        return [ListingInput.model_validate(row) for row in raw]


class AffiliateProvider(Protocol):
    def generate(self, destination: str) -> str: ...


def outbound(listing: dict, provider: AffiliateProvider | None = None, allowed_hosts=()):
    original = safe_url(listing["url"])
    if provider is None:
        return {
            "url": original,
            "affiliate": False,
            "message": "Affiliate tracking unavailable; opens the original product.",
        }
    try:
        result = safe_url(provider.generate(original))
        if urlsplit(result).hostname not in allowed_hosts:
            raise ValueError("Unexpected affiliate destination")
        return {
            "url": result,
            "affiliate": True,
            "message": "An eligible purchase may earn a commission.",
        }
    except Exception:
        return {
            "url": original,
            "affiliate": False,
            "message": "Affiliate link unavailable; original product preserved.",
        }


def ingest(session_factory, provider: ProductProvider):
    rows = provider.observations()
    with session_factory.begin() as session:
        inserted = 0
        for row in rows:
            data = row.model_dump(mode="json")
            old = session.get(Listing, row.id)
            if old:
                # A stable listing ID cannot silently change product or seller identity.
                for key in (
                    "retailer",
                    "url",
                    "brand",
                    "model",
                    "gtin",
                    "variant",
                    "condition",
                    "market",
                ):
                    if old.data[key] != data[key]:
                        raise ValueError(f"Listing identity changed: {row.id} / {key}")
            if not old:
                old = Listing(id=row.id, data=data)
                session.add(old)
            elif data["timestamp"] >= old.data["timestamp"]:
                old.data = data
            exists = session.scalar(
                select(Observation).where(
                    Observation.listing_id == row.id, Observation.timestamp == data["timestamp"]
                )
            )
            if exists and (exists.price != row.price or exists.source != row.source):
                raise ValueError("An immutable observation cannot change at the same timestamp")
            if not exists:
                session.add(
                    Observation(
                        listing_id=row.id,
                        timestamp=data["timestamp"],
                        price=row.price,
                        source=row.source,
                    )
                )
                inserted += 1
            for alert in session.scalars(select(Alert).where(Alert.listing_id == row.id)):
                from datetime import datetime

                fresh = (
                    utcnow() - datetime.fromisoformat(old.data["timestamp"])
                ).total_seconds() <= 86400
                alert.triggered = (
                    fresh
                    and old.data["price"] <= alert.target
                    and old.data["availability"] == "in_stock"
                )
        return inserted
