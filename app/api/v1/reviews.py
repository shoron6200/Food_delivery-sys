"""Review endpoints. Only someone who really received the food can review it."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.api.deps import Customer, DbSession
from app.models.order import Order, OrderStatus
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewOut

router = APIRouter(tags=["reviews"])


@router.post(
    "/orders/{order_id}/review",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
def review_order(order_id: int, data: ReviewCreate, customer: Customer, db: DbSession):
    order = db.get(Order, order_id)
    if order is None or order.customer_id != customer.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    if order.status != OrderStatus.delivered:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "You can review an order after it is delivered"
        )

    review = Review(
        order_id=order.id,
        customer_id=customer.id,
        restaurant_id=order.restaurant_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    # Keep the restaurant's running totals in step with its reviews. Written as
    # "column = column + n" so the database does the adding: two reviews saved
    # at the same moment are both counted.
    db.execute(
        update(Restaurant)
        .where(Restaurant.id == order.restaurant_id)
        .values(
            rating_sum=Restaurant.rating_sum + data.rating,
            review_count=Restaurant.review_count + 1,
        )
    )
    try:
        # One transaction: the review and the new totals are saved together.
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "You already reviewed this order"
        )
    return review


@router.get("/restaurants/{restaurant_id}/reviews", response_model=list[ReviewOut])
def list_reviews(
    restaurant_id: int,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """A restaurant's reviews, newest first. Anyone can read them."""
    if db.get(Restaurant, restaurant_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Restaurant not found")
    query = (
        select(Review)
        .where(Review.restaurant_id == restaurant_id)
        .order_by(Review.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(query).all()
