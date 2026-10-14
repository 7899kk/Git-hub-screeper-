"""Record cross-retailer discovery and independent source failures."""

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"


def upgrade():
    op.add_column(
        "collection_jobs",
        sa.Column("kind", sa.String(20), nullable=False, server_default="collect"),
    )
    op.add_column(
        "collection_jobs", sa.Column("result", sa.JSON(), nullable=False, server_default="{}")
    )


def downgrade():
    op.drop_column("collection_jobs", "result")
    op.drop_column("collection_jobs", "kind")
