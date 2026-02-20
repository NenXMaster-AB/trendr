"""initial schema

Revision ID: 20260220_0001
Revises:
Create Date: 2026-02-20 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260220_0001"
down_revision = None
branch_labels = None
depends_on = None


def _table_names() -> set[str]:
    bind = op.get_bind()
    return set(sa.inspect(bind).get_table_names())


def _index_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    existing_tables = _table_names()

    if "project" not in existing_tables:
        op.create_table(
            "project",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("source_type", sa.String(), nullable=False),
            sa.Column("source_ref", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if "artifact" not in existing_tables:
        op.create_table(
            "artifact",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("kind", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("content", sa.String(), nullable=False),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "job" not in existing_tables:
        op.create_table(
            "job",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("kind", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=True),
            sa.Column("task_id", sa.String(), nullable=True),
            sa.Column("input", sa.JSON(), nullable=True),
            sa.Column("output", sa.JSON(), nullable=True),
            sa.Column("error", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    current_tables = _table_names()
    if "artifact" in current_tables and "ix_artifact_project_id" not in _index_names("artifact"):
        op.create_index("ix_artifact_project_id", "artifact", ["project_id"])
    if "job" in current_tables and "ix_job_project_id" not in _index_names("job"):
        op.create_index("ix_job_project_id", "job", ["project_id"])


def downgrade() -> None:
    existing_tables = _table_names()

    if "job" in existing_tables:
        if "ix_job_project_id" in _index_names("job"):
            op.drop_index("ix_job_project_id", table_name="job")
        op.drop_table("job")

    if "artifact" in existing_tables:
        if "ix_artifact_project_id" in _index_names("artifact"):
            op.drop_index("ix_artifact_project_id", table_name="artifact")
        op.drop_table("artifact")

    if "project" in existing_tables:
        op.drop_table("project")
