from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON
from sqlalchemy import UniqueConstraint


class Workspace(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    slug: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserAccount(SQLModel, table=True):
    __tablename__ = "user_account"

    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkspaceMember(SQLModel, table=True):
    __tablename__ = "workspace_member"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member_workspace_user"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    user_id: int = Field(foreign_key="user_account.id", index=True)
    role: str = "member"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    name: str
    source_type: str = "youtube"  # youtube|upload|rss|doc etc
    source_ref: str  # e.g., url
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Artifact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    project_id: int = Field(foreign_key="project.id")
    kind: str  # transcript|tweet|linkedin|blog|image|thumbnail|icon
    title: str = ""
    content: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kind: str  # ingest|generate|workflow
    status: str = "queued"  # queued|running|succeeded|failed
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")
    task_id: Optional[str] = None  # Celery task id
    input: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    output: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Template(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "name",
            "kind",
            "version",
            name="uq_template_workspace_name_kind_version",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    name: str
    kind: str  # tweet|linkedin|blog
    version: int = 1
    content: str
    meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
