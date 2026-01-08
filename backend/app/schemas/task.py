from pydantic import BaseModel, field_validator
from datetime import datetime
from app.models.task import TaskStatus
from app.schemas.person import PersonBrief


class TaskBase(BaseModel):
    name: str
    description: str | None = None
    assignee_id: int | None = None
    status: TaskStatus = TaskStatus.NOT_STARTED
    severity: int = 3
    priority: int = 3
    due_date: datetime | None = None
    parent_task_id: int | None = None

    @field_validator("severity", "priority")
    @classmethod
    def validate_range(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("Must be between 1 and 5")
        return v


class TaskCreate(TaskBase):
    project_id: int
    tags: list[str] = []


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    assignee_id: int | None = None
    status: TaskStatus | None = None
    severity: int | None = None
    priority: int | None = None
    due_date: datetime | None = None
    is_archived: bool | None = None
    tags: list[str] | None = None

    @field_validator("severity", "priority")
    @classmethod
    def validate_range(cls, v: int | None) -> int | None:
        if v is not None and not 1 <= v <= 5:
            raise ValueError("Must be between 1 and 5")
        return v


class TaskTagResponse(BaseModel):
    tag: str

    class Config:
        from_attributes = True


class TaskAttachmentResponse(BaseModel):
    attachment_id: int
    file_name: str
    file_type: str
    uploaded_by: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class TaskResponse(TaskBase):
    task_id: int
    project_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    is_archived: bool
    tags: list[TaskTagResponse] = []

    class Config:
        from_attributes = True


class TaskWithDetails(TaskResponse):
    assignee: PersonBrief | None = None
    creator: PersonBrief | None = None
    attachments: list[TaskAttachmentResponse] = []
    subtask_count: int = 0


class TaskBrief(BaseModel):
    task_id: int
    name: str
    status: TaskStatus
    assignee: PersonBrief | None = None
    priority: int
    severity: int

    class Config:
        from_attributes = True
