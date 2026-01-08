import os
import uuid
import mimetypes
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Person, TaskAttachment, CommentAttachment
from app.config import get_settings
from app.services.auth import get_current_user
from app.services.permissions import check_task_access, check_comment_access

router = APIRouter()
settings = get_settings()


@router.post("/task/{task_id}", status_code=status.HTTP_201_CREATED)
def upload_task_attachment(
    task_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    check_task_access(db, task_id, current_user)

    file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.upload_dir, "tasks", str(task_id), unique_name)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb") as f:
        content = file.file.read()
        f.write(content)

    file_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"

    attachment = TaskAttachment(
        task_id=task_id,
        file_name=file.filename or "unnamed",
        file_type=file_type,
        file_path=file_path,
        uploaded_by=current_user.person_id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return {
        "attachment_id": attachment.attachment_id,
        "file_name": attachment.file_name,
        "file_type": attachment.file_type,
        "uploaded_at": attachment.uploaded_at,
    }


@router.get("/task/{attachment_id}/download")
def download_task_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    attachment = db.query(TaskAttachment).filter(TaskAttachment.attachment_id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    check_task_access(db, attachment.task_id, current_user)

    if not os.path.exists(attachment.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        attachment.file_path,
        filename=attachment.file_name,
        media_type=attachment.file_type,
    )


@router.delete("/task/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    attachment = db.query(TaskAttachment).filter(TaskAttachment.attachment_id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    check_task_access(db, attachment.task_id, current_user)

    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)

    db.delete(attachment)
    db.commit()


@router.post("/comment/{comment_id}", status_code=status.HTTP_201_CREATED)
def upload_comment_attachment(
    comment_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    check_comment_access(db, comment_id, current_user)

    file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.upload_dir, "comments", str(comment_id), unique_name)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb") as f:
        content = file.file.read()
        f.write(content)

    file_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"

    attachment = CommentAttachment(
        comment_id=comment_id,
        file_name=file.filename or "unnamed",
        file_type=file_type,
        file_path=file_path,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return {
        "attachment_id": attachment.attachment_id,
        "file_name": attachment.file_name,
        "file_type": attachment.file_type,
        "uploaded_at": attachment.uploaded_at,
    }


@router.get("/comment/{attachment_id}/download")
def download_comment_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    attachment = db.query(CommentAttachment).filter(CommentAttachment.attachment_id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    check_comment_access(db, attachment.comment_id, current_user)

    if not os.path.exists(attachment.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        attachment.file_path,
        filename=attachment.file_name,
        media_type=attachment.file_type,
    )


@router.delete("/comment/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    attachment = db.query(CommentAttachment).filter(CommentAttachment.attachment_id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    check_comment_access(db, attachment.comment_id, current_user)

    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)

    db.delete(attachment)
    db.commit()
