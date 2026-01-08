from sqlalchemy.orm import Session
from app.models import Comment, Person, Task, TaskStatus


def create_system_comment(db: Session, task_id: int, person_id: int, text: str) -> Comment:
    """Create a system-generated comment."""
    comment = Comment(
        task_id=task_id,
        person_id=person_id,
        text=text,
        is_system_comment=True,
    )
    db.add(comment)
    return comment


def log_status_change(
    db: Session,
    task: Task,
    old_status: TaskStatus | None,
    new_status: TaskStatus,
    changed_by: Person,
) -> None:
    """Log a status change as system comment."""
    old_name = old_status.value if old_status else "None"
    text = f"Status changed from {old_name} to {new_status.value}"
    create_system_comment(db, task.task_id, changed_by.person_id, text)


def log_assignee_change(
    db: Session,
    task: Task,
    old_assignee: Person | None,
    new_assignee: Person | None,
    changed_by: Person,
) -> None:
    """Log an assignee change as system comment."""
    old_name = old_assignee.name if old_assignee else "Unassigned"
    new_name = new_assignee.name if new_assignee else "Unassigned"
    text = f"Assignee changed from {old_name} to {new_name}"
    create_system_comment(db, task.task_id, changed_by.person_id, text)
