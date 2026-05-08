from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.db import get_db
from app.models import Project, ProjectStatus, User, VoiceProfile

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    voice_profile_id: str
    title: str
    lyrics: str


class ProjectResponse(BaseModel):
    id: str
    voice_profile_id: str
    title: str
    lyrics: str
    status: ProjectStatus
    error_message: str | None
    output_audio_path: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class ProjectList(BaseModel):
    projects: list[ProjectResponse]


@router.get("/", response_model=ProjectList)
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectList:
    result = await db.execute(
        select(Project)
        .where(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
    )
    return ProjectList(
        projects=[ProjectResponse.model_validate(p) for p in result.scalars().all()]
    )


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    vp_result = await db.execute(
        select(VoiceProfile).where(
            VoiceProfile.id == body.voice_profile_id,
            VoiceProfile.user_id == current_user.id,
            VoiceProfile.status == ProjectStatus.COMPLETED,
        )
    )
    voice_profile = vp_result.scalar_one_or_none()
    if not voice_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voice profile not found or not yet trained",
        )

    project = Project(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        voice_profile_id=body.voice_profile_id,
        title=body.title,
        lyrics=body.lyrics,
        status=ProjectStatus.PENDING,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    from app.worker.tasks import generate_singing
    generate_singing.delay(project.id)

    return ProjectResponse.model_validate(project)


@router.post("/{project_id}/reference-audio")
async def upload_reference_audio(
    project_id: str,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if not file.filename or not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".flac")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported audio format",
        )

    content = await file.read()
    upload_dir = settings.UPLOAD_DIR / current_user.id / "references"
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix
    ref_path = upload_dir / f"{project_id}{ext}"
    ref_path.write_bytes(content)

    project.reference_audio_path = str(ref_path)
    await db.commit()

    return {"message": "Reference audio uploaded", "path": str(ref_path)}


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}/download")
async def download_output(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
            Project.status == ProjectStatus.COMPLETED,
        )
    )
    project = result.scalar_one_or_none()
    if not project or not project.output_audio_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output audio not available",
        )

    path = Path(project.output_audio_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output file not found on disk",
        )

    return FileResponse(
        path,
        media_type="audio/wav",
        filename=f"{project.title}.wav",
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if project.output_audio_path:
        out = Path(project.output_audio_path)
        if out.exists():
            out.unlink()
    if project.reference_audio_path:
        ref = Path(project.reference_audio_path)
        if ref.exists():
            ref.unlink()

    await db.delete(project)
    await db.commit()
