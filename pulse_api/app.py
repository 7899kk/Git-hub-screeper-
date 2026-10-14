import hashlib
import json
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select

from .domain import analyze, match, safe_url, statistics, utcnow
from .providers import ingest, outbound
from .quickcommerce import GrocerySearch
from .storage import Alert, Candidate, CollectionJob, Device, Listing, Observation, Saved, database


class ResolveInput(BaseModel):
    url: str = Field(max_length=2048)


class AlertInput(BaseModel):
    listing_id: str = Field(max_length=100)
    target: int = Field(gt=0, le=10**11, strict=True)


def create_app(database_url=None):
    engine, sessions = database(database_url)

    @asynccontextmanager
    async def lifespan(app):
        yield
        engine.dispose()

    app = FastAPI(title="PricePulse live API", version="2.0.0", lifespan=lifespan)
    app.state.sessions = sessions
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv(
            "PULSE_CORS_ORIGINS",
            "http://localhost:8081,http://127.0.0.1:8081,http://localhost:8082,http://127.0.0.1:8082",
        ).split(","),
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )
    attempts = defaultdict(deque)
    lock = threading.Lock()

    @app.middleware("http")
    async def limits(request: Request, call_next):
        from starlette.responses import JSONResponse

        if int(request.headers.get("content-length", "0")) > 16384:
            return JSONResponse({"detail": "Payload too large"}, status_code=413)
        key = request.client.host if request.client else "unknown"
        with lock:
            clock = time.monotonic()
            if len(attempts) > 10000:
                for k in list(attempts):
                    if not attempts[k] or attempts[k][-1] < clock - 60:
                        del attempts[k]
            q = attempts[key]
            while q and q[0] < clock - 60:
                q.popleft()
            if len(q) >= 180:
                return JSONResponse(
                    {"detail": "Too many requests; try again in a minute"}, status_code=429
                )
            q.append(clock)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    def owner(authorization: str = Header(default="")):
        token = authorization.removeprefix("Bearer ")
        digest = hashlib.sha256(token.encode()).hexdigest()
        with sessions() as s:
            if not authorization.startswith("Bearer ") or not s.get(Device, digest):
                raise HTTPException(401, "Device session expired. Reconnect in settings.")
        return digest

    def listing(s, listing_id):
        row = s.get(Listing, listing_id)
        if not row:
            raise HTTPException(404, "No verified listing was found")
        return dict(row.data)

    def decorate(data, base=None):
        data = dict(data)
        data["match"] = match(base or data, data)
        data["age_hours"] = max(
            0, (utcnow() - datetime.fromisoformat(data["timestamp"])).total_seconds() / 3600
        )
        data["stale"] = data["age_hours"] > 24
        data["affiliate"] = False
        data["verification"] = "provider_observation"
        return data

    def enqueue(s, url, kind="collect"):
        current = s.scalar(
            select(CollectionJob).where(
                CollectionJob.url == url,
                CollectionJob.kind == kind,
                CollectionJob.status.in_(["pending", "running"]),
            )
        )
        if current:
            return current
        latest = s.scalar(
            select(CollectionJob)
            .where(CollectionJob.url == url, CollectionJob.kind == kind)
            .order_by(CollectionJob.created_at.desc())
            .limit(1)
        )
        if latest and (utcnow() - datetime.fromisoformat(latest.created_at)).total_seconds() < 30:
            raise HTTPException(429, "Wait 30 seconds before retrying this source")
        count = s.scalar(
            select(func.count())
            .select_from(CollectionJob)
            .where(CollectionJob.status.in_(["pending", "running"]))
        )
        if count >= 50:
            raise HTTPException(429, "Collection queue is busy. Try again later.")
        row = CollectionJob(
            id=secrets.token_hex(16),
            url=url,
            kind=kind,
            status="pending",
            message="Waiting for permitted retailer collection",
            created_at=utcnow().isoformat(),
            lease_until=0,
            result={},
        )
        s.add(row)
        return row

    @app.get("/health")
    def health():
        with sessions() as s:
            s.execute(select(Device).limit(1))
        return {"status": "ok", "mode": "live_only", "version": "2.0.0"}

    @app.post("/sessions", status_code=201)
    def register():
        token = secrets.token_urlsafe(32)
        with sessions.begin() as s:
            s.add(
                Device(
                    token_hash=hashlib.sha256(token.encode()).hexdigest(),
                    created_at=utcnow().isoformat(),
                )
            )
        return {"token": token}

    @app.delete("/sessions", status_code=204)
    def erase(user=Depends(owner)):
        with sessions.begin() as s:
            s.execute(delete(Saved).where(Saved.owner == user))
            s.execute(delete(Alert).where(Alert.owner == user))
            s.execute(delete(Device).where(Device.token_hash == user))

    @app.get("/retailers")
    def retailers(user=Depends(owner)):
        catalog = json.loads((Path(__file__).parent / "retailers.json").read_text())
        custom = os.getenv("PULSE_RETAILERS_FILE")
        if custom:
            catalog.extend(json.loads(Path(custom).read_text()))
        with sessions() as s:
            rows = [decorate(x.data) for x in s.scalars(select(Listing))]
            seen = {x["id"] for x in catalog}
            for row in rows:
                if row["retailer"] not in seen:
                    catalog.append(
                        {
                            "id": row["retailer"],
                            "name": row["retailer_name"],
                            "domains": [urlsplit(row["url"]).hostname],
                        }
                    )
                    seen.add(row["retailer"])
            for entry in catalog:
                available = [x for x in rows if x["retailer"] == entry["id"]]
                fresh = any(not x["stale"] for x in available)
                entry.update(
                    status="Live data available"
                    if fresh
                    else "Temporarily unavailable"
                    if available
                    else "Setup required",
                    affiliate="Unavailable",
                    capabilities=["resolve_cached_url", "history", "comparison"]
                    if available
                    else [],
                    message="Authorized feed observations only; individual prices show timestamps."
                    if fresh
                    else "Connect an authorized retailer API or licensed feed.",
                )
            domains = {d for x in catalog for d in x["domains"]}
            for candidate in s.scalars(select(Candidate)):
                if candidate.domain not in domains:
                    catalog.append(
                        {
                            "id": candidate.domain,
                            "name": candidate.domain,
                            "domains": [candidate.domain],
                            "status": "No supported data source",
                            "affiliate": "Unavailable",
                            "capabilities": [],
                            "message": "Candidate integration recorded; no page was fetched.",
                        }
                    )
        return catalog

    @app.post("/resolve")
    def resolve(body: ResolveInput, user=Depends(owner)):
        try:
            url = safe_url(body.url)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        with sessions.begin() as s:
            rows = list(s.scalars(select(Listing)))
            found = next((x for x in rows if x.data["url"] == url), None)
            if found:
                return {
                    "status": "identified",
                    "listing": decorate(found.data),
                    "canonical_url": url,
                }
            from backend.connectors import connector_for
            from backend.models import CollectionError

            try:
                connector_for(url)
            except CollectionError:
                pass
            else:
                existing = enqueue(s, url)
                return {
                    "status": "pending",
                    "job_id": existing.id,
                    "canonical_url": url,
                    "message": "Collection queued. Retailer access restrictions and failures will be reported.",
                }
            domain = urlsplit(url).hostname
            if not s.get(Candidate, domain):
                s.add(Candidate(domain=domain))
            return {
                "status": "unsupported",
                "canonical_url": url,
                "domain": domain,
                "message": "No authorized product data is available for this link. The retailer was recorded for integration review; no price was inferred.",
            }

    @app.get("/collection/{job_id}")
    def job_status(job_id: str, user=Depends(owner)):
        with sessions() as s:
            row = s.get(CollectionJob, job_id)
            if not row:
                raise HTTPException(404, "Collection request not found")
            return {
                "status": row.status,
                "message": row.message,
                "result": row.result,
                "listing": decorate(listing(s, row.listing_id)) if row.listing_id else None,
            }

    @app.post("/providers/quickcommerce/search")
    def grocery_search(body: GrocerySearch, user=Depends(owner)):
        import httpx

        from .quickcommerce import map_results, search

        schema_path = os.getenv("PULSE_QUICKCOMMERCE_SCHEMA_FILE")
        if not schema_path:
            raise HTTPException(
                503,
                "QuickCommerce response mapping needs official provider documentation. No unverified prices are displayed.",
            )
        try:
            schema = json.loads(Path(schema_path).read_text())
            market = (
                "local_"
                + hashlib.sha256(f"{body.lat:.5f},{body.lon:.5f}".encode()).hexdigest()[:24]
            )
            rows = map_results(search(body), schema, market)

            class Results:
                def observations(self):
                    return rows

            ingest(sessions, Results())
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                502,
                f"QuickCommerce returned HTTP {exc.response.status_code}. Check backend credentials and service access.",
            ) from exc
        except (ValueError, OSError, KeyError, TypeError, httpx.RequestError) as exc:
            raise HTTPException(
                503,
                "QuickCommerce is unavailable or its documented data mapping is not configured correctly.",
            ) from exc
        return {"listings": [decorate(row.model_dump(mode="json")) for row in rows]}

    @app.get("/products")
    def products(q: str = "", user=Depends(owner)):
        if len(q) > 200:
            raise HTTPException(422, "Search is too long")
        with sessions() as s:
            return [
                decorate(x.data)
                for x in s.scalars(select(Listing))
                if q.lower() in x.data["title"].lower()
            ][:100]

    @app.get("/products/{listing_id}")
    def product(listing_id: str, user=Depends(owner)):
        with sessions() as s:
            return decorate(listing(s, listing_id))

    @app.post("/products/{listing_id}/discover")
    def find_equivalents(listing_id: str, user=Depends(owner)):
        with sessions.begin() as s:
            data = listing(s, listing_id)
            row = enqueue(s, data["url"], "discover")
            return {"job_id": row.id, "status": "pending"}

    @app.post("/products/{listing_id}/refresh")
    def refresh_listing(listing_id: str, user=Depends(owner)):
        from backend.connectors import connector_for
        from backend.models import CollectionError

        with sessions.begin() as s:
            data = listing(s, listing_id)
            try:
                connector_for(data["url"])
            except CollectionError as exc:
                raise HTTPException(
                    503,
                    "This listing refreshes through its configured provider feed, not a page collector.",
                ) from exc
            row = enqueue(s, data["url"])
            return {"job_id": row.id, "status": "pending"}

    @app.get("/products/{listing_id}/comparison")
    def comparison(listing_id: str, user=Depends(owner)):
        with sessions() as s:
            base = listing(s, listing_id)
            rows = [
                decorate(x.data, base)
                for x in s.scalars(select(Listing))
                if x.data["brand"].lower() == base["brand"].lower()
            ]
        rows.sort(
            key=lambda x: (
                x["match"]["status"] != "exact" or x["stale"] or x["availability"] != "in_stock",
                x["price"],
            )
        )
        return {
            "product": decorate(base),
            "listings": rows,
            "message": "Lowest listed prices exclude shipping and conditional offers. Similar and unverified products are separated.",
        }

    def history_data(s, listing_id, days):
        query = (
            select(Observation)
            .where(Observation.listing_id == listing_id)
            .order_by(Observation.timestamp)
        )
        if days:
            query = query.where(
                Observation.timestamp >= (utcnow() - timedelta(days=days)).isoformat()
            )
        return [
            {
                "price": x.price,
                "timestamp": x.timestamp,
                "source": x.source,
                "currency": "INR",
                "price_type": "listed",
            }
            for x in s.scalars(query)
        ]

    @app.get("/products/{listing_id}/history")
    def history(listing_id: str, days: int = 30, user=Depends(owner)):
        if days not in (0, 7, 30, 90, 180):
            raise HTTPException(422, "Choose 7, 30, 90, 180 or 0 for all available history")
        with sessions() as s:
            data = decorate(listing(s, listing_id))
            points = history_data(s, listing_id, days)
        return {
            "listing": data,
            "points": points,
            "statistics": statistics(points),
            "message": "Only actual authorized provider observations. Tracking cannot reconstruct earlier prices.",
        }

    @app.get("/products/{listing_id}/analysis")
    def analysis(listing_id: str, days: int = 30, user=Depends(owner)):
        if days not in (0, 7, 30, 90, 180):
            raise HTTPException(422, "Unsupported history range")
        with sessions() as s:
            data = decorate(listing(s, listing_id))
            points = history_data(s, listing_id, days)
            comparable = [decorate(x.data, data) for x in s.scalars(select(Listing))]
        exact = [
            x["price"]
            for x in comparable
            if x["match"]["status"] == "exact"
            and not x["stale"]
            and x["availability"] == "in_stock"
        ]
        return analyze(data, points, min(exact) if exact else None)

    @app.get("/watchlist")
    def watchlist(user=Depends(owner)):
        with sessions() as s:
            return [
                decorate(listing(s, x.listing_id))
                for x in s.scalars(select(Saved).where(Saved.owner == user))
            ]

    @app.put("/watchlist/{listing_id}", status_code=204)
    def save(listing_id: str, user=Depends(owner)):
        with sessions.begin() as s:
            listing(s, listing_id)
            if not s.scalar(
                select(Saved).where(Saved.owner == user, Saved.listing_id == listing_id)
            ):
                s.add(Saved(owner=user, listing_id=listing_id))

    @app.delete("/watchlist/{listing_id}", status_code=204)
    def unsave(listing_id: str, user=Depends(owner)):
        with sessions.begin() as s:
            s.execute(delete(Saved).where(Saved.owner == user, Saved.listing_id == listing_id))

    @app.get("/alerts")
    def alerts(user=Depends(owner)):
        with sessions() as s:
            return [
                {
                    "id": x.id,
                    "listing": decorate(listing(s, x.listing_id)),
                    "target": x.target,
                    "triggered": x.triggered,
                }
                for x in s.scalars(select(Alert).where(Alert.owner == user))
            ]

    @app.put("/alerts", status_code=204)
    def alert(body: AlertInput, user=Depends(owner)):
        with sessions.begin() as s:
            data = listing(s, body.listing_id)
            row = s.scalar(
                select(Alert).where(Alert.owner == user, Alert.listing_id == body.listing_id)
            )
            triggered = (
                not decorate(data)["stale"]
                and data["availability"] == "in_stock"
                and data["price"] <= body.target
            )
            if row:
                row.target, row.triggered = body.target, triggered
            else:
                s.add(
                    Alert(
                        owner=user,
                        listing_id=body.listing_id,
                        target=body.target,
                        triggered=triggered,
                    )
                )

    @app.delete("/alerts/{alert_id}", status_code=204)
    def delete_alert(alert_id: int, user=Depends(owner)):
        with sessions.begin() as s:
            s.execute(delete(Alert).where(Alert.owner == user, Alert.id == alert_id))

    @app.post("/products/{listing_id}/outbound")
    def deal(listing_id: str, user=Depends(owner)):
        with sessions() as s:
            return outbound(listing(s, listing_id))

    return app


app = create_app()
