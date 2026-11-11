"""What a customer can order right now."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.restaurant import MenuItem, Restaurant


def get_orderable_items(db: Session, limit: int = 300) -> list[MenuItem]:
    """Available items from restaurants that are approved and open."""
    query = (
        select(MenuItem)
        .join(Restaurant)
        .where(MenuItem.is_available, Restaurant.is_approved, Restaurant.is_open)
        .order_by(MenuItem.id)
        .limit(limit)
    )
    return list(db.scalars(query))
