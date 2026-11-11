"""Unit tests for the order rules: no server, no database."""

from datetime import datetime, timezone

from app.models.order import OrderStatus as S
from app.models.user import UserRole as R
from app.services.orders import DELIVERY_MINUTES, promised_time, role_allowed_to_change


def test_the_happy_path_and_who_does_each_step():
    assert role_allowed_to_change(S.placed, S.accepted) == R.vendor
    assert role_allowed_to_change(S.accepted, S.ready) == R.vendor
    assert role_allowed_to_change(S.ready, S.picked_up) == R.rider
    assert role_allowed_to_change(S.picked_up, S.delivered) == R.rider


def test_only_a_placed_order_can_be_rejected_or_cancelled():
    assert role_allowed_to_change(S.placed, S.rejected) == R.vendor
    assert role_allowed_to_change(S.placed, S.cancelled) == R.customer
    assert role_allowed_to_change(S.accepted, S.cancelled) is None
    assert role_allowed_to_change(S.accepted, S.rejected) is None


def test_steps_cannot_be_skipped_or_undone():
    assert role_allowed_to_change(S.placed, S.delivered) is None
    assert role_allowed_to_change(S.placed, S.ready) is None
    assert role_allowed_to_change(S.ready, S.accepted) is None


def test_finished_orders_never_change():
    for finished in (S.delivered, S.rejected, S.cancelled):
        for new in S:
            assert role_allowed_to_change(finished, new) is None


def test_promise_is_cooking_time_plus_riding_time():
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    promised = promised_time(now, prep_minutes=25)
    assert (promised - now).total_seconds() == (25 + DELIVERY_MINUTES) * 60
