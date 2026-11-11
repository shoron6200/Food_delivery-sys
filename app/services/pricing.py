"""Honest Price: the one place where the money a customer pays is worked out.

The cart shows this breakdown and the order (Step 6) will charge it, both by
calling calculate_price. So what the customer sees is always what they pay.
"""

from dataclasses import dataclass

# All amounts are whole taka.
DELIVERY_FEE = 40
PLATFORM_FEE = 5


@dataclass(frozen=True)
class PriceBreakdown:
    subtotal: int  # food only, at the restaurant's own menu prices
    delivery_fee: int
    platform_fee: int
    total: int


def calculate_price(lines: list[tuple[int, int]]) -> PriceBreakdown:
    """Work out the bill for a list of (unit_price, quantity) pairs."""
    subtotal = sum(unit_price * quantity for unit_price, quantity in lines)
    if subtotal == 0:
        # Nothing to deliver, so nothing to charge.
        return PriceBreakdown(subtotal=0, delivery_fee=0, platform_fee=0, total=0)
    return PriceBreakdown(
        subtotal=subtotal,
        delivery_fee=DELIVERY_FEE,
        platform_fee=PLATFORM_FEE,
        total=subtotal + DELIVERY_FEE + PLATFORM_FEE,
    )
