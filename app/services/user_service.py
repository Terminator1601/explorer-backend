import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.user import User
from app.models.event import Event
from app.models.event_participant import EventParticipant, ParticipantStatus
from app.schemas.user import UserCreate, UserUpdate, UserStats
from app.services.auth_service import hash_password


def create_user(db: Session, data: UserCreate) -> User:
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        gender=data.gender,
        profile_picture=data.profile_picture,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def get_user_stats(db: Session, user_id: uuid.UUID) -> UserStats:
    events_created = db.query(Event).filter(Event.created_by == user_id).count()
    events_attended = (
        db.query(func.count(func.distinct(EventParticipant.event_id)))
        .filter(
            EventParticipant.user_id == user_id,
            EventParticipant.status == ParticipantStatus.joined,
        )
        .scalar()
        or 0
    )
    return UserStats(
        events_created=events_created,
        events_attended=events_attended,
        total_events_created=events_created,
        total_events_attended=events_attended,
    )
