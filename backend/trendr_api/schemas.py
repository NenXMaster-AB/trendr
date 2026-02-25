from __future__ import annotations
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime


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
    template_id: Optional[int] = None
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


class TemplateCreate(BaseModel):
    name: str
    kind: Literal["tweet", "linkedin", "blog"]
    content: str
    meta: Dict[str, Any] = Field(default_factory=dict)
    version: Optional[int] = None


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    kind: Optional[Literal["tweet", "linkedin", "blog"]] = None
    content: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class TemplateOut(BaseModel):
    id: int
    workspace_id: int
    name: str
    kind: Literal["tweet", "linkedin", "blog"]
    version: int
    content: str
    meta: Dict[str, Any]
    created_at: datetime


class WorkflowCreate(BaseModel):
    name: str
    definition_json: Dict[str, Any]


class WorkflowOut(BaseModel):
    id: int
    workspace_id: int
    name: str
    definition_json: Dict[str, Any]
    created_at: datetime


class WorkflowRunRequest(BaseModel):
    project_id: Optional[int] = None
    url: Optional[HttpUrl] = None
    project_name: Optional[str] = None
    outputs: List[Literal["tweet", "linkedin", "blog"]] = Field(
        default_factory=lambda: ["tweet", "linkedin", "blog"]
    )
    tone: str = "professional"
    brand_voice: Optional[str] = None
    template_id: Optional[int] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ProviderCapabilitiesOut(BaseModel):
    max_input_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
    supports_json_mode: bool = False
    supports_streaming: bool = False
    supports_system_prompt: bool = True


class ProviderOut(BaseModel):
    name: str
    available: bool
    capabilities: ProviderCapabilitiesOut


class ScheduledPostCreate(BaseModel):
    project_id: Optional[int] = None
    artifact_id: Optional[int] = None
    platform: str = "twitter"
    title: str = ""
    content: str = ""
    scheduled_at: datetime
    meta: Dict[str, Any] = Field(default_factory=dict)


class ScheduledPostUpdate(BaseModel):
    platform: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class ScheduledPostOut(BaseModel):
    id: int
    workspace_id: int
    project_id: Optional[int] = None
    artifact_id: Optional[int] = None
    platform: str
    title: str
    content: str
    scheduled_at: datetime
    status: str
    meta: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AnalyticsSummaryOut(BaseModel):
    kind: str
    count: int


class TimelinePointOut(BaseModel):
    date: str
    kind: str
    count: int


class MediaGenerateRequest(BaseModel):
    project_id: int
    prompt: str
    kind: str = "image"
    size: str = "1024x1024"
    quality: str = "standard"
    style: str = "vivid"


class ProviderApiKeyUpdate(BaseModel):
    api_key: str = Field(min_length=8, max_length=500)


class ProviderSettingOut(BaseModel):
    provider: str
    has_api_key: bool
    key_hint: Optional[str] = None
    configured_via: Optional[Literal["workspace", "environment"]] = None
    updated_at: Optional[datetime] = None
