"""The real Claude API is never called here: ask_claude is swapped for a fake."""

import pytest

from app.api.v1 import assistant as assistant_api
from app.core.config import settings
from app.models import MenuItem, Restaurant
from app.services.assistant import (
    AssistantAnswer,
    AssistantUnavailable,
    Pick,
    keep_real_picks,
    menu_as_text,
)
from app.services.rate_limit import RateLimiter
from tests.conftest import API, add_menu_item, add_restaurant

# ---------- Pure helpers ----------

KACCHI = Restaurant(id=1, name="Kacchi Ghor", rating_sum=9, review_count=2)
BURGER = Restaurant(id=2, name="Burger Lab", rating_sum=0, review_count=0)
MENU = [
    MenuItem(id=1, name="Kacchi Biryani", category="Biryani", price=320, restaurant=KACCHI, restaurant_id=1),
    MenuItem(id=2, name="Borhani", category="Drinks", price=60, restaurant=KACCHI, restaurant_id=1),
    MenuItem(id=3, name="Beef Burger", category="Burger", price=250, restaurant=BURGER, restaurant_id=2),
]


def test_menu_text_has_one_line_per_dish():
    assert menu_as_text(MENU).splitlines()[1:] == [
        "1 | Kacchi Biryani | Biryani | 320 | Kacchi Ghor | 4.5",
        "2 | Borhani | Drinks | 60 | Kacchi Ghor | 4.5",
        "3 | Beef Burger | Burger | 250 | Burger Lab | new",
    ]


def picked(picks):
    return [(item.name, quantity) for item, quantity in keep_real_picks(picks, MENU)]


def test_invented_dishes_are_dropped():
    assert picked([Pick(menu_item_id=999, quantity=1), Pick(menu_item_id=2, quantity=1)]) == [("Borhani", 1)]


def test_repeated_dish_is_kept_once():
    assert picked([Pick(menu_item_id=1, quantity=1), Pick(menu_item_id=1, quantity=3)]) == [("Kacchi Biryani", 1)]


def test_silly_quantities_are_forced_into_range():
    assert picked([Pick(menu_item_id=1, quantity=0), Pick(menu_item_id=2, quantity=500)]) == [
        ("Kacchi Biryani", 1),
        ("Borhani", 20),
    ]


def test_only_the_first_picks_restaurant_is_kept():
    picks = [Pick(menu_item_id=1, quantity=1), Pick(menu_item_id=3, quantity=1), Pick(menu_item_id=2, quantity=1)]
    assert picked(picks) == [("Kacchi Biryani", 1), ("Borhani", 1)]


def test_rate_limiter_allows_n_calls_per_key():
    limiter = RateLimiter(max_calls=2, per_seconds=60)
    assert [limiter.allow("a") for _ in range(3)] == [True, True, False]
    assert limiter.allow("b") is True  # another key has its own count


def test_rate_limiter_forgets_old_calls():
    limiter = RateLimiter(max_calls=1, per_seconds=0)
    assert limiter.allow("a") is True
    assert limiter.allow("a") is True


# ---------- The endpoint ----------


@pytest.fixture
def fake_claude(monkeypatch):
    """Pretend an API key is set and let each test decide what "Claude" answers."""
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    assistant_api.limiter.reset()
    calls = []

    def install(answer=None, error=None):
        def fake(message, items):
            calls.append((message, [item.name for item in items]))
            if error:
                raise error
            return answer

        monkeypatch.setattr(assistant_api, "ask_claude", fake)
        return calls

    return install


def ask(client, headers, message="500 takar moddhe 2 jon er jonno jhal kichu"):
    return client.post(f"{API}/assistant/suggest", json={"message": message}, headers=headers)


def test_suggestions_use_our_own_names_and_prices(client, customer, menu, fake_claude):
    calls = fake_claude(
        AssistantAnswer(
            reply="Kacchi ar borhani nao!",
            picks=[
                Pick(menu_item_id=menu["biryani"], quantity=2),
                Pick(menu_item_id=menu["borhani"], quantity=2),
                Pick(menu_item_id=999, quantity=1),  # a dish that does not exist
            ],
        )
    )

    response = ask(client, customer)
    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Kacchi ar borhani nao!"
    assert [(s["item"]["name"], s["item"]["price"], s["quantity"], s["line_total"]) for s in body["suggestions"]] == [
        ("Kacchi Biryani", 320, 2, 640),
        ("Borhani", 60, 2, 120),
    ]
    assert body["food_total"] == 760
    assert calls == [("500 takar moddhe 2 jon er jonno jhal kichu", ["Kacchi Biryani", "Borhani"])]


def test_model_only_sees_what_can_be_ordered_now(client, customer, vendor, menu, fake_claude):
    calls = fake_claude(AssistantAnswer(reply="ok", picks=[]))
    hidden = add_restaurant(client, vendor, name="Closed Cafe")
    add_menu_item(client, vendor, hidden, "Coffee", 150)
    client.patch(f"{API}/restaurants/{hidden}", json={"is_open": False}, headers=vendor)

    ask(client, customer)
    assert calls[0][1] == ["Kacchi Biryani", "Borhani"]


def test_no_model_call_when_nothing_can_be_ordered(client, customer, fake_claude):
    calls = fake_claude(AssistantAnswer(reply="should not be used", picks=[]))

    body = ask(client, customer).json()
    assert body["suggestions"] == []
    assert calls == []


def test_missing_api_key_is_503(client, customer, menu, monkeypatch):
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    assert ask(client, customer).status_code == 503


def test_model_trouble_is_503_with_a_safe_message(client, customer, menu, fake_claude):
    fake_claude(error=AssistantUnavailable("The assistant is busy. Try again in a minute."))

    response = ask(client, customer)
    assert response.status_code == 503
    assert response.json()["detail"] == "The assistant is busy. Try again in a minute."


def test_sixth_question_in_a_minute_is_429(client, customer, menu, fake_claude):
    fake_claude(AssistantAnswer(reply="ok", picks=[]))

    assert [ask(client, customer).status_code for _ in range(6)] == [200] * 5 + [429]


def test_message_length_and_roles(client, customer, vendor, menu, fake_claude):
    fake_claude(AssistantAnswer(reply="ok", picks=[]))

    assert ask(client, customer, message="x").status_code == 422
    assert ask(client, customer, message="x" * 501).status_code == 422
    assert ask(client, vendor).status_code == 403
    assert client.post(f"{API}/assistant/suggest", json={"message": "biryani"}).status_code == 401
