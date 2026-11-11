"""Test setup: a throwaway database and a fake secret, set before the app loads."""

import os
import tempfile

os.environ["SECRET_KEY"] = "test-only-secret-key-0123456789-abcdefgh"
os.environ["BCRYPT_ROUNDS"] = "4"  # fast hashing, for tests only
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    """A test client with empty tables, so tests cannot affect each other."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


def make_user(client, phone: str, role: str = "customer") -> dict[str, str]:
    """Register a user, log in, and return the headers that prove who they are."""
    password = "test-password"
    client.post(
        "/api/v1/auth/register",
        json={"name": f"Test {role}", "phone": phone, "password": password, "role": role},
    )
    response = client.post(
        "/api/v1/auth/login", data={"username": phone, "password": password}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def vendor(client):
    return make_user(client, "01711111111", "vendor")


@pytest.fixture
def other_vendor(client):
    return make_user(client, "01722222222", "vendor")


@pytest.fixture
def customer(client):
    return make_user(client, "01733333333", "customer")


@pytest.fixture
def rider(client):
    return make_user(client, "01755555555", "rider")


# ---------- Helpers shared by the test files ----------

API = "/api/v1"


def add_restaurant(client, vendor, name="Kacchi Ghor") -> int:
    body = {"name": name, "address": "House 12, Road 5, Dhanmondi, Dhaka"}
    return client.post(f"{API}/restaurants", json=body, headers=vendor).json()["id"]


def add_menu_item(client, vendor, restaurant_id, name, price, category="Food") -> int:
    body = {"name": name, "price": price, "category": category}
    response = client.post(
        f"{API}/restaurants/{restaurant_id}/menu-items", json=body, headers=vendor
    )
    return response.json()["id"]


def put_item(client, headers, menu_item_id, quantity=1):
    return client.put(
        f"{API}/cart/items/{menu_item_id}", json={"quantity": quantity}, headers=headers
    )


def place_order(client, headers, address="Flat 4B, House 7, Mirpur 10, Dhaka"):
    return client.post(
        f"{API}/orders", json={"delivery_address": address}, headers=headers
    )


def set_status(client, headers, order_id, new_status):
    return client.patch(
        f"{API}/orders/{order_id}/status", json={"status": new_status}, headers=headers
    )


@pytest.fixture
def menu(client, vendor):
    """One open restaurant with two items. Returns their ids."""
    restaurant_id = add_restaurant(client, vendor)
    return {
        "restaurant": restaurant_id,
        "biryani": add_menu_item(client, vendor, restaurant_id, "Kacchi Biryani", 320, "Biryani"),
        "borhani": add_menu_item(client, vendor, restaurant_id, "Borhani", 60, "Drinks"),
    }


@pytest.fixture
def order(client, customer, menu):
    """A freshly placed order: 2 biryani + 1 borhani. Returns the order JSON."""
    put_item(client, customer, menu["biryani"], quantity=2)
    put_item(client, customer, menu["borhani"], quantity=1)
    return place_order(client, customer).json()
