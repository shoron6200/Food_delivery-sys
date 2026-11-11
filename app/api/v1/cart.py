"""Cart endpoints. Every answer includes the full Honest Price breakdown."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import DbSession, require_role
from app.models.cart import CartItem
from app.models.restaurant import MenuItem
from app.models.user import User, UserRole
from app.schemas.cart import CartItemSet, CartLineOut, CartOut
from app.services.pricing import calculate_price

router = APIRouter(prefix="/cart", tags=["cart"])

Customer = Annotated[User, Depends(require_role(UserRole.customer))]


def get_cart_items(db: Session, user_id: int) -> list[CartItem]:
    query = (
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.menu_item_id)
    )
    return list(db.scalars(query))


def build_cart(db: Session, user_id: int) -> CartOut:
    """Read the cart and price it from the menu as it is right now."""
    cart_items = get_cart_items(db, user_id)
    lines = [
        CartLineOut(
            menu_item_id=cart_item.menu_item_id,
            name=cart_item.menu_item.name,
            unit_price=cart_item.menu_item.price,
            quantity=cart_item.quantity,
            line_total=cart_item.menu_item.price * cart_item.quantity,
            is_available=cart_item.menu_item.is_available,
        )
        for cart_item in cart_items
    ]
    return CartOut(
        restaurant=cart_items[0].menu_item.restaurant if cart_items else None,
        items=lines,
        price=calculate_price([(line.unit_price, line.quantity) for line in lines]),
    )


@router.get("", response_model=CartOut)
def read_cart(customer: Customer, db: DbSession):
    return build_cart(db, customer.id)


@router.put("/items/{menu_item_id}", response_model=CartOut)
def set_cart_item(
    menu_item_id: int, data: CartItemSet, customer: Customer, db: DbSession
):
    """Put an item in the cart with this quantity (replaces the old quantity)."""
    menu_item = db.get(MenuItem, menu_item_id)
    if menu_item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Menu item not found")
    if not menu_item.is_available:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "This item is not available right now"
        )
    if not menu_item.restaurant.is_open:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "This restaurant is closed right now"
        )

    cart_items = get_cart_items(db, customer.id)
    if any(
        cart_item.menu_item.restaurant_id != menu_item.restaurant_id
        for cart_item in cart_items
    ):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Your cart has items from another restaurant. Clear the cart first.",
        )

    cart_item = db.get(CartItem, (customer.id, menu_item_id))
    if cart_item is None:
        db.add(
            CartItem(
                user_id=customer.id, menu_item_id=menu_item_id, quantity=data.quantity
            )
        )
    else:
        cart_item.quantity = data.quantity
    db.commit()
    return build_cart(db, customer.id)


@router.delete("/items/{menu_item_id}", response_model=CartOut)
def remove_cart_item(menu_item_id: int, customer: Customer, db: DbSession):
    cart_item = db.get(CartItem, (customer.id, menu_item_id))
    if cart_item is not None:
        db.delete(cart_item)
        db.commit()
    return build_cart(db, customer.id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(customer: Customer, db: DbSession) -> None:
    db.execute(delete(CartItem).where(CartItem.user_id == customer.id))
    db.commit()
