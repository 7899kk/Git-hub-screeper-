"""Create live-only listings, observations and private device data."""

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None


def upgrade():
    op.create_table(
        "listings",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("data", sa.JSON(), nullable=False),
    )
    op.create_table(
        "observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.String(100), nullable=False),
        sa.Column("timestamp", sa.String(40), nullable=False),
        sa.Column("price", sa.BigInteger(), nullable=False),
        sa.Column("source", sa.String(200), nullable=False),
        sa.UniqueConstraint("listing_id", "timestamp"),
    )
    op.create_index("ix_observations_listing_id", "observations", ["listing_id"])
    op.create_table(
        "devices",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("created_at", sa.String(40), nullable=False),
    )
    op.create_table(
        "saved",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner", sa.String(64), nullable=False),
        sa.Column("listing_id", sa.String(100), nullable=False),
        sa.UniqueConstraint("owner", "listing_id"),
    )
    op.create_index("ix_saved_owner", "saved", ["owner"])
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner", sa.String(64), nullable=False),
        sa.Column("listing_id", sa.String(100), nullable=False),
        sa.Column("target", sa.BigInteger(), nullable=False),
        sa.Column("triggered", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("owner", "listing_id"),
    )
    op.create_index("ix_alerts_owner", "alerts", ["owner"])
    op.create_table("candidates", sa.Column("domain", sa.String(253), primary_key=True))


def downgrade():
    for name in ("candidates", "alerts", "saved", "devices", "observations", "listings"):
        op.drop_table(name)
