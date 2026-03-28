import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.follow import Follow
from app.models.user import User


def follow_user(db: Session, follower_id: uuid.UUID, following_id: uuid.UUID) -> Follow:
    if follower_id == following_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow yourself")

    target = db.query(User).filter(User.id == following_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = (
        db.query(Follow)
        .filter(Follow.follower_id == follower_id, Follow.following_id == following_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already following this user")

    follow = Follow(follower_id=follower_id, following_id=following_id)
    db.add(follow)
    db.commit()
    db.refresh(follow)
    return follow


def unfollow_user(db: Session, follower_id: uuid.UUID, following_id: uuid.UUID) -> None:
    follow = (
        db.query(Follow)
        .filter(Follow.follower_id == follower_id, Follow.following_id == following_id)
        .first()
    )
    if not follow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not following this user")
    db.delete(follow)
    db.commit()


def is_following(db: Session, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
    return (
        db.query(Follow)
        .filter(Follow.follower_id == follower_id, Follow.following_id == following_id)
        .first()
    ) is not None


def get_follower_count(db: Session, user_id: uuid.UUID) -> int:
    return db.query(func.count(Follow.id)).filter(Follow.following_id == user_id).scalar() or 0


def get_following_count(db: Session, user_id: uuid.UUID) -> int:
    return db.query(func.count(Follow.id)).filter(Follow.follower_id == user_id).scalar() or 0


def get_following(db: Session, user_id: uuid.UUID) -> list[User]:
    follows = db.query(Follow).filter(Follow.follower_id == user_id).all()
    return [f.following for f in follows]


def get_followers(db: Session, user_id: uuid.UUID) -> list[User]:
    follows = db.query(Follow).filter(Follow.following_id == user_id).all()
    return [f.follower for f in follows]
