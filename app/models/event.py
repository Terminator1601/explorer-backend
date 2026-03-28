import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, Float, Uuid, JSON, Uuid as UuidType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_participants: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    interest_tag: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    cover_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    media_urls: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    creator = relationship("User", back_populates="created_events", lazy="selectin")
    participants = relationship("EventParticipant", back_populates="event", lazy="selectin")
    comments = relationship("Comment", back_populates="event", lazy="selectin")
    reviews = relationship("Review", back_populates="event", lazy="selectin")
