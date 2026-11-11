"""Admin endpoints: decide which restaurants customers may order from."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import Admin, DbSession
from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantApproval, RestaurantOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/restaurants", response_model=list[RestaurantOut])
def list_all_restaurants(admin: Admin, db: DbSession, approved: bool | None = None):
    """Every restaurant. Use ?approved=false to see the ones waiting for a decision."""
    query = select(Restaurant).order_by(Restaurant.id)
    if approved is not None:
        query = query.where(Restaurant.is_approved == approved)
    return db.scalars(query).all()


@router.patch("/restaurants/{restaurant_id}", response_model=RestaurantOut)
def set_restaurant_approval(
    restaurant_id: int, data: RestaurantApproval, admin: Admin, db: DbSession
):
    """Approve a restaurant, or (with false) take it back off the platform."""
    restaurant = db.get(Restaurant, restaurant_id)
    if restaurant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Restaurant not found")
    restaurant.is_approved = data.is_approved
    db.commit()
    return restaurant
