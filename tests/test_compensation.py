"""Unit tests for the Late Compensation rule: no server, no database."""

from datetime import datetime, timedelta, timezone

from app.services.compensation import calculate_compensation, minutes_late
from app.services.pricing import calculate_price

PROMISED = datetime(2026, 1, 1, 13, 0, tzinfo=timezone.utc)
PRICE = calculate_price([(320, 2), (60, 1)])  # subtotal 700, delivery fee 40


def test_on_time_or_early_is_zero_minutes_late():
    assert minutes_late(PROMISED, PROMISED) == 0
    assert minutes_late(PROMISED, PROMISED - timedelta(minutes=10)) == 0


def test_late_minutes_are_counted_in_whole_minutes():
    assert minutes_late(PROMISED, PROMISED + timedelta(minutes=20)) == 20
    assert minutes_late(PROMISED, PROMISED + timedelta(minutes=20, seconds=59)) == 20


def test_small_delay_pays_nothing():
    assert calculate_compensation(0, PRICE) == 0
    assert calculate_compensation(15, PRICE) == 0


def test_late_delivery_gives_the_delivery_fee_back():
    assert calculate_compensation(16, PRICE) == 40
    assert calculate_compensation(30, PRICE) == 40


def test_big_delay_also_gives_ten_percent_of_the_food_price():
    assert calculate_compensation(31, PRICE) == 40 + 70
    assert calculate_compensation(120, PRICE) == 40 + 70


def test_ten_percent_is_rounded_down_to_whole_taka():
    price = calculate_price([(199, 1)])
    assert calculate_compensation(45, price) == price.delivery_fee + 19
