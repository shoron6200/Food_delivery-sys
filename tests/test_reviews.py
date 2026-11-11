from tests.conftest import API, deliver, make_user, place_order, put_item


def review(client, headers, order_id, rating=5, **extra):
    return client.post(
        f"{API}/orders/{order_id}/review", json={"rating": rating, **extra}, headers=headers
    )


def restaurant(client, restaurant_id):
    return client.get(f"{API}/restaurants/{restaurant_id}").json()


def test_new_restaurant_has_no_rating(client, menu):
    body = restaurant(client, menu["restaurant"])
    assert body["average_rating"] is None
    assert body["review_count"] == 0
    assert client.get(f"{API}/restaurants/{menu['restaurant']}/reviews").json() == []


def test_customer_reviews_delivered_order(client, customer, menu, delivered_order):
    response = review(client, customer, delivered_order["id"], rating=4, comment="  Khub moja!  ")
    assert response.status_code == 201
    body = response.json()
    assert (body["rating"], body["comment"]) == (4, "Khub moja!")
    assert body["customer_name"] == "Test"  # first name only

    assert restaurant(client, menu["restaurant"])["average_rating"] == 4.0
    assert restaurant(client, menu["restaurant"])["review_count"] == 1
    public = client.get(f"{API}/restaurants/{menu['restaurant']}/reviews").json()
    assert [r["rating"] for r in public] == [4]


def test_average_of_several_reviews_newest_listed_first(client, customer, vendor, rider, menu):
    for rating in (5, 2):
        put_item(client, customer, menu["biryani"])
        order_id = place_order(client, customer).json()["id"]
        deliver(client, vendor, rider, order_id)
        review(client, customer, order_id, rating=rating)

    body = restaurant(client, menu["restaurant"])
    assert (body["average_rating"], body["review_count"]) == (3.5, 2)
    listed = client.get(f"{API}/restaurants/{menu['restaurant']}/reviews").json()
    assert [r["rating"] for r in listed] == [2, 5]


def test_one_review_per_order(client, customer, menu, delivered_order):
    review(client, customer, delivered_order["id"], rating=5)

    assert review(client, customer, delivered_order["id"], rating=1).status_code == 409
    body = restaurant(client, menu["restaurant"])
    assert (body["average_rating"], body["review_count"]) == (5.0, 1)


def test_cannot_review_before_delivery(client, customer, menu, order):
    assert review(client, customer, order["id"]).status_code == 409
    assert restaurant(client, menu["restaurant"])["review_count"] == 0


def test_cannot_review_someone_elses_order(client, delivered_order):
    stranger = make_user(client, "01744444444", "customer")
    assert review(client, stranger, delivered_order["id"]).status_code == 404
    assert review(client, stranger, 999).status_code == 404


def test_rating_must_be_1_to_5(client, customer, delivered_order):
    assert review(client, customer, delivered_order["id"], rating=0).status_code == 422
    assert review(client, customer, delivered_order["id"], rating=6).status_code == 422
    assert review(client, customer, delivered_order["id"], rating=4.5).status_code == 422


def test_only_customers_review(client, vendor, rider, delivered_order):
    assert review(client, vendor, delivered_order["id"]).status_code == 403
    assert review(client, rider, delivered_order["id"]).status_code == 403
    assert client.post(f"{API}/orders/{delivered_order['id']}/review", json={"rating": 5}).status_code == 401


def test_reviews_of_missing_restaurant_is_404(client):
    assert client.get(f"{API}/restaurants/999/reviews").status_code == 404
