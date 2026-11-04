import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    language: Mapped[str] = mapped_column(String(2))
    total_words: Mapped[int]
    unique_words: Mapped[int]

    words: Mapped[list["AnalysisWord"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )


class AnalysisWord(Base):
    """How many times one meaningful word appeared in one analysis."""

    __tablename__ = "analysis_words"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), primary_key=True
    )
    word: Mapped[str] = mapped_column(String(100), primary_key=True)
    count: Mapped[int]

    analysis: Mapped[Analysis] = relationship(back_populates="words")
