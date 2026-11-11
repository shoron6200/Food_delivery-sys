import pytest

from tests.conftest import API, make_user, place_order, put_item, set_status


def claim(client, headers, order_id):
    return client.post(f"{API}/orders/{order_id}/claim", headers=headers)


def available_ids(client, headers):
    return [o["id"] for o in client.get(f"{API}/orders/available", headers=headers).json()]


@pytest.fixture
def accepted_order(client, vendor, order):
    """An order the restaurant has accepted, so it now needs a rider."""
    set_status(client, vendor, order["id"], "accepted")
    return order


def test_full_delivery_from_order_to_doorstep(client, customer, vendor, rider, order):
    order_id = order["id"]
    assert available_ids(client, rider) == []  # not accepted yet

    set_status(client, vendor, order_id, "accepted")
    assert available_ids(client, rider) == [order_id]

    claimed = claim(client, rider, order_id)
    assert claimed.status_code == 200
    rider_id = client.get(f"{API}/auth/me", headers=rider).json()["id"]
    assert claimed.json()["rider_id"] == rider_id
    assert available_ids(client, rider) == []  # taken

    set_status(client, vendor, order_id, "ready")
    assert set_status(client, rider, order_id, "picked_up").json()["status"] == "picked_up"
    delivered = set_status(client, rider, order_id, "delivered").json()
    assert delivered["status"] == "delivered"
    assert delivered["delivered_at"] is not None

    final = client.get(f"{API}/orders/{order_id}", headers=customer).json()
    assert final["status"] == "delivered"
    assert [o["id"] for o in client.get(f"{API}/orders", headers=rider).json()] == [order_id]


def test_only_one_rider_gets_the_order(client, rider, accepted_order):
    second_rider = make_user(client, "01766666666", "rider")

    assert claim(client, rider, accepted_order["id"]).status_code == 200
    assert claim(client, second_rider, accepted_order["id"]).status_code == 409


def test_cannot_claim_before_restaurant_accepts(client, rider, order):
    assert claim(client, rider, order["id"]).status_code == 409


def test_cannot_claim_missing_or_finished_order(client, vendor, rider, order):
    assert claim(client, rider, 999).status_code == 409
    set_status(client, vendor, order["id"], "rejected")
    assert claim(client, rider, order["id"]).status_code == 409


def test_rider_does_one_delivery_at_a_time(client, customer, vendor, rider, accepted_order, menu):
    put_item(client, customer, menu["borhani"])
    second = place_order(client, customer).json()["id"]
    set_status(client, vendor, second, "accepted")

    claim(client, rider, accepted_order["id"])
    assert claim(client, rider, second).status_code == 409

    set_status(client, vendor, accepted_order["id"], "ready")
    set_status(client, rider, accepted_order["id"], "picked_up")
    set_status(client, rider, accepted_order["id"], "delivered")
    assert claim(client, rider, second).status_code == 200


def test_rider_cannot_pick_up_before_food_is_ready(client, rider, accepted_order):
    claim(client, rider, accepted_order["id"])
    assert set_status(client, rider, accepted_order["id"], "picked_up").status_code == 409


def test_rider_who_did_not_claim_cannot_see_or_move_the_order(client, vendor, rider, accepted_order):
    second_rider = make_user(client, "01766666666", "rider")
    claim(client, rider, accepted_order["id"])
    set_status(client, vendor, accepted_order["id"], "ready")

    assert client.get(f"{API}/orders/{accepted_order['id']}", headers=second_rider).status_code == 404
    assert set_status(client, second_rider, accepted_order["id"], "picked_up").status_code == 404


def test_only_riders_see_available_orders_and_claim(client, customer, vendor, accepted_order):
    for headers in (customer, vendor):
        assert client.get(f"{API}/orders/available", headers=headers).status_code == 403
        assert claim(client, headers, accepted_order["id"]).status_code == 403
    assert client.get(f"{API}/orders/available").status_code == 401
