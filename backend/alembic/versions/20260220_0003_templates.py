"""templates table

Revision ID: 20260220_0003
Revises: 20260220_0002
Create Date: 2026-02-20 04:20:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260220_0003"
down_revision = "20260220_0002"
branch_labels = None
depends_on = None


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _table_names() -> set[str]:
    return set(_inspector().get_table_names())


def _index_names(table_name: str) -> set[str]:
    return {idx["name"] for idx in _inspector().get_indexes(table_name)}


def upgrade() -> None:
    if "template" not in _table_names():
        op.create_table(
            "template",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("workspace_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("kind", sa.String(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("meta", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "workspace_id",
                "name",
                "kind",
                "version",
                name="uq_template_workspace_name_kind_version",
            ),
        )

    if "template" in _table_names():
        index_names = _index_names("template")
        if "ix_template_workspace_id" not in index_names:
            op.create_index("ix_template_workspace_id", "template", ["workspace_id"], unique=False)
        if "ix_template_kind" not in index_names:
            op.create_index("ix_template_kind", "template", ["kind"], unique=False)


def downgrade() -> None:
    if "template" not in _table_names():
        return

    index_names = _index_names("template")
    if "ix_template_kind" in index_names:
        op.drop_index("ix_template_kind", table_name="template")
    if "ix_template_workspace_id" in index_names:
        op.drop_index("ix_template_workspace_id", table_name="template")
    op.drop_table("template")
