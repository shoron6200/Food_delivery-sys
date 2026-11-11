"""Shapes of the data that comes out of the wallet endpoint."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WalletTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int | None
    amount: int
    reason: str
    created_at: datetime


class WalletOut(BaseModel):
    balance: int
    transactions: list[WalletTransactionOut]
