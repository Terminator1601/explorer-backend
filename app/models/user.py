import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Enum, DateTime, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_picture: Mapped[str | None] = mapped_column(String(500), nullable=True)
    gender: Mapped[GenderEnum] = mapped_column(
        Enum(GenderEnum, native_enum=False, length=10), nullable=False
    )
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    interests: Mapped[list | None] = mapped_column(JSON, nullable=True)
    social_links: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    created_events = relationship("Event", back_populates="creator", lazy="selectin")
