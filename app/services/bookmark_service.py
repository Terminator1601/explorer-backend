import uuid

from sqlalchemy.orm import Session

from app.models.bookmark import Bookmark
from app.models.event import Event


def toggle_bookmark(db: Session, event_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Returns True if bookmarked, False if removed."""
    existing = (
        db.query(Bookmark)
        .filter(Bookmark.event_id == event_id, Bookmark.user_id == user_id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        return False
    bookmark = Bookmark(event_id=event_id, user_id=user_id)
    db.add(bookmark)
    db.commit()
    return True


def is_bookmarked(db: Session, event_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    return (
        db.query(Bookmark)
        .filter(Bookmark.event_id == event_id, Bookmark.user_id == user_id)
        .first()
    ) is not None


def get_user_bookmarks(db: Session, user_id: uuid.UUID) -> list[Event]:
    bookmarks = (
        db.query(Bookmark)
        .filter(Bookmark.user_id == user_id)
        .order_by(Bookmark.created_at.desc())
        .all()
    )
    event_ids = [b.event_id for b in bookmarks]
    if not event_ids:
        return []
    return db.query(Event).filter(Event.id.in_(event_ids)).all()
