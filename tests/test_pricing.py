"""Unit tests: the pricing function alone, with no server and no database."""

from app.services.pricing import DELIVERY_FEE, PLATFORM_FEE, calculate_price


def test_empty_cart_costs_nothing():
    price = calculate_price([])
    assert (price.subtotal, price.delivery_fee, price.platform_fee, price.total) == (0, 0, 0, 0)


def test_subtotal_is_price_times_quantity():
    price = calculate_price([(320, 2), (60, 1)])
    assert price.subtotal == 700


def test_total_is_subtotal_plus_the_two_fees():
    price = calculate_price([(320, 2), (60, 1)])
    assert price.delivery_fee == DELIVERY_FEE
    assert price.platform_fee == PLATFORM_FEE
    assert price.total == 700 + DELIVERY_FEE + PLATFORM_FEE


def test_parts_always_add_up_to_total():
    price = calculate_price([(199, 3), (45, 7), (1, 1)])
    assert price.subtotal + price.delivery_fee + price.platform_fee == price.total
