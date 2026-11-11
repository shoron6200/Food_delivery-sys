"""Shape of the data that comes out of the recommendation endpoints."""

from pydantic import BaseModel, ConfigDict


class SuggestedRestaurantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    average_rating: float | None


class SuggestedItemOut(BaseModel):
    """A menu item we suggest, with everything needed to show and order it."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    price: int
    restaurant: SuggestedRestaurantOut


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item: SuggestedItemOut
    score: float
    reason: str
