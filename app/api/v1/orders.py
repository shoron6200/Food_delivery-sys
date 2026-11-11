"""Order endpoints: place an order, see your orders, move an order forward."""

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, Customer, DbSession, Rider, check_taking_orders
from app.models.order import Order, OrderItem, OrderStatus
from app.models.restaurant import Restaurant
from app.models.user import User, UserRole
from app.models.wallet import WalletTransaction
from app.schemas.order import OrderCreate, OrderOut, OrderStatusChange
from app.services.cart import get_cart_items
from app.services.compensation import calculate_compensation, minutes_late
from app.services.orders import is_participant, promised_time, role_allowed_to_change
from app.services.pricing import calculate_price
from app.services.wallet import get_balance

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
    check_taking_orders(restaurant)
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

    if data.use_wallet:
        # Lock this customer's row until commit, so two orders placed at the
        # same moment cannot both spend the same credit. (PostgreSQL does the
        # locking; SQLite skips it because it lets only one writer in anyway.)
        db.execute(select(User.id).where(User.id == customer.id).with_for_update())
        db.flush()  # sends the order to the database, so it now has an id
        order.wallet_used = min(get_balance(db, customer.id), price.total)
        if order.wallet_used > 0:
            db.add(
                WalletTransaction(
                    user_id=customer.id,
                    order_id=order.id,
                    amount=-order.wallet_used,
                    reason=f"Paid for order #{order.id}",
                )
            )

    # One commit = one transaction: the order is saved, the cart is emptied and
    # the wallet is charged, or (if anything fails) none of it happens.
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


# Statuses in which an order is cooking or packed and may still need a rider.
WAITING_FOR_RIDER = (OrderStatus.accepted, OrderStatus.ready)


# Must stay above "/{order_id}": routes are tried top to bottom, and
# "available" would otherwise be read as an order id.
@router.get("/available", response_model=list[OrderOut])
def list_available_orders(rider: Rider, db: DbSession):
    """Orders that still need a rider, oldest first."""
    query = (
        select(Order)
        .where(Order.status.in_(WAITING_FOR_RIDER), Order.rider_id.is_(None))
        .order_by(Order.id)
        .limit(50)
    )
    return db.scalars(query).all()


@router.get("/{order_id}", response_model=OrderOut)
def read_order(order: MyOrder):
    return order


@router.post("/{order_id}/claim", response_model=OrderOut)
def claim_order(order_id: int, rider: Rider, db: DbSession):
    """A rider takes a delivery. The first rider to ask gets it."""
    busy = db.scalar(
        select(Order.id).where(
            Order.rider_id == rider.id,
            Order.status.in_((*WAITING_FOR_RIDER, OrderStatus.picked_up)),
        )
    )
    if busy is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Finish your delivery of order {busy} first"
        )

    # "Is it still free?" and "make it mine" in one statement, so two riders
    # asking at the same moment cannot both get the order.
    result = db.execute(
        update(Order)
        .where(
            Order.id == order_id,
            Order.rider_id.is_(None),
            Order.status.in_(WAITING_FOR_RIDER),
        )
        .values(rider_id=rider.id)
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "This order is not available for delivery"
        )
    db.commit()
    return db.get(Order, order_id)


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
        now = datetime.now(timezone.utc)
        late = minutes_late(order.promised_at, now)
        compensation = calculate_compensation(late, order.price)
        changes = {"delivered_at": now, "compensation": compensation}
        if compensation > 0:
            db.add(
                WalletTransaction(
                    user_id=order.customer_id,
                    order_id=order.id,
                    amount=compensation,
                    reason=f"Order #{order.id} arrived {late} minutes late. Sorry!",
                )
            )
    elif data.status in (OrderStatus.cancelled, OrderStatus.rejected):
        if order.wallet_used > 0:
            db.add(
                WalletTransaction(
                    user_id=order.customer_id,
                    order_id=order.id,
                    amount=order.wallet_used,
                    reason=f"Refund for order #{order.id}",
                )
            )
    # The wallet lines above are saved in the same transaction as the status.
    save_status(db, order, data.status, **changes)
    return order
