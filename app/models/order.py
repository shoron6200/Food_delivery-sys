"""The orders and order_items tables."""

import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.types import UtcDateTime
from app.models.restaurant import Restaurant
from app.services.compensation import minutes_late
from app.services.pricing import PriceBreakdown


class OrderStatus(str, enum.Enum):
    placed = "placed"  # customer has ordered, restaurant has not answered yet
    accepted = "accepted"  # restaurant is cooking
    ready = "ready"  # food is packed, waiting for the rider
    picked_up = "picked_up"  # rider is on the way
    delivered = "delivered"
    rejected = "rejected"  # restaurant said no
    cancelled = "cancelled"  # customer changed their mind


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), index=True)
    # Empty until a rider takes the delivery.
    rider_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    delivery_address: Mapped[str] = mapped_column(String(255))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.placed, index=True
    )

    # The bill, frozen at the moment of ordering (whole taka).
    subtotal: Mapped[int]
    delivery_fee: Mapped[int]
    platform_fee: Mapped[int]
    total: Mapped[int]
    # Wallet credit the customer chose to spend on this order.
    wallet_used: Mapped[int] = mapped_column(default=0)

    # The time we promised the food would arrive, and when it really did.
    promised_at: Mapped[datetime] = mapped_column(UtcDateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    # Wallet credit we paid the customer because this order arrived late.
    compensation: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, server_default=func.now())

    items: Mapped[list["OrderItem"]] = relationship(order_by="OrderItem.id")
    restaurant: Mapped[Restaurant] = relationship()

    @property
    def price(self) -> PriceBreakdown:
        return PriceBreakdown(
            subtotal=self.subtotal,
            delivery_fee=self.delivery_fee,
            platform_fee=self.platform_fee,
            total=self.total,
        )

    @property
    def amount_due(self) -> int:
        """Cash the rider collects at the door."""
        return self.total - self.wallet_used

    @property
    def late_minutes(self) -> int | None:
        """Minutes after the promised time. None while the order is not delivered."""
        if self.delivered_at is None:
            return None
        return minutes_late(self.promised_at, self.delivered_at)


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"))
    # Snapshot: copied from the menu when the order was placed, so a later
    # menu change cannot rewrite what this customer bought and paid.
    name: Mapped[str] = mapped_column(String(100))
    unit_price: Mapped[int]
    quantity: Mapped[int]
