import uuid

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.comment import Comment


def create_comment(db: Session, event_id: uuid.UUID, user_id: uuid.UUID, text: str) -> Comment:
    comment = Comment(event_id=event_id, user_id=user_id, text=text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comments(db: Session, event_id: uuid.UUID, limit: int = 20, offset: int = 0) -> list[Comment]:
    return (
        db.query(Comment)
        .filter(Comment.event_id == event_id)
        .order_by(Comment.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def delete_comment(db: Session, comment_id: uuid.UUID, user_id: uuid.UUID, event_creator_id: uuid.UUID) -> None:
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.user_id != user_id and event_creator_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this comment")
    db.delete(comment)
    db.commit()
