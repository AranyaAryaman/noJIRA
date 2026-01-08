from pydantic import BaseModel
from datetime import datetime
from app.schemas.person import PersonBrief


class CommentBase(BaseModel):
    text: str


class CommentCreate(CommentBase):
    task_id: int


class CommentUpdate(BaseModel):
    text: str


class CommentAttachmentResponse(BaseModel):
    attachment_id: int
    file_name: str
    file_type: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class CommentResponse(CommentBase):
    comment_id: int
    task_id: int
    person_id: int
    is_system_comment: bool
    created_at: datetime
    edited_at: datetime | None = None
    person: PersonBrief | None = None
    attachments: list[CommentAttachmentResponse] = []

    class Config:
        from_attributes = True
