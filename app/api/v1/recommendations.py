"""Recommendation endpoint: "For you" menu items for the logged-in customer."""

from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import Customer, DbSession
from app.models.order import Order, OrderItem, OrderStatus
from app.models.restaurant import MenuItem
from app.schemas.recommendation import RecommendationOut
from app.services.catalog import get_orderable_items
from app.services.recommend import PastItem, recommend

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=list[RecommendationOut])
def read_recommendations(
    customer: Customer,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
):
    # What this customer has really eaten: lines of their delivered orders.
    rows = db.execute(
        select(OrderItem.menu_item_id, MenuItem.category, OrderItem.quantity)
        .join(Order, OrderItem.order_id == Order.id)
        .join(MenuItem, OrderItem.menu_item_id == MenuItem.id)
        .where(Order.customer_id == customer.id, Order.status == OrderStatus.delivered)
    )
    history = [PastItem(*row) for row in rows]
    return recommend(get_orderable_items(db), history, limit)
