from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    source_type: str = "youtube"  # youtube|upload|rss|doc etc
    source_ref: str  # e.g., url
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Artifact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
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
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")
    task_id: Optional[str] = None  # Celery task id
    input: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    output: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
