from pydantic import BaseModel
from datetime import datetime
from app.models.team import TeamRole
from app.schemas.person import PersonBrief


class TeamBase(BaseModel):
    name: str
    description: str | None = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class TeamMemberAdd(BaseModel):
    person_id: int
    role: TeamRole = TeamRole.MEMBER


class TeamMemberUpdate(BaseModel):
    role: TeamRole


class TeamMemberResponse(BaseModel):
    person: PersonBrief
    role: TeamRole

    class Config:
        from_attributes = True


class TeamResponse(TeamBase):
    team_id: int
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class TeamWithMembers(TeamResponse):
    members: list[TeamMemberResponse] = []
