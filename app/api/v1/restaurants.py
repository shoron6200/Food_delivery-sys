"""Restaurant and menu endpoints.

Anyone can read. Only a vendor can create a restaurant, and only its owner
can change it or its menu.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import DbSession, require_role
from app.models.restaurant import MenuItem, Restaurant
from app.models.user import User, UserRole
from app.schemas.restaurant import (
    MenuItemCreate,
    MenuItemOut,
    MenuItemUpdate,
    RestaurantCreate,
    RestaurantOut,
    RestaurantUpdate,
)

router = APIRouter()

Vendor = Annotated[User, Depends(require_role(UserRole.vendor))]


def get_restaurant(restaurant_id: int, db: DbSession) -> Restaurant:
    """Load the restaurant named in the URL, or answer 404."""
    restaurant = db.get(Restaurant, restaurant_id)
    if restaurant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Restaurant not found")
    return restaurant


AnyRestaurant = Annotated[Restaurant, Depends(get_restaurant)]


def check_owner(restaurant: Restaurant, vendor: User) -> None:
    if restaurant.owner_id != vendor.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "This is not your restaurant"
        )


def get_own_restaurant(vendor: Vendor, restaurant: AnyRestaurant) -> Restaurant:
    """Like get_restaurant, but the logged-in vendor must be the owner."""
    check_owner(restaurant, vendor)
    return restaurant


OwnRestaurant = Annotated[Restaurant, Depends(get_own_restaurant)]


# ---------- Restaurants ----------


@router.get("/restaurants", response_model=list[RestaurantOut], tags=["restaurants"])
def list_restaurants(
    db: DbSession,
    search: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    query = select(Restaurant)
    if search:
        # autoescape: a "%" typed by the user is searched as a plain character.
        query = query.where(Restaurant.name.icontains(search, autoescape=True))
    query = query.order_by(Restaurant.id).limit(limit).offset(offset)
    return db.scalars(query).all()


@router.post(
    "/restaurants",
    response_model=RestaurantOut,
    status_code=status.HTTP_201_CREATED,
    tags=["restaurants"],
)
def create_restaurant(data: RestaurantCreate, vendor: Vendor, db: DbSession):
    # owner_id comes from the token, never from the request body.
    restaurant = Restaurant(**data.model_dump(), owner_id=vendor.id)
    db.add(restaurant)
    db.commit()
    return restaurant


@router.get(
    "/restaurants/{restaurant_id}", response_model=RestaurantOut, tags=["restaurants"]
)
def read_restaurant(restaurant: AnyRestaurant):
    return restaurant


@router.patch(
    "/restaurants/{restaurant_id}", response_model=RestaurantOut, tags=["restaurants"]
)
def update_restaurant(data: RestaurantUpdate, restaurant: OwnRestaurant, db: DbSession):
    # exclude_none: fields the client did not send (or sent as null) stay as they are.
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(restaurant, field, value)
    db.commit()
    return restaurant


# ---------- Menu ----------


@router.get(
    "/restaurants/{restaurant_id}/menu", response_model=list[MenuItemOut], tags=["menu"]
)
def read_menu(restaurant: AnyRestaurant):
    return restaurant.menu_items


@router.post(
    "/restaurants/{restaurant_id}/menu-items",
    response_model=MenuItemOut,
    status_code=status.HTTP_201_CREATED,
    tags=["menu"],
)
def create_menu_item(data: MenuItemCreate, restaurant: OwnRestaurant, db: DbSession):
    item = MenuItem(**data.model_dump(), restaurant_id=restaurant.id)
    db.add(item)
    db.commit()
    return item


@router.patch("/menu-items/{item_id}", response_model=MenuItemOut, tags=["menu"])
def update_menu_item(item_id: int, data: MenuItemUpdate, vendor: Vendor, db: DbSession):
    item = db.get(MenuItem, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Menu item not found")
    check_owner(item.restaurant, vendor)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    db.commit()
    return item
