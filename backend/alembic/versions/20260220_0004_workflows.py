"""workflows table

Revision ID: 20260220_0004
Revises: 20260220_0003
Create Date: 2026-02-20 05:10:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260220_0004"
down_revision = "20260220_0003"
branch_labels = None
depends_on = None


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _table_names() -> set[str]:
    return set(_inspector().get_table_names())


def _index_names(table_name: str) -> set[str]:
    return {idx["name"] for idx in _inspector().get_indexes(table_name)}


def upgrade() -> None:
    if "workflow" not in _table_names():
        op.create_table(
            "workflow",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("workspace_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("definition_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "workflow" in _table_names():
        index_names = _index_names("workflow")
        if "ix_workflow_workspace_id" not in index_names:
            op.create_index("ix_workflow_workspace_id", "workflow", ["workspace_id"], unique=False)


def downgrade() -> None:
    if "workflow" not in _table_names():
        return

    index_names = _index_names("workflow")
    if "ix_workflow_workspace_id" in index_names:
        op.drop_index("ix_workflow_workspace_id", table_name="workflow")
    op.drop_table("workflow")
