"""Late Compensation: if we deliver late, the customer gets wallet credit.

The customer never has to complain. The rule runs by itself at the moment
the rider marks the order as delivered.
"""

from datetime import datetime

from app.services.pricing import PriceBreakdown

# Up to this many minutes late we say sorry but pay nothing.
GRACE_MINUTES = 15
# Later than this is a big delay and pays more.
BIG_DELAY_MINUTES = 30


def minutes_late(promised_at: datetime, delivered_at: datetime) -> int:
    """Whole minutes after the promised time. 0 if on time or early."""
    seconds = (delivered_at - promised_at).total_seconds()
    return max(0, int(seconds // 60))


def calculate_compensation(late: int, price: PriceBreakdown) -> int:
    """Wallet credit (whole taka) owed for a delivery that was `late` minutes late."""
    if late <= GRACE_MINUTES:
        return 0
    if late <= BIG_DELAY_MINUTES:
        return price.delivery_fee
    # Big delay: the delivery fee back, plus 10% of the food price.
    return price.delivery_fee + price.subtotal // 10
