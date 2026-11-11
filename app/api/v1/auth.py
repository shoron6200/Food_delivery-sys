"""Register, login, and "who am I" endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.user import Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: DbSession) -> User:
    user = User(
        name=data.name,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=UserRole(data.role),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # The phone column is unique, so the database rejects a second account.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This phone number is already registered",
        )
    return user


@router.post("/login", response_model=Token)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession
) -> Token:
    """Log in with phone (sent in the "username" field) and password."""
    user = db.scalar(select(User).where(User.phone == form.username))
    if (
        user is None
        or not user.is_active
        or not verify_password(form.password, user.password_hash)
    ):
        # Same message for every failure, so nobody can test which phones exist.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong phone number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(current_user: CurrentUser) -> User:
    return current_user
