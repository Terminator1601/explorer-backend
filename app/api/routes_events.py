import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.event import EventCreate, EventOut, JoinResponse
from app.services.auth_service import get_current_user, decode_token
from app.services import event_service

router = APIRouter(prefix="/events", tags=["events"])


def _get_optional_user_id(authorization: Optional[str] = Header(None)) -> Optional[uuid.UUID]:
    """Extract user ID from Bearer token if present, without raising on missing auth."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ", 1)[1]
        user_id_str = decode_token(token)
        return uuid.UUID(user_id_str)
    except Exception:
        return None


@router.post("", response_model=EventOut, status_code=201)
def create_event(
    body: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = event_service.create_event(db, body, current_user.id)
    return _event_to_out(db, event, current_user_id=current_user.id)


@router.get("/nearby", response_model=list[EventOut])
def get_nearby_events(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: float = Query(5000.0, description="Radius in meters"),
    interest_tag: Optional[str] = Query(None),
    user_id: Optional[uuid.UUID] = Depends(_get_optional_user_id),
    db: Session = Depends(get_db),
):
    rows = event_service.get_nearby_events(db, lat, lng, radius, interest_tag)
    results = []
    for row in rows:
        out = _event_to_out(db, row["event"], current_user_id=user_id)
        out.distance_meters = row["distance_meters"]
        results.append(out)
    return results


@router.get("/{event_id}", response_model=EventOut)
def get_event(
    event_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Depends(_get_optional_user_id),
    db: Session = Depends(get_db),
):
    event = event_service.get_event_by_id(db, event_id)
    return _event_to_out(db, event, current_user_id=user_id)


@router.post("/{event_id}/join", response_model=JoinResponse)
def join_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    participant = event_service.join_event(db, event_id, current_user.id)
    return JoinResponse(
        message="Successfully joined the event",
        event_id=event_id,
        user_id=current_user.id,
        status=participant.status.value,
    )


def _event_to_out(
    db: Session, event, current_user_id: Optional[uuid.UUID] = None
) -> EventOut:
    count = event_service.get_participant_count(db, event.id)
    is_participant = False
    if current_user_id:
        is_participant = event_service.is_user_participant(db, event.id, current_user_id)
    return EventOut(
        id=event.id,
        title=event.title,
        description=event.description,
        latitude=event.latitude,
        longitude=event.longitude,
        start_time=event.start_time,
        end_time=event.end_time,
        max_participants=event.max_participants,
        is_private=event.is_private,
        interest_tag=event.interest_tag,
        created_by=event.created_by,
        created_at=event.created_at,
        creator=event.creator,
        participant_count=count,
        is_user_participant=is_participant,
    )
