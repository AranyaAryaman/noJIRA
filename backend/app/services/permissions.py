from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import (
    Person,
    Project,
    ProjectMember,
    ProjectTeam,
    Team,
    TeamMember,
    Task,
    Comment,
    ProjectRole,
    TeamRole,
)


def check_project_access(
    db: Session, project_id: int, user: Person, min_role: ProjectRole = ProjectRole.VIEWER
) -> Project:
    """Check if user has access to project, return project if yes."""
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check direct membership
    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.person_id == user.person_id,
        )
        .first()
    )

    if member:
        role_hierarchy = {ProjectRole.ADMIN: 3, ProjectRole.MEMBER: 2, ProjectRole.VIEWER: 1}
        if role_hierarchy.get(member.role, 0) >= role_hierarchy.get(min_role, 0):
            return project

    # Check via team membership
    team_ids = (
        db.query(ProjectTeam.team_id)
        .filter(ProjectTeam.project_id == project_id)
        .subquery()
    )
    team_member = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id.in_(team_ids),
            TeamMember.person_id == user.person_id,
        )
        .first()
    )

    if team_member:
        # Team members get MEMBER-level access
        if min_role in [ProjectRole.VIEWER, ProjectRole.MEMBER]:
            return project

    # Creator always has access
    if project.created_by == user.person_id:
        return project

    raise HTTPException(status_code=403, detail="Access denied")


def check_project_admin(db: Session, project_id: int, user: Person) -> Project:
    """Check if user is project admin."""
    return check_project_access(db, project_id, user, ProjectRole.ADMIN)


def check_team_access(
    db: Session, team_id: int, user: Person, require_owner: bool = False
) -> Team:
    """Check if user has access to team."""
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    member = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.person_id == user.person_id,
        )
        .first()
    )

    if not member and team.created_by != user.person_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if require_owner:
        if team.created_by != user.person_id and (not member or member.role != TeamRole.OWNER):
            raise HTTPException(status_code=403, detail="Owner access required")

    return team


def check_task_access(db: Session, task_id: int, user: Person) -> Task:
    """Check if user has access to task via project."""
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    check_project_access(db, task.project_id, user)
    return task


def check_comment_access(db: Session, comment_id: int, user: Person) -> Comment:
    """Check if user can access/modify comment."""
    comment = db.query(Comment).filter(Comment.comment_id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    check_task_access(db, comment.task_id, user)
    return comment


def check_comment_owner(db: Session, comment_id: int, user: Person) -> Comment:
    """Check if user owns the comment."""
    comment = check_comment_access(db, comment_id, user)
    if comment.person_id != user.person_id:
        raise HTTPException(status_code=403, detail="Not comment owner")
    return comment
