from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from app.database import get_db
from app.models import Person, Comment
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse
from app.schemas.person import PersonBrief
from app.services.auth import get_current_user
from app.services.permissions import check_task_access, check_comment_owner

router = APIRouter()


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    check_task_access(db, comment_data.task_id, current_user)

    comment = Comment(
        task_id=comment_data.task_id,
        person_id=current_user.person_id,
        text=comment_data.text,
        is_system_comment=False,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return _comment_to_response(db, comment)


@router.get("/task/{task_id}", response_model=list[CommentResponse])
def list_comments(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    check_task_access(db, task_id, current_user)

    comments = (
        db.query(Comment)
        .options(joinedload(Comment.person), joinedload(Comment.attachments))
        .filter(Comment.task_id == task_id)
        .order_by(Comment.created_at.asc())
        .all()
    )

    return [_comment_to_response(db, c) for c in comments]


@router.patch("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    comment = check_comment_owner(db, comment_id, current_user)

    comment.text = comment_data.text
    comment.edited_at = datetime.utcnow()

    db.commit()
    db.refresh(comment)

    return _comment_to_response(db, comment)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    comment = check_comment_owner(db, comment_id, current_user)
    db.delete(comment)
    db.commit()


def _comment_to_response(db: Session, comment: Comment) -> CommentResponse:
    """Convert comment to response."""
    comment_with_relations = (
        db.query(Comment)
        .options(joinedload(Comment.person), joinedload(Comment.attachments))
        .filter(Comment.comment_id == comment.comment_id)
        .first()
    )

    return CommentResponse(
        comment_id=comment_with_relations.comment_id,
        task_id=comment_with_relations.task_id,
        person_id=comment_with_relations.person_id,
        text=comment_with_relations.text,
        is_system_comment=comment_with_relations.is_system_comment,
        created_at=comment_with_relations.created_at,
        edited_at=comment_with_relations.edited_at,
        person=PersonBrief.model_validate(comment_with_relations.person) if comment_with_relations.person else None,
        attachments=[
            {
                "attachment_id": a.attachment_id,
                "file_name": a.file_name,
                "file_type": a.file_type,
                "uploaded_at": a.uploaded_at,
            }
            for a in comment_with_relations.attachments
        ],
    )
