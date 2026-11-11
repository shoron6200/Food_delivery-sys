KACCHI = {"name": "Kacchi Ghor", "address": "House 12, Road 5, Dhanmondi, Dhaka"}
BIRYANI = {"name": "Kacchi Biryani", "price": 320, "category": "Biryani"}


def create_restaurant(client, headers, **overrides):
    return client.post("/api/v1/restaurants", json={**KACCHI, **overrides}, headers=headers)


def create_item(client, headers, restaurant_id, **overrides):
    return client.post(
        f"/api/v1/restaurants/{restaurant_id}/menu-items",
        json={**BIRYANI, **overrides},
        headers=headers,
    )


# ---------- Restaurants ----------


def test_vendor_creates_restaurant(client, vendor):
    response = create_restaurant(client, vendor)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Kacchi Ghor"
    assert body["is_open"] is True
    assert body["avg_prep_minutes"] == 20

    me = client.get("/api/v1/auth/me", headers=vendor).json()
    assert body["owner_id"] == me["id"]


def test_customer_cannot_create_restaurant(client, customer):
    assert create_restaurant(client, customer).status_code == 403


def test_anonymous_cannot_create_restaurant(client):
    assert create_restaurant(client, headers=None).status_code == 401


def test_owner_id_in_body_is_ignored(client, vendor):
    body = create_restaurant(client, vendor, owner_id=999).json()
    assert body["owner_id"] != 999


def test_anyone_can_list_and_read_restaurants(client, vendor):
    restaurant_id = create_restaurant(client, vendor).json()["id"]
    create_restaurant(client, vendor, name="Burger Lab")

    names = [r["name"] for r in client.get("/api/v1/restaurants").json()]
    assert names == ["Kacchi Ghor", "Burger Lab"]
    assert client.get(f"/api/v1/restaurants/{restaurant_id}").json()["name"] == "Kacchi Ghor"


def test_search_ignores_case(client, vendor):
    create_restaurant(client, vendor)
    create_restaurant(client, vendor, name="Burger Lab")

    found = client.get("/api/v1/restaurants", params={"search": "KACCHI"}).json()
    assert [r["name"] for r in found] == ["Kacchi Ghor"]


def test_search_percent_is_not_a_wildcard(client, vendor):
    create_restaurant(client, vendor)
    assert client.get("/api/v1/restaurants", params={"search": "%"}).json() == []


def test_limit_and_offset(client, vendor):
    for name in ["One Cafe", "Two Cafe", "Three Cafe"]:
        create_restaurant(client, vendor, name=name)

    page = client.get("/api/v1/restaurants", params={"limit": 2, "offset": 1}).json()
    assert [r["name"] for r in page] == ["Two Cafe", "Three Cafe"]
    assert client.get("/api/v1/restaurants", params={"limit": 0}).status_code == 422


def test_missing_restaurant_is_404(client):
    assert client.get("/api/v1/restaurants/999").status_code == 404
    assert client.get("/api/v1/restaurants/999/menu").status_code == 404


def test_owner_updates_only_the_fields_sent(client, vendor):
    restaurant_id = create_restaurant(client, vendor).json()["id"]

    response = client.patch(
        f"/api/v1/restaurants/{restaurant_id}",
        json={"is_open": False, "name": None},
        headers=vendor,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_open"] is False
    assert body["name"] == "Kacchi Ghor"
    assert body["address"] == KACCHI["address"]


def test_other_vendor_cannot_update_restaurant(client, vendor, other_vendor):
    restaurant_id = create_restaurant(client, vendor).json()["id"]

    response = client.patch(
        f"/api/v1/restaurants/{restaurant_id}", json={"name": "Hacked"}, headers=other_vendor
    )
    assert response.status_code == 403
    assert client.get(f"/api/v1/restaurants/{restaurant_id}").json()["name"] == "Kacchi Ghor"


def test_anonymous_update_is_401_even_if_restaurant_is_missing(client):
    assert client.patch("/api/v1/restaurants/999", json={"name": "Nope"}).status_code == 401


# ---------- Menu ----------


def test_owner_adds_items_and_anyone_reads_menu(client, vendor):
    restaurant_id = create_restaurant(client, vendor).json()["id"]

    response = create_item(client, vendor, restaurant_id)
    assert response.status_code == 201
    assert response.json()["restaurant_id"] == restaurant_id
    create_item(client, vendor, restaurant_id, name="Borhani", price=60, category="Drinks")

    menu = client.get(f"/api/v1/restaurants/{restaurant_id}/menu").json()
    assert [(i["name"], i["price"]) for i in menu] == [("Kacchi Biryani", 320), ("Borhani", 60)]


def test_menu_shows_only_that_restaurants_items(client, vendor):
    first = create_restaurant(client, vendor).json()["id"]
    second = create_restaurant(client, vendor, name="Burger Lab").json()["id"]
    create_item(client, vendor, first)

    assert client.get(f"/api/v1/restaurants/{second}/menu").json() == []


def test_price_must_be_a_positive_whole_number(client, vendor):
    restaurant_id = create_restaurant(client, vendor).json()["id"]

    assert create_item(client, vendor, restaurant_id, price=0).status_code == 422
    assert create_item(client, vendor, restaurant_id, price=-50).status_code == 422
    assert create_item(client, vendor, restaurant_id, price=99.5).status_code == 422


def test_other_vendor_cannot_add_item(client, vendor, other_vendor):
    restaurant_id = create_restaurant(client, vendor).json()["id"]
    assert create_item(client, other_vendor, restaurant_id).status_code == 403


def test_customer_cannot_add_item(client, vendor, customer):
    restaurant_id = create_restaurant(client, vendor).json()["id"]
    assert create_item(client, customer, restaurant_id).status_code == 403


def test_add_item_to_missing_restaurant_is_404(client, vendor):
    assert create_item(client, vendor, 999).status_code == 404


def test_owner_updates_item(client, vendor):
    restaurant_id = create_restaurant(client, vendor).json()["id"]
    item_id = create_item(client, vendor, restaurant_id).json()["id"]

    response = client.patch(
        f"/api/v1/menu-items/{item_id}",
        json={"price": 350, "is_available": False},
        headers=vendor,
    )
    assert response.status_code == 200
    body = response.json()
    assert (body["price"], body["is_available"], body["name"]) == (350, False, "Kacchi Biryani")


def test_other_vendor_cannot_update_item(client, vendor, other_vendor):
    restaurant_id = create_restaurant(client, vendor).json()["id"]
    item_id = create_item(client, vendor, restaurant_id).json()["id"]

    response = client.patch(
        f"/api/v1/menu-items/{item_id}", json={"price": 1}, headers=other_vendor
    )
    assert response.status_code == 403


def test_update_missing_item_is_404(client, vendor):
    response = client.patch("/api/v1/menu-items/999", json={"price": 100}, headers=vendor)
    assert response.status_code == 404
