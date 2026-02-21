"""provider credentials table

Revision ID: 20260221_0005
Revises: 20260220_0004
Create Date: 2026-02-21 15:30:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260221_0005"
down_revision = "20260220_0004"
branch_labels = None
depends_on = None


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _table_names() -> set[str]:
    return set(_inspector().get_table_names())


def _index_names(table_name: str) -> set[str]:
    return {idx["name"] for idx in _inspector().get_indexes(table_name)}


def upgrade() -> None:
    if "providercredential" not in _table_names():
        op.create_table(
            "providercredential",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("workspace_id", sa.Integer(), nullable=False),
            sa.Column("provider", sa.String(), nullable=False),
            sa.Column("encrypted_api_key", sa.String(), nullable=False),
            sa.Column("key_hint", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "workspace_id",
                "provider",
                name="uq_provider_credential_workspace_provider",
            ),
        )

    if "providercredential" in _table_names():
        index_names = _index_names("providercredential")
        if "ix_providercredential_workspace_id" not in index_names:
            op.create_index(
                "ix_providercredential_workspace_id",
                "providercredential",
                ["workspace_id"],
                unique=False,
            )
        if "ix_providercredential_provider" not in index_names:
            op.create_index(
                "ix_providercredential_provider",
                "providercredential",
                ["provider"],
                unique=False,
            )


def downgrade() -> None:
    if "providercredential" not in _table_names():
        return

    index_names = _index_names("providercredential")
    if "ix_providercredential_provider" in index_names:
        op.drop_index("ix_providercredential_provider", table_name="providercredential")
    if "ix_providercredential_workspace_id" in index_names:
        op.drop_index("ix_providercredential_workspace_id", table_name="providercredential")
    op.drop_table("providercredential")
