from pydantic import BaseModel, EmailStr
from datetime import datetime


class PersonBase(BaseModel):
    name: str
    email: EmailStr
    nickname: str | None = None


class PersonCreate(PersonBase):
    password: str


class PersonUpdate(BaseModel):
    name: str | None = None
    nickname: str | None = None


class PersonResponse(PersonBase):
    person_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PersonBrief(BaseModel):
    person_id: int
    name: str
    email: str
    nickname: str | None = None

    class Config:
        from_attributes = True
