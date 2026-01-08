from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional

from app.database import get_db
from app.models import Person, Task, TaskTag, TaskStatus, TaskStatusHistory
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskWithDetails,
    TaskTagResponse,
)
from app.schemas.person import PersonBrief
from app.services.auth import get_current_user
from app.services.permissions import check_project_access, check_task_access
from app.services.system_comments import log_status_change, log_assignee_change

router = APIRouter()


@router.post("", response_model=TaskWithDetails, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    check_project_access(db, task_data.project_id, current_user)

    if task_data.parent_task_id:
        parent = db.query(Task).filter(Task.task_id == task_data.parent_task_id).first()
        if not parent or parent.project_id != task_data.project_id:
            raise HTTPException(status_code=400, detail="Invalid parent task")

    if task_data.assignee_id:
        assignee = db.query(Person).filter(Person.person_id == task_data.assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="Assignee not found")

    task = Task(
        project_id=task_data.project_id,
        parent_task_id=task_data.parent_task_id,
        name=task_data.name,
        description=task_data.description,
        assignee_id=task_data.assignee_id,
        status=task_data.status,
        severity=task_data.severity,
        priority=task_data.priority,
        due_date=task_data.due_date,
        created_by=current_user.person_id,
    )
    db.add(task)
    db.flush()

    # Add tags
    for tag_name in task_data.tags:
        tag = TaskTag(task_id=task.task_id, tag=tag_name)
        db.add(tag)

    # Record initial status
    history = TaskStatusHistory(
        task_id=task.task_id,
        old_status=None,
        new_status=task.status,
        changed_by=current_user.person_id,
    )
    db.add(history)

    db.commit()
    db.refresh(task)

    return _task_to_response(db, task)


@router.get("", response_model=list[TaskWithDetails])
def list_tasks(
    project_id: int,
    status: Optional[TaskStatus] = None,
    assignee_id: Optional[int] = None,
    severity: Optional[int] = None,
    include_archived: bool = False,
    parent_task_id: Optional[int] = Query(None, description="Filter by parent task (null for root tasks)"),
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    check_project_access(db, project_id, current_user)

    query = db.query(Task).filter(Task.project_id == project_id)

    if status:
        query = query.filter(Task.status == status)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    if severity:
        query = query.filter(Task.severity == severity)
    if not include_archived:
        query = query.filter(Task.is_archived == False)
    if parent_task_id is not None:
        query = query.filter(Task.parent_task_id == parent_task_id)

    tasks = query.order_by(Task.priority.desc(), Task.created_at.desc()).all()
    return [_task_to_response(db, t) for t in tasks]


@router.get("/{task_id}", response_model=TaskWithDetails)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    task = check_task_access(db, task_id, current_user)
    return _task_to_response(db, task)


@router.patch("/{task_id}", response_model=TaskWithDetails)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    task = check_task_access(db, task_id, current_user)

    # Track changes for system comments
    old_status = task.status
    old_assignee = task.assignee

    if task_data.name is not None:
        task.name = task_data.name
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.severity is not None:
        task.severity = task_data.severity
    if task_data.priority is not None:
        task.priority = task_data.priority
    if task_data.due_date is not None:
        task.due_date = task_data.due_date
    if task_data.is_archived is not None:
        task.is_archived = task_data.is_archived

    # Handle status change
    if task_data.status is not None and task_data.status != old_status:
        task.status = task_data.status
        history = TaskStatusHistory(
            task_id=task.task_id,
            old_status=old_status,
            new_status=task.status,
            changed_by=current_user.person_id,
        )
        db.add(history)
        log_status_change(db, task, old_status, task.status, current_user)

    # Handle assignee change
    if task_data.assignee_id is not None:
        new_assignee_id = task_data.assignee_id if task_data.assignee_id != 0 else None
        old_assignee_id = task.assignee_id

        if new_assignee_id != old_assignee_id:
            if new_assignee_id:
                assignee = db.query(Person).filter(Person.person_id == new_assignee_id).first()
                if not assignee:
                    raise HTTPException(status_code=404, detail="Assignee not found")
                task.assignee_id = new_assignee_id
            else:
                task.assignee_id = None

            new_assignee = db.query(Person).filter(Person.person_id == task.assignee_id).first() if task.assignee_id else None
            log_assignee_change(db, task, old_assignee, new_assignee, current_user)

    # Handle tags
    if task_data.tags is not None:
        db.query(TaskTag).filter(TaskTag.task_id == task.task_id).delete()
        for tag_name in task_data.tags:
            tag = TaskTag(task_id=task.task_id, tag=tag_name)
            db.add(tag)

    db.commit()
    db.refresh(task)
    return _task_to_response(db, task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    task = check_task_access(db, task_id, current_user)
    db.delete(task)
    db.commit()


def _task_to_response(db: Session, task: Task) -> TaskWithDetails:
    """Convert task to response with all details."""
    subtask_count = db.query(func.count(Task.task_id)).filter(Task.parent_task_id == task.task_id).scalar()

    task_with_relations = (
        db.query(Task)
        .options(
            joinedload(Task.assignee),
            joinedload(Task.creator),
            joinedload(Task.tags),
            joinedload(Task.attachments),
        )
        .filter(Task.task_id == task.task_id)
        .first()
    )

    return TaskWithDetails(
        task_id=task_with_relations.task_id,
        project_id=task_with_relations.project_id,
        parent_task_id=task_with_relations.parent_task_id,
        name=task_with_relations.name,
        description=task_with_relations.description,
        assignee_id=task_with_relations.assignee_id,
        status=task_with_relations.status,
        severity=task_with_relations.severity,
        priority=task_with_relations.priority,
        due_date=task_with_relations.due_date,
        created_by=task_with_relations.created_by,
        created_at=task_with_relations.created_at,
        updated_at=task_with_relations.updated_at,
        is_archived=task_with_relations.is_archived,
        tags=[TaskTagResponse(tag=t.tag) for t in task_with_relations.tags],
        assignee=PersonBrief.model_validate(task_with_relations.assignee) if task_with_relations.assignee else None,
        creator=PersonBrief.model_validate(task_with_relations.creator) if task_with_relations.creator else None,
        attachments=[
            {
                "attachment_id": a.attachment_id,
                "file_name": a.file_name,
                "file_type": a.file_type,
                "uploaded_by": a.uploaded_by,
                "uploaded_at": a.uploaded_at,
            }
            for a in task_with_relations.attachments
        ],
        subtask_count=subtask_count,
    )
