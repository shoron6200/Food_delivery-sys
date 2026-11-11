"""The wallet_transactions table: every taka that entered or left a wallet."""

from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.types import UtcDateTime


class WalletTransaction(Base):
    """One line in a customer's wallet history. Lines are added, never changed.

    There is no "balance" column anywhere: the balance is the sum of the lines.
    """

    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"))
    # Whole taka. Positive = money in (compensation, refund). Negative = spent.
    amount: Mapped[int]
    reason: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, server_default=func.now())
