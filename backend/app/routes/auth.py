from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.models import Person
from app.schemas.auth import UserRegister, UserLogin, Token
from app.schemas.person import PersonResponse
from app.services.auth import (
    get_password_hash,
    create_access_token,
    authenticate_user,
    get_current_user,
)
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/register", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(Person).filter(Person.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    person = Person(
        name=user_data.name,
        email=user_data.email,
        nickname=user_data.nickname,
        password_hash=get_password_hash(user_data.password),
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": str(user.person_id)},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return Token(access_token=access_token)


@router.get("/me", response_model=PersonResponse)
def get_me(current_user: Person = Depends(get_current_user)):
    return current_user


@router.get("/people", response_model=list[PersonResponse])
def list_people(
    search: str = "",
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    """List all users, optionally filtered by email/name search."""
    query = db.query(Person)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Person.email.ilike(search_term)) | (Person.name.ilike(search_term))
        )
    return query.limit(50).all()


@router.get("/people/{person_id}", response_model=PersonResponse)
def get_person(
    person_id: int,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user),
):
    """Get a specific user by ID."""
    person = db.query(Person).filter(Person.person_id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person
