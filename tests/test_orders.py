from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.api.v1.orders import save_status
from app.db.database import SessionLocal
from app.models.order import Order, OrderStatus
from app.services.orders import DELIVERY_MINUTES
from tests.conftest import API, make_user, place_order, put_item, set_status

# ---------- Placing an order ----------


def test_order_charges_exactly_what_the_cart_showed(client, customer, menu):
    put_item(client, customer, menu["biryani"], quantity=2)
    cart = put_item(client, customer, menu["borhani"], quantity=1).json()

    response = place_order(client, customer)
    assert response.status_code == 201
    order = response.json()

    assert order["price"] == cart["price"]
    assert order["status"] == "placed"
    assert order["rider_id"] is None
    assert order["restaurant"] == {"id": menu["restaurant"], "name": "Kacchi Ghor"}
    assert [(i["name"], i["unit_price"], i["quantity"], i["line_total"]) for i in order["items"]] == [
        ("Kacchi Biryani", 320, 2, 640),
        ("Borhani", 60, 1, 60),
    ]


def test_placing_an_order_empties_the_cart(client, customer, order):
    assert client.get(f"{API}/cart", headers=customer).json()["items"] == []


def test_promised_time_is_prep_plus_delivery_minutes_from_now(client, order):
    promised = datetime.fromisoformat(order["promised_at"])
    expected = datetime.now(timezone.utc) + timedelta(minutes=20 + DELIVERY_MINUTES)
    assert abs((promised - expected).total_seconds()) < 60


def test_cannot_order_with_empty_cart(client, customer):
    assert place_order(client, customer).status_code == 409


def test_cannot_order_if_restaurant_closed_after_adding(client, customer, vendor, menu):
    put_item(client, customer, menu["biryani"])
    client.patch(f"{API}/restaurants/{menu['restaurant']}", json={"is_open": False}, headers=vendor)

    assert place_order(client, customer).status_code == 409
    assert len(client.get(f"{API}/cart", headers=customer).json()["items"]) == 1


def test_cannot_order_an_item_that_became_unavailable(client, customer, vendor, menu):
    put_item(client, customer, menu["biryani"])
    client.patch(f"{API}/menu-items/{menu['biryani']}", json={"is_available": False}, headers=vendor)

    response = place_order(client, customer)
    assert response.status_code == 409
    assert "Kacchi Biryani" in response.json()["detail"]


def test_address_is_required(client, customer, menu):
    put_item(client, customer, menu["biryani"])
    assert place_order(client, customer, address="x").status_code == 422


def test_only_customers_place_orders(client, vendor):
    assert place_order(client, vendor).status_code == 403


def test_old_order_keeps_its_price_and_name_after_menu_changes(client, customer, vendor, order):
    biryani_id = order["items"][0]["menu_item_id"]
    client.patch(
        f"{API}/menu-items/{biryani_id}", json={"price": 999, "name": "New Name"}, headers=vendor
    )

    again = client.get(f"{API}/orders/{order['id']}", headers=customer).json()
    assert again["items"] == order["items"]
    assert again["price"] == order["price"]


# ---------- Seeing orders ----------


def test_customer_sees_own_orders_newest_first(client, customer, menu):
    put_item(client, customer, menu["biryani"])
    first = place_order(client, customer).json()["id"]
    put_item(client, customer, menu["borhani"])
    second = place_order(client, customer).json()["id"]

    orders = client.get(f"{API}/orders", headers=customer).json()
    assert [o["id"] for o in orders] == [second, first]


def test_vendor_sees_orders_of_own_restaurant_only(client, vendor, other_vendor, order):
    assert [o["id"] for o in client.get(f"{API}/orders", headers=vendor).json()] == [order["id"]]
    assert client.get(f"{API}/orders", headers=other_vendor).json() == []


def test_filter_by_status(client, customer, order):
    placed = client.get(f"{API}/orders", params={"status": "placed"}, headers=customer).json()
    delivered = client.get(f"{API}/orders", params={"status": "delivered"}, headers=customer).json()
    assert len(placed) == 1
    assert delivered == []


def test_strangers_get_404_for_someone_elses_order(client, other_vendor, order):
    other_customer = make_user(client, "01744444444", "customer")
    url = f"{API}/orders/{order['id']}"

    assert client.get(url, headers=other_customer).status_code == 404
    assert client.get(url, headers=other_vendor).status_code == 404
    assert client.get(url).status_code == 401
    assert client.get(f"{API}/orders/999", headers=other_customer).status_code == 404


# ---------- Status flow ----------


def test_vendor_accepts_then_marks_ready(client, vendor, order):
    assert set_status(client, vendor, order["id"], "accepted").json()["status"] == "accepted"
    assert set_status(client, vendor, order["id"], "ready").json()["status"] == "ready"


def test_vendor_rejects(client, vendor, order):
    assert set_status(client, vendor, order["id"], "rejected").json()["status"] == "rejected"


def test_customer_cancels_before_restaurant_accepts(client, customer, order):
    assert set_status(client, customer, order["id"], "cancelled").json()["status"] == "cancelled"


def test_customer_cannot_cancel_after_restaurant_accepted(client, customer, vendor, order):
    set_status(client, vendor, order["id"], "accepted")
    assert set_status(client, customer, order["id"], "cancelled").status_code == 409


def test_wrong_role_gets_403(client, customer, vendor, order):
    assert set_status(client, customer, order["id"], "accepted").status_code == 403
    assert set_status(client, vendor, order["id"], "cancelled").status_code == 403


def test_steps_cannot_be_skipped(client, vendor, order):
    assert set_status(client, vendor, order["id"], "ready").status_code == 409
    assert set_status(client, vendor, order["id"], "delivered").status_code == 409


def test_finished_order_cannot_change(client, customer, vendor, order):
    set_status(client, vendor, order["id"], "rejected")
    assert set_status(client, vendor, order["id"], "accepted").status_code == 409
    assert set_status(client, customer, order["id"], "cancelled").status_code == 409


def test_other_vendor_cannot_touch_the_order(client, other_vendor, order):
    assert set_status(client, other_vendor, order["id"], "accepted").status_code == 404


def test_unknown_status_is_422(client, vendor, order):
    assert set_status(client, vendor, order["id"], "eaten").status_code == 422


def test_status_change_fails_if_someone_else_changed_it_first(client, vendor, order):
    """Two requests read 'placed' at once; the slower one must not win."""
    with SessionLocal() as db:
        stale = db.get(Order, order["id"])  # this request read "placed"...
        set_status(client, vendor, order["id"], "accepted")  # ...then the vendor accepted
        with pytest.raises(HTTPException) as error:
            save_status(db, stale, OrderStatus.cancelled)  # ...so this cancel must fail
    assert error.value.status_code == 409
    assert client.get(f"{API}/orders/{order['id']}", headers=vendor).json()["status"] == "accepted"
