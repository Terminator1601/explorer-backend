import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Enum, DateTime, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ParticipantStatus(str, enum.Enum):
    joined = "joined"
    pending = "pending"


class EventParticipant(Base):
    __tablename__ = "event_participants"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_user_event"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("events.id"), nullable=False
    )
    status: Mapped[ParticipantStatus] = mapped_column(
        Enum(ParticipantStatus, native_enum=False, length=10),
        nullable=False,
        default=ParticipantStatus.joined,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    event = relationship("Event", back_populates="participants")
    user = relationship("User", lazy="selectin")
