"""The restaurants and menu_items tables."""

from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.types import UtcDateTime


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Foreign key: this number must be the id of a real row in "users".
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(String(500))
    address: Mapped[str] = mapped_column(String(255))
    is_open: Mapped[bool] = mapped_column(default=True)
    # New restaurants are hidden from customers until an admin approves them.
    is_approved: Mapped[bool] = mapped_column(default=False)
    avg_prep_minutes: Mapped[int] = mapped_column(default=20)
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, server_default=func.now()
    )

    # Not a column. Lets us write restaurant.menu_items to get the items.
    menu_items: Mapped[list["MenuItem"]] = relationship(
        back_populates="restaurant", order_by="MenuItem.id"
    )


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(500))
    # Whole taka as an integer. Money is never stored as float (0.1 + 0.2 != 0.3).
    price: Mapped[int]
    category: Mapped[str] = mapped_column(String(50))
    is_available: Mapped[bool] = mapped_column(default=True)

    restaurant: Mapped[Restaurant] = relationship(back_populates="menu_items")
