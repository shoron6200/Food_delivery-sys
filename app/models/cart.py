"""The cart_items table: what each customer has in their cart right now."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.restaurant import MenuItem


class CartItem(Base):
    __tablename__ = "cart_items"

    # Composite primary key: the pair (user, menu item) is unique, so one
    # customer cannot have the same item on two rows. Quantity counts repeats.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    menu_item_id: Mapped[int] = mapped_column(
        ForeignKey("menu_items.id"), primary_key=True
    )
    quantity: Mapped[int]

    # No price column on purpose: the price is always read from the menu.
    menu_item: Mapped[MenuItem] = relationship()
