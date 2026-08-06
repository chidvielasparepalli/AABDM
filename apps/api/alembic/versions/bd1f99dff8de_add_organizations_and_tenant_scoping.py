"""add organizations and tenant scoping

Revision ID: bd1f99dff8de
Revises: c86bc7eb7338
Create Date: 2026-08-06 14:37:36.766834

Adds multi-tenancy:

- organizations + organization_members tables
- organization_id (FK organizations.id) on every business table,
  backfilled to the default organization (id 1), then NOT NULL.

Backfill targets organization id 1 — the legacy default org. Any
pre-existing single-tenant data lands there, preserving backward
compatibility.

Note: SQLite has no `ALTER COLUMN ... SET NOT NULL`, so each business table
is rebuilt via the batch_alter_table dance (create new → copy → drop →
rename). Postgres takes the same path via batch ops (no-op where the
dialect supports inline alter).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd1f99dff8de'
down_revision: Union[str, Sequence[str], None] = 'c86bc7eb7338'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Every business table gets an organization_id column.
TENANT_TABLES = [
    "clients",
    "calls",
    "transcript_lines",
    "timeline",
    "documents",
    "learning_entries",
    "memories",
    "follow_ups",
    "meetings",
    "negotiation_configs",
    "research_reports",
    "emails",
]


def upgrade() -> None:
    """Add organizations and scope all business rows to a tenant."""
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "organization_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
    )
    op.create_index(
        "ix_organization_members_organization_id",
        "organization_members",
        ["organization_id"],
    )

    # Legacy default organization — all pre-existing data lands here.
    op.execute(
        sa.text(
            "INSERT INTO organizations (id, name, created_at) "
            "VALUES (1, 'Default Organization', CURRENT_TIMESTAMP)"
        )
    )

    for table in TENANT_TABLES:
        with op.batch_alter_table(table) as batch:
            batch.add_column(
                sa.Column("organization_id", sa.Integer(), nullable=True),
            )
            batch.create_index(f"ix_{table}_organization_id", ["organization_id"])
        op.execute(sa.text(f"UPDATE {table} SET organization_id = 1 WHERE organization_id IS NULL"))
        with op.batch_alter_table(table) as batch:
            batch.alter_column("organization_id", nullable=False)
            batch.create_foreign_key(
                f"fk_{table}_organization_id",
                "organizations",
                ["organization_id"],
                ["id"],
            )


def downgrade() -> None:
    """Drop tenant scoping. Business rows lose their organization_id."""
    for table in TENANT_TABLES:
        with op.batch_alter_table(table) as batch:
            batch.drop_constraint(f"fk_{table}_organization_id", type_="foreignkey")
            batch.drop_index(f"ix_{table}_organization_id")
            batch.drop_column("organization_id")
    op.drop_index("ix_organization_members_organization_id", table_name="organization_members")
    op.drop_table("organization_members")
    op.drop_table("organizations")
