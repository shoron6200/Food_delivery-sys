"""Shapes of the data that goes in and out of the order endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.order import OrderStatus
from app.schemas.cart import PriceOut


class OrderCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    delivery_address: str = Field(
        min_length=5, max_length=255, examples=["Flat 4B, House 7, Road 2, Mirpur 10"]
    )


class OrderStatusChange(BaseModel):
    status: OrderStatus


class OrderRestaurantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    menu_item_id: int
    name: str
    unit_price: int
    quantity: int

    @computed_field
    @property
    def line_total(self) -> int:
        return self.unit_price * self.quantity


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatus
    customer_id: int
    rider_id: int | None
    restaurant: OrderRestaurantOut
    delivery_address: str
    items: list[OrderItemOut]
    price: PriceOut
    promised_at: datetime
    delivered_at: datetime | None
    created_at: datetime
