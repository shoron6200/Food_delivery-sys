"""Test setup: a throwaway database and a fake secret, set before the app loads."""

import os
import tempfile

os.environ["SECRET_KEY"] = "test-only-secret-key-0123456789-abcdefgh"
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
