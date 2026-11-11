"""DEMO HELPER: pretend an order's promised time has already passed.

Run from the project folder:  python -m scripts.make_order_late ORDER_ID [MINUTES]

Nobody wants to wait 40 minutes in a presentation to show Late Compensation.
This moves the order's promised time into the past, so that delivering it
right now counts as MINUTES late (default 20). Use it before the rider marks
the order as delivered. Never run this against real customer data.
"""

import sys
from datetime import datetime, timedelta, timezone

from app.db.database import SessionLocal
from app.models import Order


def main() -> int:
    if len(sys.argv) not in (2, 3) or not all(arg.isdigit() for arg in sys.argv[1:]):
        print("Usage: python -m scripts.make_order_late ORDER_ID [MINUTES]")
        return 1
    order_id = int(sys.argv[1])
    minutes = int(sys.argv[2]) if len(sys.argv) == 3 else 20

    with SessionLocal() as db:
        order = db.get(Order, order_id)
        if order is None:
            print(f"There is no order {order_id}.")
            return 1
        if order.delivered_at is not None:
            print(f"Order {order_id} is already delivered.")
            return 1
        order.promised_at = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        db.commit()

    print(f"Order {order_id} now counts as {minutes} minutes late. Deliver it to see the credit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
