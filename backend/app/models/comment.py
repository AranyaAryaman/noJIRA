from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Comment(Base):
    __tablename__ = "comment"

    comment_id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("task.task_id", ondelete="CASCADE"))
    person_id: Mapped[int] = mapped_column(ForeignKey("person.person_id"))
    text: Mapped[str] = mapped_column(Text)
    is_system_comment: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    task: Mapped["Task"] = relationship(back_populates="comments")
    person: Mapped["Person"] = relationship(back_populates="comments")
    attachments: Mapped[list["CommentAttachment"]] = relationship(back_populates="comment", cascade="all, delete-orphan")


class CommentAttachment(Base):
    __tablename__ = "comment_attachment"

    attachment_id: Mapped[int] = mapped_column(primary_key=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comment.comment_id", ondelete="CASCADE"))
    file_name: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(100))
    file_path: Mapped[str] = mapped_column(String(500))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    comment: Mapped["Comment"] = relationship(back_populates="attachments")
