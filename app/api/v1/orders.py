"""Order endpoints: place an order, see your orders, move an order forward."""

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, Customer, DbSession
from app.models.order import Order, OrderItem, OrderStatus
from app.models.restaurant import Restaurant
from app.models.user import UserRole
from app.schemas.order import OrderCreate, OrderOut, OrderStatusChange
from app.services.cart import get_cart_items
from app.services.orders import is_participant, promised_time, role_allowed_to_change
from app.services.pricing import calculate_price

router = APIRouter(prefix="/orders", tags=["orders"])


def get_my_order(order_id: int, user: CurrentUser, db: DbSession) -> Order:
    """Load an order the logged-in user is part of, or answer 404."""
    order = db.get(Order, order_id)
    if order is None or not is_participant(order, user):
        # Same answer for "does not exist" and "not yours", so nobody can
        # find out which order numbers are real.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


MyOrder = Annotated[Order, Depends(get_my_order)]


def save_status(db: Session, order: Order, new_status: OrderStatus, **changes) -> None:
    """Move the order to new_status, but only if nobody else moved it first."""
    result = db.execute(
        update(Order)
        .where(Order.id == order.id, Order.status == order.status)
        .values(status=new_status, **changes)
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This order was just changed by someone else. Load it again.",
        )
    db.commit()
    db.refresh(order)


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def place_order(data: OrderCreate, customer: Customer, db: DbSession):
    """Turn the cart into an order. The price is the one the cart showed."""
    cart_items = get_cart_items(db, customer.id)
    if not cart_items:
        raise HTTPException(status.HTTP_409_CONFLICT, "Your cart is empty")

    restaurant = cart_items[0].menu_item.restaurant
    if not restaurant.is_open:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "This restaurant is closed right now"
        )
    unavailable = [
        cart_item.menu_item.name
        for cart_item in cart_items
        if not cart_item.menu_item.is_available
    ]
    if unavailable:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Not available right now: {', '.join(unavailable)}. Remove them first.",
        )

    price = calculate_price(
        [(cart_item.menu_item.price, cart_item.quantity) for cart_item in cart_items]
    )
    order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        delivery_address=data.delivery_address,
        promised_at=promised_time(
            datetime.now(timezone.utc), restaurant.avg_prep_minutes
        ),
        **asdict(price),
    )
    order.items = [
        OrderItem(
            menu_item_id=cart_item.menu_item_id,
            name=cart_item.menu_item.name,
            unit_price=cart_item.menu_item.price,
            quantity=cart_item.quantity,
        )
        for cart_item in cart_items
    ]
    db.add(order)
    for cart_item in cart_items:
        db.delete(cart_item)
    # One commit = one transaction: the order is saved AND the cart is emptied,
    # or (if anything fails) neither happens.
    db.commit()
    return order


@router.get("", response_model=list[OrderOut])
def list_my_orders(
    user: CurrentUser,
    db: DbSession,
    status_filter: Annotated[OrderStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Your orders, newest first. What "your" means depends on your role."""
    query = select(Order)
    if user.role == UserRole.customer:
        query = query.where(Order.customer_id == user.id)
    elif user.role == UserRole.vendor:
        query = query.join(Restaurant).where(Restaurant.owner_id == user.id)
    elif user.role == UserRole.rider:
        query = query.where(Order.rider_id == user.id)
    # An admin gets no filter: they see every order.
    if status_filter is not None:
        query = query.where(Order.status == status_filter)
    query = query.order_by(Order.id.desc()).limit(limit).offset(offset)
    return db.scalars(query).all()


@router.get("/{order_id}", response_model=OrderOut)
def read_order(order: MyOrder):
    return order


@router.patch("/{order_id}/status", response_model=OrderOut)
def change_status(
    data: OrderStatusChange, order: MyOrder, user: CurrentUser, db: DbSession
):
    allowed_role = role_allowed_to_change(order.status, data.status)
    if allowed_role is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"An order that is '{order.status.value}' cannot become '{data.status.value}'",
        )
    if user.role != allowed_role:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, f"Only the {allowed_role.value} can do this"
        )

    changes = {}
    if data.status == OrderStatus.delivered:
        changes["delivered_at"] = datetime.now(timezone.utc)
    save_status(db, order, data.status, **changes)
    return order
