"""Reading a customer's cart from the database."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cart import CartItem


def get_cart_items(db: Session, user_id: int) -> list[CartItem]:
    query = (
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.menu_item_id)
    )
    return list(db.scalars(query))
