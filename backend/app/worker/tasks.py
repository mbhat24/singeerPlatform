from __future__ import annotations

from datetime import datetime, timezone

from celery import Celery
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings

celery_app = Celery(
    "singer_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


def _get_sync_session() -> Session:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite+aiosqlite"):
        db_url = db_url.replace("sqlite+aiosqlite:///", "sqlite:///", 1)

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def train_voice_model(self, voice_profile_id: str) -> dict:
    from app.models import ProjectStatus, VoiceProfile
    from app.services.voice_clone import voice_cloning_service

    session = _get_sync_session()
    try:
        profile = session.execute(
            select(VoiceProfile).where(VoiceProfile.id == voice_profile_id)
        ).scalar_one_or_none()

        if not profile:
            return {"status": "error", "message": "Voice profile not found"}

        profile.status = ProjectStatus.PROCESSING
        session.commit()

        model_path = voice_cloning_service.train_voice_model(
            voice_profile_id, profile.sample_path
        )

        profile.model_path = str(model_path)
        profile.status = ProjectStatus.COMPLETED
        session.commit()

        return {"status": "completed", "model_path": str(model_path)}

    except Exception as exc:
        profile = session.execute(
            select(VoiceProfile).where(VoiceProfile.id == voice_profile_id)
        ).scalar_one_or_none()
        if profile:
            profile.status = ProjectStatus.FAILED
            session.commit()
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def generate_singing(self, project_id: str) -> dict:
    from app.models import Project, ProjectStatus
    from app.services.voice_clone import voice_cloning_service

    session = _get_sync_session()
    try:
        project = session.execute(
            select(Project).where(Project.id == project_id)
        ).scalar_one_or_none()

        if not project:
            return {"status": "error", "message": "Project not found"}

        project.status = ProjectStatus.PROCESSING
        session.commit()

        output_path = voice_cloning_service.generate_singing(
            voice_profile_id=project.voice_profile_id,
            lyrics=project.lyrics,
            reference_audio_path=project.reference_audio_path,
        )

        project.output_audio_path = str(output_path)
        project.status = ProjectStatus.COMPLETED
        project.completed_at = datetime.now(timezone.utc)
        session.commit()

        return {"status": "completed", "output_path": str(output_path)}

    except Exception as exc:
        project = session.execute(
            select(Project).where(Project.id == project_id)
        ).scalar_one_or_none()
        if project:
            project.status = ProjectStatus.FAILED
            project.error_message = str(exc)
            session.commit()
        raise self.retry(exc=exc)
    finally:
        session.close()
