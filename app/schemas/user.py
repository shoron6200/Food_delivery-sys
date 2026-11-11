"""Shapes of the data that goes in and out of the auth endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.user import UserRole


class UserCreate(BaseModel):
    """What a client sends to register."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100, examples=["Rahim Uddin"])
    # Bangladeshi mobile number: 11 digits, starts with 013-019.
    phone: str = Field(pattern=r"^01[3-9]\d{8}$", examples=["01712345678"])
    password: str = Field(min_length=8, examples=["my-secret-pass"])
    # "admin" is missing on purpose: nobody may make themselves an admin.
    role: Literal["customer", "vendor", "rider"] = "customer"

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        # bcrypt can hash at most 72 bytes (a Bangla letter takes 3 bytes).
        if len(value.encode()) > 72:
            raise ValueError("Password is too long (max 72 bytes)")
        return value


class UserOut(BaseModel):
    """What we send back about a user. Note: no password_hash here."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    role: UserRole
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
