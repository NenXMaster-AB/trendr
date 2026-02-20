from __future__ import annotations
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any, List, Literal


class ProjectCreate(BaseModel):
    name: str
    source_type: str = "youtube"
    source_ref: str


class ProjectOut(BaseModel):
    id: int
    workspace_id: int
    name: str
    source_type: str
    source_ref: str


class IngestYouTubeRequest(BaseModel):
    url: HttpUrl
    project_name: Optional[str] = None


class GenerateRequest(BaseModel):
    project_id: int
    outputs: List[Literal["tweet", "linkedin", "blog"]] = Field(default_factory=lambda: ["tweet", "linkedin", "blog"])
    tone: str = "professional"
    brand_voice: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class JobOut(BaseModel):
    id: int
    kind: str
    status: str
    workspace_id: int
    project_id: Optional[int] = None
    task_id: Optional[str] = None
    input: Dict[str, Any]
    output: Dict[str, Any]
    error: Optional[str] = None


class ArtifactUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
