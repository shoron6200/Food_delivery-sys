"""Reading a customer's wallet."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.wallet import WalletTransaction


def get_balance(db: Session, user_id: int) -> int:
    """The wallet balance in whole taka: the sum of every transaction."""
    total = db.scalar(
        select(func.coalesce(func.sum(WalletTransaction.amount), 0)).where(
            WalletTransaction.user_id == user_id
        )
    )
    return int(total)
