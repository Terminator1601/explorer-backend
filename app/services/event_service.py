import uuid
import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.event import Event
from app.models.event_participant import EventParticipant, ParticipantStatus
from app.schemas.event import EventCreate

EARTH_RADIUS_M = 6_371_000


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in meters between two points."""
    lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _rough_bbox(lat: float, lng: float, radius_m: float):
    """Return a (lat_min, lat_max, lng_min, lng_max) bounding box for pre-filtering."""
    delta_lat = radius_m / EARTH_RADIUS_M * (180 / math.pi)
    delta_lng = delta_lat / max(math.cos(math.radians(lat)), 1e-10)
    return lat - delta_lat, lat + delta_lat, lng - delta_lng, lng + delta_lng


def create_event(db: Session, data: EventCreate, user_id: uuid.UUID) -> Event:
    event = Event(
        title=data.title,
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
        start_time=data.start_time,
        end_time=data.end_time,
        max_participants=data.max_participants,
        is_private=data.is_private,
        interest_tag=data.interest_tag,
        cover_image=data.cover_image,
        media_urls=data.media_urls or [],
        created_by=user_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    participant = EventParticipant(
        user_id=user_id,
        event_id=event.id,
        status=ParticipantStatus.joined,
    )
    db.add(participant)
    db.commit()

    return event


def get_event_by_id(db: Session, event_id: uuid.UUID) -> Event:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


def get_nearby_events(
    db: Session, lat: float, lng: float, radius: float, interest_tag: str | None = None
) -> list[dict]:
    """
    Return upcoming/ongoing public events within `radius` meters of (lat, lng).
    Uses a bounding-box pre-filter in SQL then exact Haversine in Python.
    """
    now = datetime.now(timezone.utc)
    lat_min, lat_max, lng_min, lng_max = _rough_bbox(lat, lng, radius)

    query = (
        db.query(Event)
        .filter(
            Event.latitude.between(lat_min, lat_max),
            Event.longitude.between(lng_min, lng_max),
            Event.end_time >= now,
            Event.is_private.is_(False),
        )
    )

    if interest_tag:
        query = query.filter(Event.interest_tag == interest_tag)

    candidates = query.all()

    results = []
    for event in candidates:
        dist = _haversine(lat, lng, event.latitude, event.longitude)
        if dist <= radius:
            results.append({"event": event, "distance_meters": round(dist, 2)})

    results.sort(key=lambda r: r["distance_meters"])
    return results


def join_event(db: Session, event_id: uuid.UUID, user_id: uuid.UUID) -> EventParticipant:
    event = get_event_by_id(db, event_id)

    current_count = (
        db.query(EventParticipant)
        .filter(
            EventParticipant.event_id == event_id,
            EventParticipant.status == ParticipantStatus.joined,
        )
        .count()
    )
    if current_count >= event.max_participants:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event is full")

    existing = (
        db.query(EventParticipant)
        .filter(EventParticipant.event_id == event_id, EventParticipant.user_id == user_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already joined this event")

    participant = EventParticipant(
        user_id=user_id,
        event_id=event_id,
        status=ParticipantStatus.joined,
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def leave_event(db: Session, event_id: uuid.UUID, user_id: uuid.UUID) -> None:
    event = get_event_by_id(db, event_id)
    if event.created_by == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event creator cannot leave their own event",
        )
    participant = (
        db.query(EventParticipant)
        .filter(EventParticipant.event_id == event_id, EventParticipant.user_id == user_id)
        .first()
    )
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not a participant of this event")
    db.delete(participant)
    db.commit()


def update_event(db: Session, event_id: uuid.UUID, user_id: uuid.UUID, data) -> Event:
    event = get_event_by_id(db, event_id)
    if event.created_by != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the creator can edit this event")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event_id: uuid.UUID, user_id: uuid.UUID) -> None:
    event = get_event_by_id(db, event_id)
    if event.created_by != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the creator can delete this event")
    db.query(EventParticipant).filter(EventParticipant.event_id == event_id).delete()
    db.delete(event)
    db.commit()


def get_user_events(db: Session, user_id: uuid.UUID, event_type: str) -> list[dict]:
    now = datetime.now(timezone.utc)
    if event_type == "created":
        events = (
            db.query(Event)
            .filter(Event.created_by == user_id, Event.end_time >= now)
            .order_by(Event.start_time)
            .all()
        )
    else:
        events = (
            db.query(Event)
            .join(EventParticipant, EventParticipant.event_id == Event.id)
            .filter(
                EventParticipant.user_id == user_id,
                EventParticipant.status == ParticipantStatus.joined,
                Event.end_time >= now,
            )
            .order_by(Event.start_time)
            .all()
        )
    return [{"event": e, "distance_meters": None} for e in events]


def get_participant_count(db: Session, event_id: uuid.UUID) -> int:
    return (
        db.query(EventParticipant)
        .filter(
            EventParticipant.event_id == event_id,
            EventParticipant.status == ParticipantStatus.joined,
        )
        .count()
    )


def is_user_participant(db: Session, event_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    return (
        db.query(EventParticipant)
        .filter(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user_id,
            EventParticipant.status == ParticipantStatus.joined,
        )
        .first()
    ) is not None
