"""events table

Revision ID: 20260224_0007
Revises: 20260224_0006
Create Date: 2026-02-24 14:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260224_0007"
down_revision = "20260224_0006"
branch_labels = None
depends_on = None


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _table_names() -> set[str]:
    return set(_inspector().get_table_names())


def _index_names(table_name: str) -> set[str]:
    return {idx["name"] for idx in _inspector().get_indexes(table_name)}


def upgrade() -> None:
    if "event" not in _table_names():
        op.create_table(
            "event",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("workspace_id", sa.Integer(), nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=True),
            sa.Column("kind", sa.String(), nullable=False),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
            sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "event" in _table_names():
        index_names = _index_names("event")
        if "ix_event_workspace_id" not in index_names:
            op.create_index("ix_event_workspace_id", "event", ["workspace_id"], unique=False)
        if "ix_event_kind" not in index_names:
            op.create_index("ix_event_kind", "event", ["kind"], unique=False)


def downgrade() -> None:
    if "event" not in _table_names():
        return

    index_names = _index_names("event")
    if "ix_event_kind" in index_names:
        op.drop_index("ix_event_kind", table_name="event")
    if "ix_event_workspace_id" in index_names:
        op.drop_index("ix_event_workspace_id", table_name="event")
    op.drop_table("event")
