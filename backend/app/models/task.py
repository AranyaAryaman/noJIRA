from datetime import datetime
from typing import Optional
import enum
from sqlalchemy import String, DateTime, ForeignKey, Enum, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TaskStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    PLANNING = "PLANNING"
    DEVELOPMENT = "DEVELOPMENT"
    TESTING = "TESTING"
    FINISHED = "FINISHED"


class Task(Base):
    __tablename__ = "task"

    task_id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.project_id", ondelete="CASCADE"))
    parent_task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("task.task_id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("person.person_id", ondelete="SET NULL"), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.NOT_STARTED)
    severity: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    priority: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("person.person_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="tasks")
    parent_task: Mapped[Optional["Task"]] = relationship(
        back_populates="subtasks", remote_side="Task.task_id"
    )
    subtasks: Mapped[list["Task"]] = relationship(back_populates="parent_task")
    assignee: Mapped[Optional["Person"]] = relationship(
        back_populates="assigned_tasks", foreign_keys=[assignee_id]
    )
    creator: Mapped["Person"] = relationship(
        back_populates="created_tasks", foreign_keys=[created_by]
    )
    tags: Mapped[list["TaskTag"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    watchers: Mapped[list["TaskWatcher"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    attachments: Mapped[list["TaskAttachment"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    status_history: Mapped[list["TaskStatusHistory"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class TaskTag(Base):
    __tablename__ = "task_tag"

    task_id: Mapped[int] = mapped_column(ForeignKey("task.task_id", ondelete="CASCADE"), primary_key=True)
    tag: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Relationships
    task: Mapped["Task"] = relationship(back_populates="tags")


class TaskWatcher(Base):
    __tablename__ = "task_watcher"

    task_id: Mapped[int] = mapped_column(ForeignKey("task.task_id", ondelete="CASCADE"), primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("person.person_id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    task: Mapped["Task"] = relationship(back_populates="watchers")
    person: Mapped["Person"] = relationship(back_populates="watched_tasks")


class TaskAttachment(Base):
    __tablename__ = "task_attachment"

    attachment_id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("task.task_id", ondelete="CASCADE"))
    file_name: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(100))
    file_path: Mapped[str] = mapped_column(String(500))
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("person.person_id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    task: Mapped["Task"] = relationship(back_populates="attachments")
    uploader: Mapped["Person"] = relationship("Person")


class TaskStatusHistory(Base):
    __tablename__ = "task_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("task.task_id", ondelete="CASCADE"))
    old_status: Mapped[Optional[TaskStatus]] = mapped_column(Enum(TaskStatus), nullable=True)
    new_status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus))
    changed_by: Mapped[int] = mapped_column(ForeignKey("person.person_id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    task: Mapped["Task"] = relationship(back_populates="status_history")
    changer: Mapped["Person"] = relationship("Person")
