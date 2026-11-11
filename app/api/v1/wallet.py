"""Wallet endpoint: a customer's credit and where it came from."""

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import Customer, DbSession
from app.models.wallet import WalletTransaction
from app.schemas.wallet import WalletOut
from app.services.wallet import get_balance

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("", response_model=WalletOut)
def read_wallet(customer: Customer, db: DbSession):
    """Balance plus the 50 most recent transactions, newest first."""
    query = (
        select(WalletTransaction)
        .where(WalletTransaction.user_id == customer.id)
        .order_by(WalletTransaction.id.desc())
        .limit(50)
    )
    return WalletOut(
        balance=get_balance(db, customer.id),
        transactions=db.scalars(query).all(),
    )
