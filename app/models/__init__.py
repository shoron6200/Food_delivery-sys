"""Import every model here, so all tables are known whenever any model is used."""

from app.models.cart import CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.models.restaurant import MenuItem, Restaurant
from app.models.review import Review
from app.models.user import User, UserRole

__all__ = [
    "CartItem",
    "MenuItem",
    "Order",
    "OrderItem",
    "OrderStatus",
    "Restaurant",
    "Review",
    "User",
    "UserRole",
]
