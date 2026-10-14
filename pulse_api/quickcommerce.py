"""Documented search request supplied by the user; response mapping is explicit."""

import os
from typing import Literal

import httpx
from pydantic import BaseModel, Field


class GrocerySearch(BaseModel):
    q: str = Field(min_length=1, max_length=100)
    platform: Literal["BlinkIt"] = "BlinkIt"
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


def search(body: GrocerySearch, client=None):
    key = os.getenv("PULSE_QUICKCOMMERCE_KEY")
    if not key:
        raise ValueError("QuickCommerce requires its backend key in secure environment settings")
    # This is the user-provided official endpoint and auth header. No arbitrary URLs or redirects.
    own_client = client is None
    client = client or httpx.Client(timeout=30, follow_redirects=False)
    try:
        response = client.get(
            "https://api.quickcommerceapi.com/v1/search",
            params=body.model_dump(),
            headers={"X-API-Key": key},
        )
        response.raise_for_status()
        return response.json()
    finally:
        if own_client:
            client.close()


def path_value(value, path):
    for part in path.split(".") if path else []:
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def map_results(raw, schema: dict, market: str):
    """No inferred field names or currency: map only a reviewed provider schema."""
    from .domain import ListingInput, utcnow
    from .logic_money import paise

    records = path_value(raw, schema["results_path"])
    if not isinstance(records, list):
        raise ValueError("Configured result path is not a list")
    result = []
    for record in records:
        data = {field: path_value(record, path) for field, path in schema["fields"].items()}
        from urllib.parse import urlsplit

        from .domain import safe_url

        if urlsplit(safe_url(data["url"])).hostname not in ("blinkit.com", "www.blinkit.com"):
            raise ValueError("QuickCommerce listing destination must belong to BlinkIt")
        if schema.get("currency") != "INR":
            raise ValueError("Reviewed schema must explicitly identify INR currency")
        data["price"] = paise(data["price"], schema["price_unit"])
        data.update(
            currency="INR",
            source="QuickCommerce API / BlinkIt",
            timestamp=utcnow(),
            retailer="blinkit",
            retailer_name="BlinkIt",
            condition=data.get("condition", "unknown"),
            variant=data.get("variant", {}),
        )
        import hashlib

        data["market"] = market
        data["id"] = (
            "blinkit_" + hashlib.sha256((str(data["id"]) + market).encode()).hexdigest()[:32]
        )
        result.append(ListingInput.model_validate(data))
    return result
