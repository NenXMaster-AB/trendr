from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..db import get_session
from ..models import Project
from ..schemas import ProjectCreate, ProjectOut

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("", response_model=ProjectOut)
def create_project(payload: ProjectCreate, session: Session = Depends(get_session)):
    project = Project(name=payload.name, source_type=payload.source_type, source_ref=payload.source_ref)
    session.add(project)
    session.commit()
    session.refresh(project)
    return ProjectOut(id=project.id, name=project.name, source_type=project.source_type, source_ref=project.source_ref)

@router.get("", response_model=list[ProjectOut])
def list_projects(session: Session = Depends(get_session)):
    rows = session.exec(select(Project).order_by(Project.id.desc())).all()
    return [ProjectOut(id=p.id, name=p.name, source_type=p.source_type, source_ref=p.source_ref) for p in rows]


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, session: Session = Depends(get_session)):
    project = session.exec(select(Project).where(Project.id == project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(
        id=project.id,
        name=project.name,
        source_type=project.source_type,
        source_ref=project.source_ref,
    )
