from datetime import datetime
from typing import Optional
import enum
from sqlalchemy import String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TeamRole(str, enum.Enum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"


class Team(Base):
    __tablename__ = "team"

    team_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("person.person_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    creator: Mapped["Person"] = relationship("Person")
    members: Mapped[list["TeamMember"]] = relationship(back_populates="team", cascade="all, delete-orphan")
    projects: Mapped[list["ProjectTeam"]] = relationship(back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_member"

    team_id: Mapped[int] = mapped_column(ForeignKey("team.team_id", ondelete="CASCADE"), primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("person.person_id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[TeamRole] = mapped_column(Enum(TeamRole), default=TeamRole.MEMBER)

    # Relationships
    team: Mapped["Team"] = relationship(back_populates="members")
    person: Mapped["Person"] = relationship(back_populates="team_memberships")
