"""Order rules: who may move an order from one status to the next."""

from datetime import datetime, timedelta

from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole

# Minutes we allow for the ride from restaurant to customer.
DELIVERY_MINUTES = 20

# The whole life of an order. (from, to): the only role allowed to do it.
# Any move that is not in this table is impossible.
TRANSITIONS: dict[tuple[OrderStatus, OrderStatus], UserRole] = {
    (OrderStatus.placed, OrderStatus.accepted): UserRole.vendor,
    (OrderStatus.placed, OrderStatus.rejected): UserRole.vendor,
    (OrderStatus.placed, OrderStatus.cancelled): UserRole.customer,
    (OrderStatus.accepted, OrderStatus.ready): UserRole.vendor,
    (OrderStatus.ready, OrderStatus.picked_up): UserRole.rider,
    (OrderStatus.picked_up, OrderStatus.delivered): UserRole.rider,
}


def role_allowed_to_change(current: OrderStatus, new: OrderStatus) -> UserRole | None:
    """Which role may make this move? None means nobody: the move is invalid."""
    return TRANSITIONS.get((current, new))


def promised_time(now: datetime, prep_minutes: int) -> datetime:
    """The arrival time we promise the customer: cooking time + riding time."""
    return now + timedelta(minutes=prep_minutes + DELIVERY_MINUTES)


def is_participant(order: Order, user: User) -> bool:
    """May this user see this order?"""
    if user.role == UserRole.admin:
        return True
    if user.role == UserRole.customer:
        return order.customer_id == user.id
    if user.role == UserRole.vendor:
        return order.restaurant.owner_id == user.id
    return order.rider_id == user.id
