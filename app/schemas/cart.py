"""Shapes of the data that goes in and out of the cart endpoints."""

from pydantic import BaseModel, ConfigDict, Field


class CartItemSet(BaseModel):
    quantity: int = Field(ge=1, le=20, examples=[2])


class CartRestaurantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_open: bool


class CartLineOut(BaseModel):
    menu_item_id: int
    name: str
    unit_price: int
    quantity: int
    line_total: int
    is_available: bool


class PriceOut(BaseModel):
    """The Honest Price breakdown, in whole taka."""

    model_config = ConfigDict(from_attributes=True)

    subtotal: int
    delivery_fee: int
    platform_fee: int
    total: int


class CartOut(BaseModel):
    restaurant: CartRestaurantOut | None
    items: list[CartLineOut]
    price: PriceOut
