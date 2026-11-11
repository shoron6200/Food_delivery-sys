"""Shapes of the data that goes in and out of the assistant endpoint."""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recommendation import SuggestedItemOut


class AssistantRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(
        min_length=2,
        max_length=500,
        examples=["500 takar moddhe 2 jon er jonno jhal kichu"],
    )


class AssistantSuggestionOut(BaseModel):
    item: SuggestedItemOut
    quantity: int
    line_total: int


class AssistantOut(BaseModel):
    reply: str
    suggestions: list[AssistantSuggestionOut]
    # Food only, in whole taka. Fees are added in the cart, as always.
    food_total: int
