from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.db import get_db
from app.models import ProjectStatus, User, VoiceProfile

router = APIRouter(prefix="/api/voices", tags=["voices"])


class VoiceProfileResponse(BaseModel):
    id: str
    name: str
    duration_seconds: float
    status: ProjectStatus

    model_config = {"from_attributes": True}


class VoiceProfileList(BaseModel):
    profiles: list[VoiceProfileResponse]


@router.get("/", response_model=VoiceProfileList)
async def list_voice_profiles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoiceProfileList:
    result = await db.execute(
        select(VoiceProfile).where(VoiceProfile.user_id == current_user.id).order_by(VoiceProfile.created_at.desc())
    )
    return VoiceProfileList(profiles=[VoiceProfileResponse.model_validate(vp) for vp in result.scalars().all()])


@router.post("/upload", response_model=VoiceProfileResponse, status_code=status.HTTP_201_CREATED)
async def upload_voice_sample(
    name: str,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoiceProfileResponse:
    if not file.filename or not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".flac", ".ogg")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported audio format. Use WAV, MP3, M4A, FLAC, or OGG.")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    profile_id = str(uuid.uuid4())
    upload_dir = settings.UPLOAD_DIR / current_user.id / "voices"
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix
    sample_path = upload_dir / f"{profile_id}{ext}"
    sample_path.write_bytes(content)

    import librosa
    duration = librosa.get_duration(path=str(sample_path))
    if duration < settings.MIN_VOICE_SAMPLE_SECONDS:
        sample_path.unlink()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Audio too short. Minimum {settings.MIN_VOICE_SAMPLE_SECONDS}s required, got {duration:.1f}s")

    profile = VoiceProfile(
        id=profile_id,
        user_id=current_user.id,
        name=name,
        sample_path=str(sample_path),
        duration_seconds=duration,
        status=ProjectStatus.PROCESSING,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    try:
        from app.services.voice_clone import voice_cloning_service
        model_path = voice_cloning_service.train_voice_model(profile_id, str(sample_path))
        profile.model_path = str(model_path)
        profile.status = ProjectStatus.COMPLETED
    except Exception as e:
        profile.status = ProjectStatus.FAILED
    await db.commit()
    await db.refresh(profile)

    return VoiceProfileResponse.model_validate(profile)


@router.get("/{profile_id}", response_model=VoiceProfileResponse)
async def get_voice_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoiceProfileResponse:
    result = await db.execute(select(VoiceProfile).where(VoiceProfile.id == profile_id, VoiceProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice profile not found")
    return VoiceProfileResponse.model_validate(profile)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voice_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(VoiceProfile).where(VoiceProfile.id == profile_id, VoiceProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice profile not found")
    sample_file = Path(profile.sample_path)
    if sample_file.exists():
        sample_file.unlink()
    if profile.model_path:
        model_file = Path(profile.model_path)
        if model_file.exists():
            model_file.unlink()
    await db.delete(profile)
    await db.commit()
