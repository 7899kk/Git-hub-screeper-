"""Prices are integer paise. Unknown attributes cannot prove an exact variant."""

import ipaddress
import re
from datetime import datetime, timezone
from statistics import mean, median
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel, Field, field_validator


def utcnow():
    return datetime.now(timezone.utc)


def safe_url(value: str) -> str:
    if any(ord(c) < 32 for c in value):
        raise ValueError("Control characters are not accepted in URLs")
    value = value.strip()
    if len(value) > 2048 or any(ord(c) < 33 for c in value):
        raise ValueError("Enter a valid HTTPS product URL")
    p = urlsplit(value)
    if (
        p.scheme != "https"
        or not p.hostname
        or p.username
        or p.password
        or p.port not in (None, 443)
    ):
        raise ValueError("Only public HTTPS URLs without credentials are accepted")
    host = p.hostname.encode("idna").decode("ascii").lower()
    if "." not in host or host.endswith((".local", ".localhost", ".internal")):
        raise ValueError("Private addresses are not supported")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host):
            raise ValueError("Invalid hostname")
    else:
        raise ValueError("IP-address product links are not supported")
    # Do not remove unknown parameters: they may identify the selected variant.
    query = [
        (k, v)
        for k, v in parse_qsl(p.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid")
    ]
    return urlunsplit(("https", host, p.path or "/", urlencode(query), ""))


class ListingInput(BaseModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,100}$")
    retailer: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,100}$")
    retailer_name: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=500)
    url: str
    brand: str = Field(default="", max_length=100)
    model: str = Field(default="", max_length=100)
    gtin: str = Field(default="", max_length=30)
    variant: dict[str, str]
    condition: str = Field(pattern=r"^(new|refurbished|used|unknown)$")
    price: int = Field(gt=0, le=10**11, strict=True)
    currency: str = Field(default="INR", pattern="^INR$")
    shipping: int | None = Field(default=None, ge=0, strict=True)
    seller: str | None = Field(default=None, max_length=200)
    availability: str = Field(default="unknown", pattern=r"^(in_stock|out_of_stock|unknown)$")
    timestamp: datetime
    source: str = Field(min_length=1, max_length=200)
    image: str | None = None
    offers: list[str] = Field(default_factory=list, max_length=20)
    market: str = Field(default="IN", max_length=100)

    @field_validator("url", "image")
    @classmethod
    def validate_url(cls, v):
        return safe_url(v) if v else v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        if v.tzinfo is None or v > utcnow():
            raise ValueError("Observation needs an actual timezone-aware past timestamp")
        return v.astimezone(timezone.utc)


def normalized(value):
    return re.sub(r"\s+", " ", str(value).strip().lower())


def match(a: dict, b: dict) -> dict:
    if a.get("market", "IN") != b.get("market", "IN"):
        return {
            "status": "similar",
            "reason": "Delivery areas differ; local prices are not interchangeable",
        }
    if (
        not a.get("brand")
        or not b.get("brand")
        or a.get("condition") == "unknown"
        or b.get("condition") == "unknown"
    ):
        return {"status": "unverified", "reason": "Brand or product condition is not verified"}
    for key in ("brand", "condition"):
        if normalized(a.get(key, "")) != normalized(b.get(key, "")):
            return {"status": "similar", "reason": f"{key} differs"}
    av, bv = a.get("variant", {}), b.get("variant", {})
    for key in av.keys() | bv.keys():
        if key in av and key in bv and normalized(av[key]) != normalized(bv[key]):
            return {"status": "similar", "reason": f"{key} differs"}
    # Check all supplied identifiers before accepting any matching identifier.
    for key in ("gtin", "model"):
        if a.get(key) and b.get(key) and normalized(a[key]) != normalized(b[key]):
            return {"status": "similar", "reason": f"{key} differs"}
    identity = any(
        a.get(k) and b.get(k) and normalized(a[k]) == normalized(b[k]) for k in ("gtin", "model")
    )
    if identity and av and av.keys() == bv.keys() and all(av.values()) and all(bv.values()):
        return {
            "status": "exact",
            "reason": "Identifier, condition and every supplied variant attribute agree",
        }
    if identity:
        return {
            "status": "likely",
            "reason": "Identifier agrees; variant information is incomplete",
        }
    return {"status": "unverified", "reason": "No shared exact product identifier"}


def statistics(points: list[dict]):
    values = [p["price"] for p in points]
    return {
        "count": len(values),
        "minimum": min(values) if values else None,
        "maximum": max(values) if values else None,
        "average": round(mean(values)) if values else None,
        "median": round(median(values)) if values else None,
    }


def analyze(
    listing: dict,
    points: list[dict],
    cheaper: int | None = None,
    minimum_observations=5,
    minimum_days=7,
    freshness_hours=24,
    discount_ratio=0.9,
):
    stats = statistics(points)
    age = (utcnow() - datetime.fromisoformat(listing["timestamp"])).total_seconds()
    span = (
        (
            (
                datetime.fromisoformat(points[-1]["timestamp"])
                - datetime.fromisoformat(points[0]["timestamp"])
            ).total_seconds()
            / 86400
        )
        if len(points) > 1
        else 0
    )
    if (
        listing.get("match", {}).get("status") != "exact"
        or age > freshness_hours * 3600
        or stats["count"] < minimum_observations
        or span < minimum_days
        or listing["availability"] != "in_stock"
    ):
        return {
            "label": "Insufficient data",
            "reason": "Needs a fresh in-stock exact match and at least 5 observations spanning 7 days. No future price is predicted.",
        }
    if cheaper is not None and cheaper < listing["price"]:
        return {
            "label": "Consider waiting",
            "reason": "A fresh exact listing has a lower listed price elsewhere. Compare shipping before buying.",
        }
    if listing["price"] <= stats["average"] * discount_ratio:
        return {
            "label": "Good time to buy",
            "reason": "Current listed price is at least 10% below this retailer's observed average. Future discounts are unknown.",
        }
    if listing["price"] > stats["average"] * 1.1:
        return {
            "label": "Consider waiting",
            "reason": "Current listed price is over 10% above this retailer's observed average. No future reduction is guaranteed.",
        }
    return {
        "label": "Fair price",
        "reason": "Current listed price is within 10% of this retailer's observed average.",
    }
