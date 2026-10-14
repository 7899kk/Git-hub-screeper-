import os

from sqlalchemy import JSON, BigInteger, Boolean, String, UniqueConstraint, create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Listing(Base):
    __tablename__ = "listings"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    data: Mapped[dict] = mapped_column(JSON)


class Observation(Base):
    __tablename__ = "observations"
    __table_args__ = (UniqueConstraint("listing_id", "timestamp"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[str] = mapped_column(String(100), index=True)
    timestamp: Mapped[str] = mapped_column(String(40))
    price: Mapped[int] = mapped_column(BigInteger)
    source: Mapped[str] = mapped_column(String(200))


class Device(Base):
    __tablename__ = "devices"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[str] = mapped_column(String(40))


class Saved(Base):
    __tablename__ = "saved"
    __table_args__ = (UniqueConstraint("owner", "listing_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(64), index=True)
    listing_id: Mapped[str] = mapped_column(String(100))


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (UniqueConstraint("owner", "listing_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(64), index=True)
    listing_id: Mapped[str] = mapped_column(String(100))
    target: Mapped[int] = mapped_column(BigInteger)
    triggered: Mapped[bool] = mapped_column(Boolean, default=False)


class Candidate(Base):
    __tablename__ = "candidates"
    domain: Mapped[str] = mapped_column(String(253), primary_key=True)


class CollectionJob(Base):
    __tablename__ = "collection_jobs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    url: Mapped[str] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    message: Mapped[str] = mapped_column(String(500), default="")
    listing_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[str] = mapped_column(String(40))
    lease_until: Mapped[float] = mapped_column(default=0.0)
    kind: Mapped[str] = mapped_column(String(20), default="collect")
    result: Mapped[dict] = mapped_column(JSON, default=dict)


def database(url=None):
    url = url or os.getenv("DATABASE_URL")
    if not url and os.getenv("PULSE_DB_HOST"):
        url = URL.create(
            "postgresql+psycopg",
            username=os.getenv("PULSE_DB_USER", "pulse"),
            password=os.environ["PULSE_DB_PASSWORD"],
            host=os.environ["PULSE_DB_HOST"],
            database=os.getenv("PULSE_DB_NAME", "pulse"),
        )
    url = url or "sqlite:///data/pulse-api.db"
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False}
        if make_url(url).drivername.startswith("sqlite")
        else {},
        pool_pre_ping=True,
    )
    return engine, sessionmaker(engine, expire_on_commit=False)
