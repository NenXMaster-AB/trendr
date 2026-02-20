from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import wait_for_db
from .plugins.providers import register_all

from .api.health import router as health_router
from .api.projects import router as projects_router
from .api.ingest import router as ingest_router
from .api.generate import router as generate_router
from .api.jobs import router as jobs_router
from .api.artifacts import router as artifacts_router
from .api.templates import router as templates_router
from .api.workflows import router as workflows_router
from .api.providers import router as providers_router

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    wait_for_db()
    register_all()

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(projects_router, prefix=settings.api_prefix)
app.include_router(ingest_router, prefix=settings.api_prefix)
app.include_router(generate_router, prefix=settings.api_prefix)
app.include_router(jobs_router, prefix=settings.api_prefix)
app.include_router(artifacts_router, prefix=settings.api_prefix)
app.include_router(templates_router, prefix=settings.api_prefix)
app.include_router(workflows_router, prefix=settings.api_prefix)
app.include_router(providers_router, prefix=settings.api_prefix)
