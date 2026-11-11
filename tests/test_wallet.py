from datetime import datetime, timedelta, timezone

from app.db.database import SessionLocal
from app.models import Order, User, WalletTransaction
from app.services.pricing import DELIVERY_FEE
from tests.conftest import API, deliver, make_user, place_order, put_item, set_status


def wallet(client, headers):
    return client.get(f"{API}/wallet", headers=headers).json()


def make_late(order_id, minutes):
    """Move the promised time into the past, as if the clock had run on."""
    with SessionLocal() as db:
        order = db.get(Order, order_id)
        order.promised_at = datetime.now(timezone.utc) - timedelta(minutes=minutes, seconds=5)
        db.commit()


def give_credit(amount, phone="01733333333"):
    """Put credit straight into a customer's wallet."""
    with SessionLocal() as db:
        user = db.query(User).filter_by(phone=phone).one()
        db.add(WalletTransaction(user_id=user.id, amount=amount, reason="Test credit"))
        db.commit()


# ---------- Late Compensation ----------


def test_new_wallet_is_empty(client, customer):
    assert wallet(client, customer) == {"balance": 0, "transactions": []}


def test_on_time_delivery_pays_nothing(client, customer, delivered_order):
    order = client.get(f"{API}/orders/{delivered_order['id']}", headers=customer).json()
    assert (order["late_minutes"], order["compensation"]) == (0, 0)
    assert wallet(client, customer)["balance"] == 0


def test_undelivered_order_has_no_lateness_yet(order):
    assert order["late_minutes"] is None
    assert order["compensation"] == 0


def test_late_delivery_credits_the_delivery_fee_automatically(client, customer, vendor, rider, order):
    make_late(order["id"], minutes=20)
    deliver(client, vendor, rider, order["id"])

    delivered = client.get(f"{API}/orders/{order['id']}", headers=customer).json()
    assert delivered["late_minutes"] == 20
    assert delivered["compensation"] == DELIVERY_FEE

    mine = wallet(client, customer)
    assert mine["balance"] == DELIVERY_FEE
    assert len(mine["transactions"]) == 1
    assert mine["transactions"][0]["amount"] == DELIVERY_FEE
    assert mine["transactions"][0]["order_id"] == order["id"]
    assert "20 minutes late" in mine["transactions"][0]["reason"]


def test_very_late_delivery_also_credits_ten_percent_of_food(client, customer, vendor, rider, order):
    make_late(order["id"], minutes=45)
    deliver(client, vendor, rider, order["id"])

    expected = DELIVERY_FEE + order["price"]["subtotal"] // 10
    assert wallet(client, customer)["balance"] == expected


# ---------- Spending credit ----------


def test_wallet_credit_reduces_the_cash_to_pay(client, customer, menu):
    give_credit(100)
    put_item(client, customer, menu["biryani"])

    order = place_order(client, customer, use_wallet=True).json()
    assert order["wallet_used"] == 100
    assert order["amount_due"] == order["price"]["total"] - 100
    assert wallet(client, customer)["balance"] == 0
    assert wallet(client, customer)["transactions"][0]["amount"] == -100


def test_wallet_is_not_touched_unless_asked(client, customer, menu):
    give_credit(100)
    put_item(client, customer, menu["biryani"])

    order = place_order(client, customer).json()
    assert order["wallet_used"] == 0
    assert order["amount_due"] == order["price"]["total"]
    assert wallet(client, customer)["balance"] == 100


def test_wallet_never_pays_more_than_the_bill(client, customer, menu):
    give_credit(5000)
    put_item(client, customer, menu["borhani"])

    order = place_order(client, customer, use_wallet=True).json()
    assert order["wallet_used"] == order["price"]["total"]
    assert order["amount_due"] == 0
    assert wallet(client, customer)["balance"] == 5000 - order["price"]["total"]


def test_use_wallet_with_empty_wallet_is_fine(client, customer, menu):
    put_item(client, customer, menu["borhani"])

    order = place_order(client, customer, use_wallet=True).json()
    assert order["wallet_used"] == 0
    assert wallet(client, customer)["transactions"] == []


def test_cancelling_gives_spent_credit_back(client, customer, menu):
    give_credit(100)
    put_item(client, customer, menu["biryani"])
    order = place_order(client, customer, use_wallet=True).json()

    set_status(client, customer, order["id"], "cancelled")
    mine = wallet(client, customer)
    assert mine["balance"] == 100
    assert [t["amount"] for t in mine["transactions"]] == [100, -100, 100]


def test_rejection_gives_spent_credit_back(client, customer, vendor, menu):
    give_credit(100)
    put_item(client, customer, menu["biryani"])
    order = place_order(client, customer, use_wallet=True).json()

    set_status(client, vendor, order["id"], "rejected")
    assert wallet(client, customer)["balance"] == 100


def test_earned_credit_can_pay_for_the_next_order(client, customer, vendor, rider, order, menu):
    make_late(order["id"], minutes=20)
    deliver(client, vendor, rider, order["id"])

    put_item(client, customer, menu["borhani"])
    second = place_order(client, customer, use_wallet=True).json()
    assert second["wallet_used"] == DELIVERY_FEE
    assert wallet(client, customer)["balance"] == 0


# ---------- Who can see what ----------


def test_wallets_are_private(client, customer, vendor, rider, order):
    stranger = make_user(client, "01744444444", "customer")
    make_late(order["id"], minutes=20)
    deliver(client, vendor, rider, order["id"])

    assert wallet(client, stranger) == {"balance": 0, "transactions": []}


def test_only_customers_have_a_wallet(client, vendor, rider):
    assert client.get(f"{API}/wallet", headers=vendor).status_code == 403
    assert client.get(f"{API}/wallet", headers=rider).status_code == 403
    assert client.get(f"{API}/wallet").status_code == 401
