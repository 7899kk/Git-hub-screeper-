"""Persistent collection queue with recovery leases."""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"


def upgrade():
    op.create_table(
        "collection_jobs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("listing_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.Column("lease_until", sa.Float(), nullable=False),
    )


def downgrade():
    op.drop_table("collection_jobs")
