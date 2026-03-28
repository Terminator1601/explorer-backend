import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserOut
from app.services.auth_service import get_current_user
from app.services import follow_service

router = APIRouter(prefix="/users", tags=["follows"])


@router.post("/{user_id}/follow", status_code=201)
def follow_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    follow_service.follow_user(db, current_user.id, user_id)
    return {"message": "Followed successfully"}


@router.delete("/{user_id}/follow", status_code=204)
def unfollow_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    follow_service.unfollow_user(db, current_user.id, user_id)
    return None


@router.get("/me/following", response_model=list[UserOut])
def get_my_following(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return follow_service.get_following(db, current_user.id)


@router.get("/{user_id}/followers", response_model=list[UserOut])
def get_user_followers(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    return follow_service.get_followers(db, user_id)
