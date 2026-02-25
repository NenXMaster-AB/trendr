"""scheduled posts table

Revision ID: 20260224_0006
Revises: 20260221_0005
Create Date: 2026-02-24 12:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260224_0006"
down_revision = "20260221_0005"
branch_labels = None
depends_on = None


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _table_names() -> set[str]:
    return set(_inspector().get_table_names())


def _index_names(table_name: str) -> set[str]:
    return {idx["name"] for idx in _inspector().get_indexes(table_name)}


def upgrade() -> None:
    if "scheduled_post" not in _table_names():
        op.create_table(
            "scheduled_post",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("workspace_id", sa.Integer(), nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=True),
            sa.Column("artifact_id", sa.Integer(), nullable=True),
            sa.Column("platform", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("content", sa.String(), nullable=False),
            sa.Column("scheduled_at", sa.DateTime(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
            sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
            sa.ForeignKeyConstraint(["artifact_id"], ["artifact.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "scheduled_post" in _table_names():
        index_names = _index_names("scheduled_post")
        if "ix_scheduled_post_workspace_id" not in index_names:
            op.create_index(
                "ix_scheduled_post_workspace_id",
                "scheduled_post",
                ["workspace_id"],
                unique=False,
            )


def downgrade() -> None:
    if "scheduled_post" not in _table_names():
        return

    index_names = _index_names("scheduled_post")
    if "ix_scheduled_post_workspace_id" in index_names:
        op.drop_index("ix_scheduled_post_workspace_id", table_name="scheduled_post")
    op.drop_table("scheduled_post")
