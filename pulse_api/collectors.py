"""Adapter for original collectors. Bounded requests, no access-control bypass."""

import hashlib
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from backend.connectors import REGISTRY, connector_for
from backend.models import CollectionError
from sqlalchemy import or_, select, update

from .domain import ListingInput, safe_url, utcnow
from .providers import ingest
from .storage import CollectionJob, Listing


class SingleObservation:
    def __init__(self, row):
        self.row = row

    def observations(self):
        return [self.row]


def convert(connector, row):
    if isinstance(row, ListingInput):
        return row
    return ListingInput(
        id=hashlib.sha256(f"{row.platform}:{row.url}".encode()).hexdigest()[:40],
        retailer=row.platform,
        retailer_name=connector.name,
        title=row.title,
        url=row.url,
        brand=row.brand,
        model=row.model,
        gtin=row.gtin,
        variant=row.variant,
        condition="unknown",
        price=row.price,
        mrp=row.mrp,
        shipping=row.shipping,
        seller=row.seller or None,
        availability=row.availability
        if row.availability in ("in_stock", "out_of_stock")
        else "unknown",
        timestamp=row.timestamp,
        source=f"Permitted retailer structured data ({row.evidence})",
    )


def with_groq(connector):
    from .groq import extract, key

    if not key():
        return connector
    original = connector.parse

    def parse(html, url):
        try:
            return original(html, url)
        except CollectionError as exc:
            # Do not reinterpret ambiguous offers, currencies or access challenges.
            if exc.code != "missing_price" or not key():
                raise
            return extract(connector, html, url)

    connector.parse = parse
    return connector


def collect(url):
    connector = with_groq(connector_for(safe_url(url)))
    return convert(connector, connector.collect(url))


def discover(sessions, url):
    with sessions() as s:
        base = next((x.data for x in s.scalars(select(Listing)) if x.data["url"] == url), None)
    if not base:
        raise ValueError("Identify the primary product before discovery")
    query = " ".join([base.get("brand", ""), base["model"]]) if base.get("model") else base["title"]

    def source(cls):
        connector = with_groq(cls())
        try:
            rows, failures = connector.search(query[:200], limit=1)
            ids = []
            for row in rows:
                typed = convert(connector, row)
                ingest(sessions, SingleObservation(typed))
                ids.append(typed.id)
            return {
                "retailer": connector.key,
                "status": "observed" if ids else "unavailable",
                "listing_ids": ids,
                "failures": failures,
            }
        except Exception as exc:
            return {"retailer": connector.key, "status": "unavailable", "message": str(exc)[:300]}

    with ThreadPoolExecutor(max_workers=4) as pool:
        return {
            "sources": list(
                pool.map(source, [cls for cls in REGISTRY.values() if cls.key != base["retailer"]])
            )
        }


def enqueue_due(sessions, interval=21600):
    with sessions.begin() as s:
        for row in s.scalars(select(Listing)):
            try:
                connector_for(row.data["url"])
            except Exception:
                continue
            if (
                utcnow() - datetime.fromisoformat(row.data["timestamp"])
            ).total_seconds() < interval:
                continue
            latest = s.scalar(
                select(CollectionJob)
                .where(CollectionJob.url == row.data["url"], CollectionJob.kind == "collect")
                .order_by(CollectionJob.created_at.desc())
                .limit(1)
            )
            if latest and (
                latest.status in ("pending", "running")
                or (utcnow() - datetime.fromisoformat(latest.created_at)).total_seconds() < interval
            ):
                continue
            s.add(
                CollectionJob(
                    id=secrets.token_hex(16),
                    url=row.data["url"],
                    status="pending",
                    kind="collect",
                    message="Scheduled refresh",
                    created_at=utcnow().isoformat(),
                    lease_until=0,
                    result={},
                )
            )


def process_jobs(sessions, collector=collect):
    with sessions.begin() as s:
        job = s.scalar(
            select(CollectionJob)
            .where(
                or_(
                    CollectionJob.status == "pending",
                    (CollectionJob.status == "running") & (CollectionJob.lease_until < time.time()),
                )
            )
            .order_by(CollectionJob.created_at)
            .limit(1)
        )
        if not job:
            return 0
        job_id, url, kind = job.id, job.url, job.kind
        claim = s.execute(
            update(CollectionJob)
            .where(CollectionJob.id == job_id, CollectionJob.lease_until == job.lease_until)
            .values(status="running", lease_until=time.time() + 600)
        )
        if claim.rowcount != 1:
            return 0
    try:
        if kind == "discover":
            result = discover(sessions, url)
            count = sum(source["status"] == "observed" for source in result["sources"])
            status, listing_id, message = (
                "complete",
                None,
                f"Discovery completed: {count} sources returned observations. Other sources were unavailable.",
            )
        else:
            row = collector(url)
            ingest(sessions, SingleObservation(row))
            result = {}
            status, listing_id, message = (
                "complete",
                row.id,
                "Actual retailer observation recorded. Missing attributes remain unknown.",
            )
    except Exception as exc:
        status, listing_id, message, result = "failed", None, str(exc)[:500], {}
    with sessions.begin() as s:
        s.execute(
            update(CollectionJob)
            .where(CollectionJob.id == job_id)
            .values(
                status=status, listing_id=listing_id, message=message, lease_until=0, result=result
            )
        )
    return 1
