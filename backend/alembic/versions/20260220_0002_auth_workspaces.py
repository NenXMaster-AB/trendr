"""auth and workspaces

Revision ID: 20260220_0002
Revises: 20260220_0001
Create Date: 2026-02-20 00:30:00.000000

"""
from __future__ import annotations

from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260220_0002"
down_revision = "20260220_0001"
branch_labels = None
depends_on = None


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _table_names() -> set[str]:
    return set(_inspector().get_table_names())


def _column_names(table_name: str) -> set[str]:
    inspector = _inspector()
    return {col["name"] for col in inspector.get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    inspector = _inspector()
    return {idx["name"] for idx in inspector.get_indexes(table_name)}


def _has_workspace_fk(table_name: str) -> bool:
    inspector = _inspector()
    for fk in inspector.get_foreign_keys(table_name):
        if fk.get("referred_table") != "workspace":
            continue
        if fk.get("constrained_columns") == ["workspace_id"]:
            return True
    return False


def _default_workspace_id() -> int:
    bind = op.get_bind()
    workspace_slug = "default"
    row = bind.execute(
        sa.text("SELECT id FROM workspace WHERE slug = :slug"),
        {"slug": workspace_slug},
    ).first()
    if row:
        return int(row[0])

    bind.execute(
        sa.text(
            "INSERT INTO workspace (name, slug, created_at) "
            "VALUES (:name, :slug, :created_at)"
        ),
        {
            "name": "Default Workspace",
            "slug": workspace_slug,
            "created_at": datetime.utcnow(),
        },
    )
    row = bind.execute(
        sa.text("SELECT id FROM workspace WHERE slug = :slug"),
        {"slug": workspace_slug},
    ).first()
    if not row:
        raise RuntimeError("Failed to create default workspace")
    return int(row[0])


def _ensure_legacy_user_and_membership(workspace_id: int) -> None:
    bind = op.get_bind()
    external_id = "legacy-system"
    row = bind.execute(
        sa.text("SELECT id FROM user_account WHERE external_id = :external_id"),
        {"external_id": external_id},
    ).first()
    if row:
        user_id = int(row[0])
    else:
        bind.execute(
            sa.text(
                "INSERT INTO user_account (external_id, created_at) "
                "VALUES (:external_id, :created_at)"
            ),
            {"external_id": external_id, "created_at": datetime.utcnow()},
        )
        row = bind.execute(
            sa.text("SELECT id FROM user_account WHERE external_id = :external_id"),
            {"external_id": external_id},
        ).first()
        if not row:
            raise RuntimeError("Failed to create legacy user")
        user_id = int(row[0])

    membership_row = bind.execute(
        sa.text(
            "SELECT id FROM workspace_member "
            "WHERE workspace_id = :workspace_id AND user_id = :user_id"
        ),
        {"workspace_id": workspace_id, "user_id": user_id},
    ).first()
    if not membership_row:
        bind.execute(
            sa.text(
                "INSERT INTO workspace_member (workspace_id, user_id, role, created_at) "
                "VALUES (:workspace_id, :user_id, :role, :created_at)"
            ),
            {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "role": "owner",
                "created_at": datetime.utcnow(),
            },
        )


def upgrade() -> None:
    tables = _table_names()

    if "workspace" not in tables:
        op.create_table(
            "workspace",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("slug", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("slug", name="uq_workspace_slug"),
        )
        op.create_index("ix_workspace_slug", "workspace", ["slug"], unique=True)

    if "user_account" not in tables:
        op.create_table(
            "user_account",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("external_id", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("external_id", name="uq_user_account_external_id"),
        )
        op.create_index(
            "ix_user_account_external_id",
            "user_account",
            ["external_id"],
            unique=True,
        )

    if "workspace_member" not in tables:
        op.create_table(
            "workspace_member",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("workspace_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["user_account.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "workspace_id",
                "user_id",
                name="uq_workspace_member_workspace_user",
            ),
        )
        op.create_index(
            "ix_workspace_member_workspace_id",
            "workspace_member",
            ["workspace_id"],
        )
        op.create_index("ix_workspace_member_user_id", "workspace_member", ["user_id"])

    for table_name in ("project", "artifact", "job"):
        if "workspace_id" not in _column_names(table_name):
            with op.batch_alter_table(table_name) as batch_op:
                batch_op.add_column(sa.Column("workspace_id", sa.Integer(), nullable=True))

    workspace_id = _default_workspace_id()
    _ensure_legacy_user_and_membership(workspace_id)

    bind = op.get_bind()
    for table_name in ("project", "artifact", "job"):
        bind.execute(
            sa.text(
                f"UPDATE {table_name} "
                "SET workspace_id = :workspace_id "
                "WHERE workspace_id IS NULL"
            ),
            {"workspace_id": workspace_id},
        )

    for table_name in ("project", "artifact", "job"):
        with op.batch_alter_table(table_name) as batch_op:
            if not _has_workspace_fk(table_name):
                batch_op.create_foreign_key(
                    f"fk_{table_name}_workspace_id_workspace",
                    "workspace",
                    ["workspace_id"],
                    ["id"],
                )
            index_name = f"ix_{table_name}_workspace_id"
            if index_name not in _index_names(table_name):
                batch_op.create_index(index_name, ["workspace_id"], unique=False)
            batch_op.alter_column(
                "workspace_id",
                existing_type=sa.Integer(),
                nullable=False,
            )


def downgrade() -> None:
    for table_name in ("job", "artifact", "project"):
        if table_name not in _table_names():
            continue
        if "workspace_id" not in _column_names(table_name):
            continue
        with op.batch_alter_table(table_name) as batch_op:
            index_name = f"ix_{table_name}_workspace_id"
            if index_name in _index_names(table_name):
                batch_op.drop_index(index_name)
            fk_name = f"fk_{table_name}_workspace_id_workspace"
            if _has_workspace_fk(table_name):
                batch_op.drop_constraint(fk_name, type_="foreignkey")
            batch_op.drop_column("workspace_id")

    if "workspace_member" in _table_names():
        index_names = _index_names("workspace_member")
        if "ix_workspace_member_user_id" in index_names:
            op.drop_index("ix_workspace_member_user_id", table_name="workspace_member")
        if "ix_workspace_member_workspace_id" in index_names:
            op.drop_index("ix_workspace_member_workspace_id", table_name="workspace_member")
        op.drop_table("workspace_member")

    if "user_account" in _table_names():
        if "ix_user_account_external_id" in _index_names("user_account"):
            op.drop_index("ix_user_account_external_id", table_name="user_account")
        op.drop_table("user_account")

    if "workspace" in _table_names():
        if "ix_workspace_slug" in _index_names("workspace"):
            op.drop_index("ix_workspace_slug", table_name="workspace")
        op.drop_table("workspace")
