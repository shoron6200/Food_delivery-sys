RAHIM = {"name": "Rahim Uddin", "phone": "01712345678", "password": "my-secret-pass"}


def register(client, **overrides):
    return client.post("/api/v1/auth/register", json={**RAHIM, **overrides})


def login(client, phone=RAHIM["phone"], password=RAHIM["password"]):
    return client.post(
        "/api/v1/auth/login", data={"username": phone, "password": password}
    )


def test_health(client):
    assert client.get("/").json()["status"] == "ok"


def test_register_creates_customer_and_hides_password(client):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["phone"] == RAHIM["phone"]
    assert body["role"] == "customer"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_as_vendor(client):
    assert register(client, role="vendor").json()["role"] == "vendor"


def test_register_same_phone_twice_is_rejected(client):
    register(client)
    assert register(client, name="Someone Else").status_code == 409


def test_register_rejects_bad_phone(client):
    assert register(client, phone="12345").status_code == 422


def test_register_rejects_short_password(client):
    assert register(client, password="short").status_code == 422


def test_nobody_can_register_as_admin(client):
    assert register(client, role="admin").status_code == 422


def test_login_then_me(client):
    register(client)
    response = login(client)
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["name"] == RAHIM["name"]


def test_login_wrong_password(client):
    register(client)
    assert login(client, password="wrong-password").status_code == 401


def test_login_unknown_phone(client):
    assert login(client, phone="01999999999").status_code == 401


def test_login_overlong_password_is_just_wrong(client):
    register(client)
    assert login(client, password="x" * 100).status_code == 401


def test_me_without_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_with_fake_token(client):
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401
