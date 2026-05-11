from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProjectStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    voice_profiles = relationship("VoiceProfile", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")


class VoiceProfile(Base):
    __tablename__ = "voice_profiles"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    sample_path = Column(String, nullable=False)
    model_path = Column(String, nullable=True)
    duration_seconds = Column(Float, nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PENDING)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", back_populates="voice_profiles")
    projects = relationship("Project", back_populates="voice_profile")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    voice_profile_id = Column(String, ForeignKey("voice_profiles.id"), nullable=False)
    title = Column(String, nullable=False)
    lyrics = Column(Text, nullable=False)
    reference_audio_path = Column(String, nullable=True)
    output_audio_path = Column(String, nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PENDING)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="projects")
    voice_profile = relationship("VoiceProfile", back_populates="projects")
