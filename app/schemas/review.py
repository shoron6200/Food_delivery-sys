"""Shapes of the data that goes in and out of the review endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    rating: int = Field(ge=1, le=5, examples=[5])
    comment: str | None = Field(default=None, max_length=500, examples=["Khub moja!"])


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rating: int
    comment: str | None
    customer_name: str
    created_at: datetime
