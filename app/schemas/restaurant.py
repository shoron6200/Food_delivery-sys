"""Shapes of the data that goes in and out of the restaurant and menu endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RestaurantCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100, examples=["Kacchi Ghor"])
    description: str | None = Field(default=None, max_length=500)
    address: str = Field(
        min_length=5, max_length=255, examples=["House 12, Road 5, Dhanmondi, Dhaka"]
    )
    avg_prep_minutes: int = Field(default=20, ge=5, le=120)


class RestaurantUpdate(BaseModel):
    """For PATCH: send only the fields you want to change."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    address: str | None = Field(default=None, min_length=5, max_length=255)
    avg_prep_minutes: int | None = Field(default=None, ge=5, le=120)
    is_open: bool | None = None


class RestaurantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    name: str
    description: str | None
    address: str
    is_open: bool
    is_approved: bool
    avg_prep_minutes: int
    average_rating: float | None
    review_count: int
    created_at: datetime


class MenuItemCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100, examples=["Kacchi Biryani"])
    description: str | None = Field(default=None, max_length=500)
    # Whole taka. gt=0 means "greater than 0", so free or negative prices fail.
    price: int = Field(gt=0, le=100_000, examples=[320])
    category: str = Field(min_length=2, max_length=50, examples=["Biryani"])
    is_available: bool = True


class MenuItemUpdate(BaseModel):
    """For PATCH: send only the fields you want to change."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: int | None = Field(default=None, gt=0, le=100_000)
    category: str | None = Field(default=None, min_length=2, max_length=50)
    is_available: bool | None = None


class MenuItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    name: str
    description: str | None
    price: int
    category: str
    is_available: bool


class RestaurantApproval(BaseModel):
    is_approved: bool
