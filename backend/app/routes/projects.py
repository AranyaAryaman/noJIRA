from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.database import get_db
from app.models import (
    Person,
    Project,
    ProjectMember,
    ProjectTeam,
    TeamMember,
    ProjectRole,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectWithDetails,
    ProjectMemberAdd,
    ProjectMemberUpdate,
    ProjectMemberResponse,
    ProjectTeamAdd,
    ProjectTeamResponse,
)
from app.schemas.person import PersonBrief
from app.schemas.team import TeamResponse
from app.services.auth import get_current_user
from app.services.permissions import check_project_access, check_project_admin

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    project = Project(
        name=project_data.name,
        description=project_data.description,
        created_by=current_user.person_id,
    )
    db.add(project)
    db.flush()

    # Add creator as admin
    member = ProjectMember(
        project_id=project.project_id,
        person_id=current_user.person_id,
        role=ProjectRole.ADMIN,
    )
    db.add(member)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    # Projects via direct membership
    direct_project_ids = (
        db.query(ProjectMember.project_id)
        .filter(ProjectMember.person_id == current_user.person_id)
        .subquery()
    )

    # Projects via team membership
    user_team_ids = (
        db.query(TeamMember.team_id)
        .filter(TeamMember.person_id == current_user.person_id)
        .subquery()
    )
    team_project_ids = (
        db.query(ProjectTeam.project_id)
        .filter(ProjectTeam.team_id.in_(user_team_ids))
        .subquery()
    )

    query = db.query(Project).filter(
        or_(
            Project.project_id.in_(direct_project_ids),
            Project.project_id.in_(team_project_ids),
        )
    )

    if not include_archived:
        query = query.filter(Project.is_archived == False)

    return query.all()


@router.get("/{project_id}", response_model=ProjectWithDetails)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    check_project_access(db, project_id, current_user)

    project = (
        db.query(Project)
        .options(
            joinedload(Project.members).joinedload(ProjectMember.person),
            joinedload(Project.teams).joinedload(ProjectTeam.team),
        )
        .filter(Project.project_id == project_id)
        .first()
    )

    members = [
        ProjectMemberResponse(
            person=PersonBrief.model_validate(pm.person),
            role=pm.role,
        )
        for pm in project.members
    ]

    teams = [
        ProjectTeamResponse(team=TeamResponse.model_validate(pt.team))
        for pt in project.teams
    ]

    return ProjectWithDetails(
        project_id=project.project_id,
        name=project.name,
        description=project.description,
        created_by=project.created_by,
        created_at=project.created_at,
        is_archived=project.is_archived,
        members=members,
        teams=teams,
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    project = check_project_admin(db, project_id, current_user)

    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.is_archived is not None:
        project.is_archived = project_data.is_archived

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    project = check_project_admin(db, project_id, current_user)
    db.delete(project)
    db.commit()


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
def add_project_member(
    project_id: int,
    member_data: ProjectMemberAdd,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    check_project_admin(db, project_id, current_user)

    person = db.query(Person).filter(Person.person_id == member_data.person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.person_id == member_data.person_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already a member")

    member = ProjectMember(
        project_id=project_id,
        person_id=member_data.person_id,
        role=member_data.role,
    )
    db.add(member)
    db.commit()

    return ProjectMemberResponse(
        person=PersonBrief.model_validate(person),
        role=member.role,
    )


@router.patch("/{project_id}/members/{person_id}", response_model=ProjectMemberResponse)
def update_project_member(
    project_id: int,
    person_id: int,
    member_data: ProjectMemberUpdate,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    check_project_admin(db, project_id, current_user)

    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.person_id == person_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.role = member_data.role
    db.commit()

    person = db.query(Person).filter(Person.person_id == person_id).first()
    return ProjectMemberResponse(
        person=PersonBrief.model_validate(person),
        role=member.role,
    )


@router.delete("/{project_id}/members/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(
    project_id: int,
    person_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    check_project_admin(db, project_id, current_user)

    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.person_id == person_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    db.delete(member)
    db.commit()


@router.post("/{project_id}/teams", response_model=ProjectTeamResponse, status_code=status.HTTP_201_CREATED)
def add_project_team(
    project_id: int,
    team_data: ProjectTeamAdd,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    check_project_admin(db, project_id, current_user)

    from app.models import Team

    team = db.query(Team).filter(Team.team_id == team_data.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    existing = (
        db.query(ProjectTeam)
        .filter(
            ProjectTeam.project_id == project_id,
            ProjectTeam.team_id == team_data.team_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Team already added")

    project_team = ProjectTeam(
        project_id=project_id,
        team_id=team_data.team_id,
    )
    db.add(project_team)
    db.commit()

    return ProjectTeamResponse(team=TeamResponse.model_validate(team))


@router.delete("/{project_id}/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_team(
    project_id: int,
    team_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    check_project_admin(db, project_id, current_user)

    project_team = (
        db.query(ProjectTeam)
        .filter(
            ProjectTeam.project_id == project_id,
            ProjectTeam.team_id == team_id,
        )
        .first()
    )
    if not project_team:
        raise HTTPException(status_code=404, detail="Team not in project")

    db.delete(project_team)
    db.commit()
