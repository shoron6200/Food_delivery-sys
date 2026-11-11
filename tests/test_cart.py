import pytest

from app.services.pricing import DELIVERY_FEE, PLATFORM_FEE
from tests.conftest import make_user

API = "/api/v1"


def add_restaurant(client, vendor, name="Kacchi Ghor"):
    body = {"name": name, "address": "House 12, Road 5, Dhanmondi, Dhaka"}
    return client.post(f"{API}/restaurants", json=body, headers=vendor).json()["id"]


def add_menu_item(client, vendor, restaurant_id, name, price):
    body = {"name": name, "price": price, "category": "Food"}
    response = client.post(
        f"{API}/restaurants/{restaurant_id}/menu-items", json=body, headers=vendor
    )
    return response.json()["id"]


@pytest.fixture
def menu(client, vendor):
    """One open restaurant with two items. Returns their ids."""
    restaurant_id = add_restaurant(client, vendor)
    return {
        "restaurant": restaurant_id,
        "biryani": add_menu_item(client, vendor, restaurant_id, "Kacchi Biryani", 320),
        "borhani": add_menu_item(client, vendor, restaurant_id, "Borhani", 60),
    }


def put_item(client, headers, menu_item_id, quantity=1):
    return client.put(
        f"{API}/cart/items/{menu_item_id}", json={"quantity": quantity}, headers=headers
    )


def test_new_cart_is_empty_and_free(client, customer):
    cart = client.get(f"{API}/cart", headers=customer).json()
    assert cart == {
        "restaurant": None,
        "items": [],
        "price": {"subtotal": 0, "delivery_fee": 0, "platform_fee": 0, "total": 0},
    }


def test_add_item_shows_full_price_breakdown(client, customer, menu):
    response = put_item(client, customer, menu["biryani"], quantity=2)
    assert response.status_code == 200
    cart = response.json()

    assert cart["restaurant"] == {"id": menu["restaurant"], "name": "Kacchi Ghor", "is_open": True}
    assert cart["items"] == [
        {
            "menu_item_id": menu["biryani"],
            "name": "Kacchi Biryani",
            "unit_price": 320,
            "quantity": 2,
            "line_total": 640,
            "is_available": True,
        }
    ]
    assert cart["price"] == {
        "subtotal": 640,
        "delivery_fee": DELIVERY_FEE,
        "platform_fee": PLATFORM_FEE,
        "total": 640 + DELIVERY_FEE + PLATFORM_FEE,
    }


def test_put_twice_replaces_quantity_instead_of_adding(client, customer, menu):
    put_item(client, customer, menu["biryani"], quantity=2)
    put_item(client, customer, menu["biryani"], quantity=2)
    cart = put_item(client, customer, menu["biryani"], quantity=3).json()

    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 3


def test_two_items_add_up(client, customer, menu):
    put_item(client, customer, menu["biryani"], quantity=1)
    put_item(client, customer, menu["borhani"], quantity=2)

    cart = client.get(f"{API}/cart", headers=customer).json()
    assert [line["line_total"] for line in cart["items"]] == [320, 120]
    assert cart["price"]["subtotal"] == 440


def test_cart_uses_the_menu_price_of_right_now(client, customer, vendor, menu):
    put_item(client, customer, menu["biryani"], quantity=1)
    client.patch(f"{API}/menu-items/{menu['biryani']}", json={"price": 350}, headers=vendor)

    cart = client.get(f"{API}/cart", headers=customer).json()
    assert cart["items"][0]["unit_price"] == 350
    assert cart["price"]["subtotal"] == 350


def test_item_turned_off_later_is_flagged_in_cart(client, customer, vendor, menu):
    put_item(client, customer, menu["biryani"])
    client.patch(
        f"{API}/menu-items/{menu['biryani']}", json={"is_available": False}, headers=vendor
    )

    cart = client.get(f"{API}/cart", headers=customer).json()
    assert cart["items"][0]["is_available"] is False


def test_cannot_mix_two_restaurants(client, customer, vendor, menu):
    other_restaurant = add_restaurant(client, vendor, name="Burger Lab")
    burger = add_menu_item(client, vendor, other_restaurant, "Beef Burger", 250)
    put_item(client, customer, menu["biryani"])

    response = put_item(client, customer, burger)
    assert response.status_code == 409
    cart = client.get(f"{API}/cart", headers=customer).json()
    assert [line["name"] for line in cart["items"]] == ["Kacchi Biryani"]


def test_after_clearing_cart_another_restaurant_is_fine(client, customer, vendor, menu):
    other_restaurant = add_restaurant(client, vendor, name="Burger Lab")
    burger = add_menu_item(client, vendor, other_restaurant, "Beef Burger", 250)
    put_item(client, customer, menu["biryani"])

    assert client.delete(f"{API}/cart", headers=customer).status_code == 204
    cart = put_item(client, customer, burger).json()
    assert cart["restaurant"]["name"] == "Burger Lab"


def test_cannot_add_unavailable_item(client, customer, vendor, menu):
    client.patch(
        f"{API}/menu-items/{menu['biryani']}", json={"is_available": False}, headers=vendor
    )
    assert put_item(client, customer, menu["biryani"]).status_code == 409


def test_cannot_add_from_closed_restaurant(client, customer, vendor, menu):
    client.patch(
        f"{API}/restaurants/{menu['restaurant']}", json={"is_open": False}, headers=vendor
    )
    assert put_item(client, customer, menu["biryani"]).status_code == 409


def test_missing_menu_item_is_404(client, customer):
    assert put_item(client, customer, 999).status_code == 404


def test_quantity_must_be_1_to_20(client, customer, menu):
    assert put_item(client, customer, menu["biryani"], quantity=0).status_code == 422
    assert put_item(client, customer, menu["biryani"], quantity=21).status_code == 422
    assert put_item(client, customer, menu["biryani"], quantity=20).status_code == 200


def test_remove_item(client, customer, menu):
    put_item(client, customer, menu["biryani"])
    put_item(client, customer, menu["borhani"])

    response = client.delete(f"{API}/cart/items/{menu['biryani']}", headers=customer)
    assert response.status_code == 200
    assert [line["name"] for line in response.json()["items"]] == ["Borhani"]


def test_removing_item_that_is_not_in_cart_is_fine(client, customer, menu):
    response = client.delete(f"{API}/cart/items/{menu['biryani']}", headers=customer)
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_each_customer_has_their_own_cart(client, customer, menu):
    other_customer = make_user(client, "01744444444", "customer")
    put_item(client, customer, menu["biryani"])

    assert client.get(f"{API}/cart", headers=other_customer).json()["items"] == []
    client.delete(f"{API}/cart", headers=other_customer)
    assert len(client.get(f"{API}/cart", headers=customer).json()["items"]) == 1


def test_only_customers_have_a_cart(client, vendor, menu):
    assert client.get(f"{API}/cart", headers=vendor).status_code == 403
    assert put_item(client, vendor, menu["biryani"]).status_code == 403


def test_cart_needs_login(client, menu):
    assert client.get(f"{API}/cart").status_code == 401
    assert put_item(client, None, menu["biryani"]).status_code == 401
