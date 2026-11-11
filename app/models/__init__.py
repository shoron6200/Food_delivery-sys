"""Import every model here, so all tables are known whenever any model is used."""

from app.models.restaurant import MenuItem, Restaurant
from app.models.user import User, UserRole

__all__ = ["MenuItem", "Restaurant", "User", "UserRole"]
