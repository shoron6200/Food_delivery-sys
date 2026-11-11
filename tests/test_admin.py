from tests.conftest import API, add_menu_item, place_order, put_item


def new_restaurant(client, vendor, name="Kacchi Ghor") -> int:
    """A restaurant that has NOT been approved yet."""
    body = {"name": name, "address": "House 12, Road 5, Dhanmondi, Dhaka"}
    return client.post(f"{API}/restaurants", json=body, headers=vendor).json()["id"]


def set_approval(client, headers, restaurant_id, is_approved=True):
    return client.patch(
        f"{API}/admin/restaurants/{restaurant_id}",
        json={"is_approved": is_approved},
        headers=headers,
    )


def test_admin_sees_waiting_restaurants_and_approves_one(client, admin, vendor):
    first = new_restaurant(client, vendor)
    new_restaurant(client, vendor, name="Burger Lab")

    waiting = client.get(f"{API}/admin/restaurants", params={"approved": False}, headers=admin)
    assert [r["name"] for r in waiting.json()] == ["Kacchi Ghor", "Burger Lab"]

    response = set_approval(client, admin, first)
    assert response.status_code == 200
    assert response.json()["is_approved"] is True

    assert [r["name"] for r in client.get(f"{API}/restaurants").json()] == ["Kacchi Ghor"]
    still_waiting = client.get(
        f"{API}/admin/restaurants", params={"approved": False}, headers=admin
    ).json()
    assert [r["name"] for r in still_waiting] == ["Burger Lab"]
    assert len(client.get(f"{API}/admin/restaurants", headers=admin).json()) == 2


def test_admin_can_take_a_restaurant_off_again(client, admin, vendor):
    restaurant_id = new_restaurant(client, vendor)
    set_approval(client, admin, restaurant_id)
    set_approval(client, admin, restaurant_id, is_approved=False)

    assert client.get(f"{API}/restaurants").json() == []


def test_only_admin_uses_admin_endpoints(client, vendor, customer, rider):
    restaurant_id = new_restaurant(client, vendor)

    for headers in (vendor, customer, rider):
        assert client.get(f"{API}/admin/restaurants", headers=headers).status_code == 403
        assert set_approval(client, headers, restaurant_id).status_code == 403
    assert client.get(f"{API}/admin/restaurants").status_code == 401


def test_approving_missing_restaurant_is_404(client, admin):
    assert set_approval(client, admin, 999).status_code == 404


def test_cannot_add_to_cart_before_approval_but_can_after(client, admin, vendor, customer):
    restaurant_id = new_restaurant(client, vendor)
    item = add_menu_item(client, vendor, restaurant_id, "Kacchi Biryani", 320)

    assert put_item(client, customer, item).status_code == 409
    set_approval(client, admin, restaurant_id)
    assert put_item(client, customer, item).status_code == 200


def test_cannot_order_if_approval_is_taken_away_after_adding(client, admin, customer, menu):
    put_item(client, customer, menu["biryani"])
    set_approval(client, admin, menu["restaurant"], is_approved=False)

    assert place_order(client, customer).status_code == 409


def test_admin_sees_every_order_but_cannot_move_them(client, admin, order):
    assert [o["id"] for o in client.get(f"{API}/orders", headers=admin).json()] == [order["id"]]
    assert client.get(f"{API}/orders/{order['id']}", headers=admin).status_code == 200

    response = client.patch(
        f"{API}/orders/{order['id']}/status", json={"status": "accepted"}, headers=admin
    )
    assert response.status_code == 403
