import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.review import Review
from app.models.event import Event
from app.models.event_participant import EventParticipant, ParticipantStatus


def create_review(
    db: Session, event_id: uuid.UUID, user_id: uuid.UUID, rating: int, text: str | None
) -> Review:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    now = datetime.now(timezone.utc)
    if event.end_time > now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot review an event that hasn't ended yet",
        )

    was_participant = (
        db.query(EventParticipant)
        .filter(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user_id,
            EventParticipant.status == ParticipantStatus.joined,
        )
        .first()
    )
    if not was_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only participants can review an event",
        )

    existing = (
        db.query(Review)
        .filter(Review.event_id == event_id, Review.user_id == user_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already reviewed this event")

    review = Review(event_id=event_id, user_id=user_id, rating=rating, text=text)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_reviews(db: Session, event_id: uuid.UUID) -> list[Review]:
    return (
        db.query(Review)
        .filter(Review.event_id == event_id)
        .order_by(Review.created_at.desc())
        .all()
    )


def get_average_rating(db: Session, event_id: uuid.UUID) -> tuple[float | None, int]:
    result = (
        db.query(func.avg(Review.rating), func.count(Review.id))
        .filter(Review.event_id == event_id)
        .first()
    )
    avg_rating = round(float(result[0]), 1) if result[0] else None
    count = result[1] or 0
    return avg_rating, count
