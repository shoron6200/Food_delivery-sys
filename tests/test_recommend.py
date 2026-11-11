"""Unit tests for the ranking rule (no database), then the endpoint."""

from app.models import MenuItem, Restaurant
from app.services.recommend import PastItem, recommend
from tests.conftest import (
    API,
    add_menu_item,
    add_restaurant,
    deliver,
    place_order,
    put_item,
)

# ---------- The ranking rule ----------


def restaurant(name, rating_sum=0, review_count=0):
    return Restaurant(name=name, rating_sum=rating_sum, review_count=review_count)


def item(item_id, name, category, price, restaurant):
    return MenuItem(id=item_id, name=name, category=category, price=price, restaurant=restaurant)


UNRATED = restaurant("New Place")
GOOD = restaurant("Good Place", rating_sum=9, review_count=2)  # 4.5 stars
BAD = restaurant("Bad Place", rating_sum=3, review_count=2)  # 1.5 stars


def names(recommendations):
    return [r.item.name for r in recommendations]


def test_new_customer_sees_best_rated_restaurants_first():
    candidates = [
        item(1, "Burger", "Burger", 250, BAD),
        item(2, "Pizza", "Pizza", 500, UNRATED),
        item(3, "Biryani", "Biryani", 320, GOOD),
    ]
    result = recommend(candidates, history=[])

    assert names(result) == ["Biryani", "Pizza", "Burger"]
    assert result[0].reason == "From a highly rated restaurant"
    assert result[1].reason == "Something new to try"
    assert result[1].score == 3.0  # unrated counts as average


def test_favourite_category_beats_a_slightly_better_rating():
    candidates = [
        item(1, "Tehari", "Biryani", 200, UNRATED),
        item(2, "Pizza", "Pizza", 500, GOOD),
    ]
    history = [PastItem(menu_item_id=99, category="Biryani", quantity=3)]
    result = recommend(candidates, history)

    assert names(result) == ["Tehari", "Pizza"]
    assert result[0].reason == "Because you like Biryani"


def test_item_ordered_before_gets_a_bonus_and_says_so():
    candidates = [
        item(1, "Kacchi", "Biryani", 320, UNRATED),
        item(2, "Tehari", "Biryani", 200, UNRATED),
    ]
    history = [PastItem(menu_item_id=1, category="Biryani", quantity=1)]
    result = recommend(candidates, history)

    assert names(result) == ["Kacchi", "Tehari"]
    assert result[0].reason == "You ordered this before"
    assert result[0].score - result[1].score == 2.0


def test_category_match_ignores_upper_and_lower_case():
    candidates = [item(1, "Tehari", "biryani", 200, UNRATED)]
    history = [PastItem(menu_item_id=99, category="BIRYANI", quantity=1)]

    assert recommend(candidates, history)[0].score == 8.0  # 3 + 5 * 100%


def test_category_points_follow_the_share_of_past_orders():
    candidates = [
        item(1, "Tehari", "Biryani", 200, UNRATED),
        item(2, "Cola", "Drinks", 40, UNRATED),
    ]
    history = [
        PastItem(menu_item_id=98, category="Biryani", quantity=3),
        PastItem(menu_item_id=99, category="Drinks", quantity=1),
    ]
    scores = {r.item.name: r.score for r in recommend(candidates, history)}

    assert scores == {"Tehari": 3 + 5 * 0.75, "Cola": 3 + 5 * 0.25}


def test_ties_put_the_cheaper_item_first_and_limit_cuts_the_list():
    candidates = [
        item(1, "Pricey", "Food", 900, UNRATED),
        item(2, "Cheap", "Food", 100, UNRATED),
        item(3, "Middle", "Food", 500, UNRATED),
    ]
    assert names(recommend(candidates, history=[], limit=2)) == ["Cheap", "Middle"]


# ---------- The endpoint ----------


def recommendations(client, headers, **params):
    return client.get(f"{API}/recommendations", params=params, headers=headers)


def test_endpoint_learns_from_delivered_orders(client, customer, vendor, rider, menu):
    burger_place = add_restaurant(client, vendor, name="Burger Lab")
    add_menu_item(client, vendor, burger_place, "Beef Burger", 250, "Burger")
    tehari = add_menu_item(client, vendor, burger_place, "Tehari", 200, "Biryani")

    before = recommendations(client, customer).json()
    assert {r["reason"] for r in before} == {"Something new to try"}

    put_item(client, customer, menu["biryani"])
    deliver(client, vendor, rider, place_order(client, customer).json()["id"])

    after = recommendations(client, customer).json()
    assert [(r["item"]["name"], r["reason"]) for r in after[:2]] == [
        ("Kacchi Biryani", "You ordered this before"),
        ("Tehari", "Because you like Biryani"),
    ]
    assert after[1]["item"]["id"] == tehari
    assert after[1]["item"]["restaurant"]["name"] == "Burger Lab"


def test_undelivered_orders_do_not_count_as_taste(client, customer, order):
    reasons = {r["reason"] for r in recommendations(client, customer).json()}
    assert reasons == {"Something new to try"}


def test_only_things_you_can_order_right_now_are_suggested(client, customer, vendor, menu):
    closed = add_restaurant(client, vendor, name="Closed Cafe")
    add_menu_item(client, vendor, closed, "Coffee", 150)
    client.patch(f"{API}/restaurants/{closed}", json={"is_open": False}, headers=vendor)
    client.patch(f"{API}/menu-items/{menu['borhani']}", json={"is_available": False}, headers=vendor)

    assert [r["item"]["name"] for r in recommendations(client, customer).json()] == ["Kacchi Biryani"]


def test_limit_and_roles(client, customer, vendor, menu):
    assert len(recommendations(client, customer, limit=1).json()) == 1
    assert recommendations(client, customer, limit=0).status_code == 422
    assert recommendations(client, vendor).status_code == 403
    assert client.get(f"{API}/recommendations").status_code == 401
