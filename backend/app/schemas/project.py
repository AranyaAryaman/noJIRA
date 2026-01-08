from pydantic import BaseModel
from datetime import datetime
from app.models.project import ProjectRole
from app.schemas.person import PersonBrief
from app.schemas.team import TeamResponse


class ProjectBase(BaseModel):
    name: str
    description: str | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_archived: bool | None = None


class ProjectMemberAdd(BaseModel):
    person_id: int
    role: ProjectRole = ProjectRole.MEMBER


class ProjectMemberUpdate(BaseModel):
    role: ProjectRole


class ProjectTeamAdd(BaseModel):
    team_id: int


class ProjectMemberResponse(BaseModel):
    person: PersonBrief
    role: ProjectRole

    class Config:
        from_attributes = True


class ProjectTeamResponse(BaseModel):
    team: TeamResponse

    class Config:
        from_attributes = True


class ProjectResponse(ProjectBase):
    project_id: int
    created_by: int
    created_at: datetime
    is_archived: bool

    class Config:
        from_attributes = True


class ProjectWithDetails(ProjectResponse):
    members: list[ProjectMemberResponse] = []
    teams: list[ProjectTeamResponse] = []
