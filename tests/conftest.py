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
