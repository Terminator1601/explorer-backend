import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.event import EventCreate, EventUpdate, EventOut, JoinResponse, LeaveResponse
from app.schemas.comment import CommentCreate, CommentOut
from app.schemas.review import ReviewCreate, ReviewOut
from app.services.auth_service import get_current_user, decode_token
from app.services import event_service, comment_service, bookmark_service, review_service

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
    radius: float = Query(50000.0, description="Radius in meters"),
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


@router.get("/recommended", response_model=list[EventOut])
def get_recommended_events(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: float = Query(50000.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    interests = current_user.interests or []
    if not interests:
        rows = event_service.get_nearby_events(db, lat, lng, radius)
    else:
        all_events = []
        seen_ids = set()
        for tag in interests:
            tag_rows = event_service.get_nearby_events(db, lat, lng, radius, tag)
            for row in tag_rows:
                eid = row["event"].id
                if eid not in seen_ids:
                    seen_ids.add(eid)
                    all_events.append(row)
        rows = sorted(all_events, key=lambda r: r["distance_meters"] or 0)

    results = []
    for row in rows:
        out = _event_to_out(db, row["event"], current_user_id=current_user.id)
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


@router.delete("/{event_id}/join", response_model=LeaveResponse)
def leave_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event_service.leave_event(db, event_id, current_user.id)
    return LeaveResponse(
        message="Successfully left the event",
        event_id=event_id,
        user_id=current_user.id,
    )


@router.patch("/{event_id}", response_model=EventOut)
def update_event(
    event_id: uuid.UUID,
    body: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = event_service.update_event(db, event_id, current_user.id, body)
    return _event_to_out(db, event, current_user_id=current_user.id)


@router.delete("/{event_id}", status_code=204)
def delete_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event_service.delete_event(db, event_id, current_user.id)
    return None


@router.post("/{event_id}/comments", response_model=CommentOut, status_code=201)
def create_comment(
    event_id: uuid.UUID,
    body: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event_service.get_event_by_id(db, event_id)
    comment = comment_service.create_comment(db, event_id, current_user.id, body.text)
    return comment


@router.get("/{event_id}/comments", response_model=list[CommentOut])
def get_comments(
    event_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return comment_service.get_comments(db, event_id, limit, offset)


@router.delete("/{event_id}/comments/{comment_id}", status_code=204)
def delete_comment(
    event_id: uuid.UUID,
    comment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = event_service.get_event_by_id(db, event_id)
    comment_service.delete_comment(db, comment_id, current_user.id, event.created_by)
    return None


@router.post("/{event_id}/bookmark")
def toggle_bookmark(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event_service.get_event_by_id(db, event_id)
    is_bookmarked = bookmark_service.toggle_bookmark(db, event_id, current_user.id)
    return {"bookmarked": is_bookmarked}


@router.post("/{event_id}/reviews", response_model=ReviewOut, status_code=201)
def create_review(
    event_id: uuid.UUID,
    body: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = review_service.create_review(db, event_id, current_user.id, body.rating, body.text)
    return review


@router.get("/{event_id}/reviews", response_model=list[ReviewOut])
def get_reviews(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    return review_service.get_reviews(db, event_id)


def _event_to_out(
    db: Session, event, current_user_id: Optional[uuid.UUID] = None
) -> EventOut:
    count = event_service.get_participant_count(db, event.id)
    is_participant = False
    is_bookmarked = False
    if current_user_id:
        is_participant = event_service.is_user_participant(db, event.id, current_user_id)
        is_bookmarked = bookmark_service.is_bookmarked(db, event.id, current_user_id)

    avg_rating, review_count = review_service.get_average_rating(db, event.id)

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
        cover_image=event.cover_image,
        media_urls=event.media_urls or [],
        created_by=event.created_by,
        created_at=event.created_at,
        creator=event.creator,
        participant_count=count,
        is_user_participant=is_participant,
        is_bookmarked=is_bookmarked,
        average_rating=avg_rating,
        review_count=review_count,
    )
