from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Person, Team, TeamMember, TeamRole
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamWithMembers,
    TeamMemberAdd,
    TeamMemberUpdate,
    TeamMemberResponse,
)
from app.schemas.person import PersonBrief
from app.services.auth import get_current_user
from app.services.permissions import check_team_access

router = APIRouter()


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    team_data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    team = Team(
        name=team_data.name,
        description=team_data.description,
        created_by=current_user.person_id,
    )
    db.add(team)
    db.flush()

    # Add creator as owner
    member = TeamMember(
        team_id=team.team_id,
        person_id=current_user.person_id,
        role=TeamRole.OWNER,
    )
    db.add(member)
    db.commit()
    db.refresh(team)
    return team


@router.get("", response_model=list[TeamResponse])
def list_teams(
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    # Return teams user is member of
    team_ids = (
        db.query(TeamMember.team_id)
        .filter(TeamMember.person_id == current_user.person_id)
        .subquery()
    )
    teams = db.query(Team).filter(Team.team_id.in_(team_ids)).all()
    return teams


@router.get("/{team_id}", response_model=TeamWithMembers)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    team = check_team_access(db, team_id, current_user)
    team = (
        db.query(Team)
        .options(joinedload(Team.members).joinedload(TeamMember.person))
        .filter(Team.team_id == team_id)
        .first()
    )

    members = []
    for tm in team.members:
        members.append(
            TeamMemberResponse(
                person=PersonBrief.model_validate(tm.person),
                role=tm.role,
            )
        )

    return TeamWithMembers(
        team_id=team.team_id,
        name=team.name,
        description=team.description,
        created_by=team.created_by,
        created_at=team.created_at,
        members=members,
    )


@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    team_data: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    team = check_team_access(db, team_id, current_user, require_owner=True)

    if team_data.name is not None:
        team.name = team_data.name
    if team_data.description is not None:
        team.description = team_data.description

    db.commit()
    db.refresh(team)
    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    team = check_team_access(db, team_id, current_user, require_owner=True)
    db.delete(team)
    db.commit()


@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
def add_team_member(
    team_id: int,
    member_data: TeamMemberAdd,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    check_team_access(db, team_id, current_user, require_owner=True)

    person = db.query(Person).filter(Person.person_id == member_data.person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    existing = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.person_id == member_data.person_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already a member")

    member = TeamMember(
        team_id=team_id,
        person_id=member_data.person_id,
        role=member_data.role,
    )
    db.add(member)
    db.commit()

    return TeamMemberResponse(
        person=PersonBrief.model_validate(person),
        role=member.role,
    )


@router.patch("/{team_id}/members/{person_id}", response_model=TeamMemberResponse)
def update_team_member(
    team_id: int,
    person_id: int,
    member_data: TeamMemberUpdate,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    check_team_access(db, team_id, current_user, require_owner=True)

    member = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.person_id == person_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.role = member_data.role
    db.commit()

    person = db.query(Person).filter(Person.person_id == person_id).first()
    return TeamMemberResponse(
        person=PersonBrief.model_validate(person),
        role=member.role,
    )


@router.delete("/{team_id}/members/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    team_id: int,
    person_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    check_team_access(db, team_id, current_user, require_owner=True)

    member = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.person_id == person_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    db.delete(member)
    db.commit()
