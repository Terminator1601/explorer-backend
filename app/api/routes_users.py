import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate, UserStats
from app.schemas.event import EventOut
from app.services.auth_service import get_current_user
from app.services import user_service, event_service, bookmark_service, follow_service
from app.services.cloudinary_service import upload_media

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.update_user(db, current_user, body)


@router.get("/me/stats", response_model=UserStats)
def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.get_user_stats(db, current_user.id)


@router.post("/me/profile-picture", response_model=UserOut)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File name is required")

    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image uploads are allowed for profile pictures",
        )

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    unique_filename = f"profile-{current_user.id}-{file.filename}"
    result = upload_media(payload, unique_filename, content_type)

    current_user.profile_picture = result["secure_url"]
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/events", response_model=list[EventOut])
def get_my_events(
    type: str = Query("created", regex="^(created|joined)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = event_service.get_user_events(db, current_user.id, type)
    results = []
    for row in rows:
        out = _event_to_out(db, row["event"], current_user_id=current_user.id)
        results.append(out)
    return results


@router.get("/me/bookmarks", response_model=list[EventOut])
def get_my_bookmarks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    events = bookmark_service.get_user_bookmarks(db, current_user.id)
    from app.services import review_service
    results = []
    for event in events:
        out = _event_to_out(db, event, current_user_id=current_user.id)
        results.append(out)
    return results


def _event_to_out(db, event, current_user_id=None):
    from app.services import review_service as rv_svc
    count = event_service.get_participant_count(db, event.id)
    is_participant = False
    is_bookmarked_val = False
    if current_user_id:
        is_participant = event_service.is_user_participant(db, event.id, current_user_id)
        is_bookmarked_val = bookmark_service.is_bookmarked(db, event.id, current_user_id)
    avg_rating, review_count = rv_svc.get_average_rating(db, event.id)
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
        is_bookmarked=is_bookmarked_val,
        average_rating=avg_rating,
        review_count=review_count,
    )


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    return user_service.get_user_by_id(db, user_id)
