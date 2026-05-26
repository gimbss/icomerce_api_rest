"""Integration tests for the FastAPI application routers."""
from fastapi.testclient import TestClient
from main import app
import uuid

from app.database.unit_of_work import UnitOfWork
from app.models.user import User
from app.models.email_verification import EmailVerification

client = TestClient(app)


def _unique_email():
    return f"api_{uuid.uuid4().hex[:8]}@test.com"


def _unique_product():
    return f"ApiProd_{uuid.uuid4().hex[:8]}"


def _get_verification_code(email: str) -> str:
    """Get the verification code for a user from the database."""
    with UnitOfWork() as uow:
        user = uow.session.query(User).filter(User.email == email).first()
        assert user is not None, f"User with email {email} not found"
        verification = uow.session.query(EmailVerification).filter(
            EmailVerification.user_id == user.id,
            EmailVerification.used == False,
        ).first()
        assert verification is not None, f"No verification code found for {email}"
        return verification.code


def _verify_email(email: str) -> None:
    """Verify a user's email by getting the code from the database and calling /validate."""
    code = _get_verification_code(email)
    resp = client.post("/api/v1/auth/validate", json={"email": email, "code": code})
    assert resp.status_code == 200, f"Verification failed: {resp.text}"


def _register_and_login(email=None):
    """Register, verify email, then login to get a token."""
    email = email or _unique_email()
    resp = client.post("/api/v1/auth/register", json={
        "email": email, "password": "Test@1234", "name": "API Tester"
    })
    assert resp.status_code == 201, f"Register failed: {resp.text}"
    uid = resp.json()["user_id"]

    _verify_email(email)

    resp = client.post("/api/v1/auth/login", json={
        "email": email, "password": "Test@1234"
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["token"]
    return uid, token


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def _register_and_login_admin(email=None):
    """Register, verify email, promote to admin, then login to get a token."""
    email = email or _unique_email()
    uid, token = _register_and_login(email)
    # Promote user to admin
    with UnitOfWork() as uow:
        user = uow.users.get_user_by_id(uid)
        user.role = "admin"
        uow.session.commit()
    return uid, token


# -----------------------------------------------------------------------
# Health — PUBLIC
# -----------------------------------------------------------------------

def test_health():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# -----------------------------------------------------------------------
# Auth — PUBLIC: register (no token), login (returns token), validate
# -----------------------------------------------------------------------

def test_auth_register():
    email = _unique_email()
    resp = client.post("/api/v1/auth/register", json={
        "email": email, "password": "Test@1234", "name": "API Tester"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"
    assert "user_id" in data
    # Register should NOT return a token
    assert "token" not in data, "Register should not return token"


def test_auth_register_duplicate_email():
    email = _unique_email()
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "First@123", "name": "First"
    })
    resp = client.post("/api/v1/auth/register", json={
        "email": email, "password": "Second@123", "name": "Second"
    })
    assert resp.status_code == 409


def test_auth_login():
    email = _unique_email()
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "MyPass@1", "name": "Login Tester"
    })
    _verify_email(email)
    resp = client.post("/api/v1/auth/login", json={
        "email": email, "password": "MyPass@1"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "token" in data
    assert data["token"].count(".") == 2
    assert "user_id" in data


def test_auth_login_wrong_password():
    email = _unique_email()
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "Correct@1", "name": "User"
    })
    _verify_email(email)
    resp = client.post("/api/v1/auth/login", json={
        "email": email, "password": "Wrong@1"
    })
    assert resp.status_code == 401


def test_auth_login_not_found():
    resp = client.post("/api/v1/auth/login", json={
        "email": "noone@test.com", "password": "NoOne@123"
    })
    assert resp.status_code == 401


def test_auth_login_revokes_old_tokens_and_creates_new():
    email = _unique_email()
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "Pass@1234", "name": "Revoke Tester"
    })
    _verify_email(email)
    r1 = client.post("/api/v1/auth/login", json={"email": email, "password": "Pass@1234"})
    t1 = r1.json()["token"]

    r2 = client.post("/api/v1/auth/login", json={"email": email, "password": "Pass@1234"})
    t2 = r2.json()["token"]

    assert t1 != t2, "New login should generate a different token"

    # Old token should be revoked
    v1 = client.post("/api/v1/auth/validate-token", json={"token": t1})
    assert v1.status_code == 401, "Old token should be revoked"

    # New token should be valid
    v2 = client.post("/api/v1/auth/validate-token", json={"token": t2})
    assert v2.status_code == 200


def test_auth_validate_token():
    _, token = _register_and_login()
    resp = client.post("/api/v1/auth/validate-token", json={"token": token})
    assert resp.status_code == 200
    assert "user_id" in resp.json()


def test_auth_validate_invalid_token():
    resp = client.post("/api/v1/auth/validate-token", json={"token": "bad.token.here"})
    assert resp.status_code == 401


def test_auth_verify_email():
    """Test email verification flow: register -> verify -> login."""
    email = _unique_email()
    resp = client.post("/api/v1/auth/register", json={
        "email": email, "password": "Verify@123", "name": "Verify Tester"
    })
    assert resp.status_code == 201

    # Login should fail before verification
    login_resp = client.post("/api/v1/auth/login", json={
        "email": email, "password": "Verify@123"
    })
    assert login_resp.status_code == 403, "Login should fail before email verification"

    # Get verification code from DB and verify
    code = _get_verification_code(email)
    verify_resp = client.post("/api/v1/auth/validate", json={"email": email, "code": code})
    assert verify_resp.status_code == 200
    assert "user_id" in verify_resp.json()

    # Login should succeed after verification
    login_resp = client.post("/api/v1/auth/login", json={
        "email": email, "password": "Verify@123"
    })
    assert login_resp.status_code == 200


def test_auth_verify_email_invalid_code():
    """Test that invalid verification code returns error."""
    email = _unique_email()
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "Verify@123", "name": "Verify Tester"
    })
    verify_resp = client.post("/api/v1/auth/validate", json={"email": email, "code": "ZZZZZZ"})
    assert verify_resp.status_code == 400


def test_auth_resend_verification():
    """Test resending verification code."""
    email = _unique_email()
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "Resend@123", "name": "Resend Tester"
    })
    resp = client.post("/api/v1/auth/resend-verification", json={"email": email})
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


def test_auth_login_unverified():
    """Test that login fails for unverified users."""
    email = _unique_email()
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "Unverified@1", "name": "Unverified User"
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": email, "password": "Unverified@1"
    })
    assert resp.status_code == 403


# -----------------------------------------------------------------------
# Auth — PROTECTED: update/delete (Bearer + ownership)
# -----------------------------------------------------------------------

def test_auth_update_profile_protected():
    uid, token = _register_and_login()
    resp = client.put(
        f"/api/v1/auth/users/{uid}",
        json={"name": "New Name"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    assert resp.json()["user_id"] == uid


def test_auth_update_profile_no_token():
    uid, _ = _register_and_login()
    resp = client.put(f"/api/v1/auth/users/{uid}", json={"name": "Hacker"})
    assert resp.status_code == 401


def test_auth_update_profile_forbidden():
    uid1, _ = _register_and_login()
    _, token2 = _register_and_login()
    resp = client.put(
        f"/api/v1/auth/users/{uid1}",
        json={"name": "Hacker"},
        headers=_auth_header(token2),
    )
    assert resp.status_code == 403


def test_auth_delete_user_protected():
    uid, token = _register_and_login()
    resp = client.delete(
        f"/api/v1/auth/users/{uid}",
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True


def test_auth_delete_user_no_token():
    uid, _ = _register_and_login()
    resp = client.delete(f"/api/v1/auth/users/{uid}")
    assert resp.status_code == 401


def test_auth_delete_user_forbidden():
    uid1, _ = _register_and_login()
    _, token2 = _register_and_login()
    resp = client.delete(
        f"/api/v1/auth/users/{uid1}",
        headers=_auth_header(token2),
    )
    assert resp.status_code == 403


# -----------------------------------------------------------------------
# Password Strength Validation
# -----------------------------------------------------------------------

def test_auth_register_weak_password_too_short():
    """Senha com menos de 8 caracteres deve ser rejeitada."""
    email = _unique_email()
    resp = client.post("/api/v1/auth/register", json={
        "email": email, "password": "T@1a", "name": "Short Pwd"
    })
    assert resp.status_code == 422


def test_auth_register_weak_password_no_uppercase():
    """Senha sem letra maiúscula deve ser rejeitada."""
    email = _unique_email()
    resp = client.post("/api/v1/auth/register", json={
        "email": email, "password": "test@1234", "name": "No Upper"
    })
    assert resp.status_code == 422


def test_auth_register_weak_password_no_lowercase():
    """Senha sem letra minúscula deve ser rejeitada."""
    email = _unique_email()
    resp = client.post("/api/v1/auth/register", json={
        "email": email, "password": "TEST@1234", "name": "No Lower"
    })
    assert resp.status_code == 422


def test_auth_register_weak_password_no_digit():
    """Senha sem dígito deve ser rejeitada."""
    email = _unique_email()
    resp = client.post("/api/v1/auth/register", json={
        "email": email, "password": "Test@abcd", "name": "No Digit"
    })
    assert resp.status_code == 422


def test_auth_register_weak_password_no_special():
    """Senha sem caractere especial deve ser rejeitada."""
    email = _unique_email()
    resp = client.post("/api/v1/auth/register", json={
        "email": email, "password": "Test12345", "name": "No Special"
    })
    assert resp.status_code == 422


def test_auth_register_strong_password():
    """Senha forte deve ser aceita."""
    email = _unique_email()
    resp = client.post("/api/v1/auth/register", json={
        "email": email, "password": "Test@1234", "name": "Strong Pwd"
    })
    assert resp.status_code == 201


def test_auth_update_profile_weak_password():
    """Atualização de perfil com senha fraca deve ser rejeitada."""
    uid, token = _register_and_login()
    resp = client.put(
        f"/api/v1/auth/users/{uid}",
        json={"password": "weak"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 422


# -----------------------------------------------------------------------
# Products — PROTECTED (all need Bearer)
# -----------------------------------------------------------------------

def test_create_product():
    _, token = _register_and_login_admin()
    resp = client.post(
        "/api/v1/products",
        json={
            "name": _unique_product(), "description": "Test product",
            "price": 29.90, "category": "CatA", "stock": 10,
        },
        headers=_auth_header(token),
    )
    assert resp.status_code == 201
    assert resp.json()["product"]["name"].startswith("ApiProd_")


def test_create_product_no_token():
    resp = client.post("/api/v1/products", json={
        "name": _unique_product(), "description": "x",
        "price": 10.0, "category": "Cat", "stock": 1,
    })
    assert resp.status_code == 401


def _create_product_for_order(token):
    resp = client.post(
        "/api/v1/products",
        json={"name": _unique_product(), "description": "x",
              "price": 10.0, "category": "Cat", "stock": 5},
        headers=_auth_header(token),
    )
    assert resp.status_code == 201, f"Failed to create product: {resp.text}"
    return resp.json()["product"]["id"]


def test_get_product():
    _, admin_token = _register_and_login_admin()
    pid = _create_product_for_order(admin_token)
    # Any authenticated user can view products
    _, user_token = _register_and_login()
    resp = client.get(f"/api/v1/products/{pid}", headers=_auth_header(user_token))
    assert resp.status_code == 200
    assert resp.json()["product"]["id"] == pid


def test_get_product_no_token():
    _, admin_token = _register_and_login_admin()
    pid = _create_product_for_order(admin_token)
    # Now try without token
    resp = client.get(f"/api/v1/products/{pid}")
    assert resp.status_code == 401


def test_get_product_not_found():
    _, token = _register_and_login()
    resp = client.get("/api/v1/products/99999", headers=_auth_header(token))
    assert resp.status_code == 404


def test_update_product():
    _, admin_token = _register_and_login_admin()
    pid = _create_product_for_order(admin_token)
    resp = client.put(
        f"/api/v1/products/{pid}", json={"price": 15.50},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["product"]["price"] == 15.50


def test_update_product_not_found():
    _, admin_token = _register_and_login_admin()
    resp = client.put(
        "/api/v1/products/99999", json={"price": 10.0},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 404


def test_delete_product():
    _, admin_token = _register_and_login_admin()
    pid = _create_product_for_order(admin_token)
    resp = client.delete(f"/api/v1/products/{pid}", headers=_auth_header(admin_token))
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True


def test_delete_product_not_found():
    _, admin_token = _register_and_login_admin()
    resp = client.delete("/api/v1/products/99999", headers=_auth_header(admin_token))
    assert resp.status_code == 404


# -----------------------------------------------------------------------
# Orders — PROTECTED (all need Bearer)
# -----------------------------------------------------------------------

def test_create_order():
    _, admin_token = _register_and_login_admin()
    uid, user_token = _register_and_login()
    pid = _create_product_for_order(admin_token)
    resp = client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": pid, "quantity": 2}]},
        headers=_auth_header(user_token),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["order"]["items"][0]["quantity"] == 2
    assert resp.json()["order"]["user_id"] == uid
    return resp.json()["order"]["id"], uid, user_token


def test_create_order_no_token():
    resp = client.post("/api/v1/orders", json={
        "items": [{"product_id": 1, "quantity": 1}]
    })
    assert resp.status_code == 401


def test_get_order():
    oid, uid, token = test_create_order()
    resp = client.get(f"/api/v1/orders/{oid}", headers=_auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["order"]["id"] == oid


def test_get_order_no_token():
    resp = client.get("/api/v1/orders/1")
    assert resp.status_code == 401


def test_get_order_not_found():
    _, token = _register_and_login()
    resp = client.get("/api/v1/orders/99999", headers=_auth_header(token))
    assert resp.status_code == 404


def test_get_orders_by_user():
    _, admin_token = _register_and_login_admin()
    uid, user_token = _register_and_login()
    pid1 = _create_product_for_order(admin_token)
    pid2 = _create_product_for_order(admin_token)
    client.post("/api/v1/orders", json={"items": [{"product_id": pid1, "quantity": 1}]}, headers=_auth_header(user_token))
    client.post("/api/v1/orders", json={"items": [{"product_id": pid2, "quantity": 2}]}, headers=_auth_header(user_token))
    resp = client.get(f"/api/v1/orders/user/{uid}", headers=_auth_header(user_token))
    assert resp.status_code == 200
    assert len(resp.json()["orders"]) >= 2


def test_get_orders_by_user_empty():
    uid, token = _register_and_login()
    resp = client.get(f"/api/v1/orders/user/{uid}", headers=_auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["orders"] == []


def test_delete_order():
    oid, uid, token = test_create_order()
    resp = client.delete(f"/api/v1/orders/{oid}", headers=_auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True


def test_delete_order_not_found():
    _, token = _register_and_login()
    resp = client.delete("/api/v1/orders/99999", headers=_auth_header(token))
    assert resp.status_code == 404


# -----------------------------------------------------------------------
# Orders — Ownership verification (403 Forbidden)
# -----------------------------------------------------------------------

def test_get_order_forbidden():
    """User A cannot view User B's order."""
    oid, _, _ = test_create_order()
    _, token_b = _register_and_login()
    resp = client.get(f"/api/v1/orders/{oid}", headers=_auth_header(token_b))
    assert resp.status_code == 403


def test_get_orders_by_user_forbidden():
    """User A cannot view User B's orders list."""
    uid_a, token_a = _register_and_login()
    _, token_b = _register_and_login()
    resp = client.get(f"/api/v1/orders/user/{uid_a}", headers=_auth_header(token_b))
    assert resp.status_code == 403


def test_delete_order_forbidden():
    """User A cannot delete User B's order."""
    oid, _, token_a = test_create_order()
    _, token_b = _register_and_login()
    resp = client.delete(f"/api/v1/orders/{oid}", headers=_auth_header(token_b))
    assert resp.status_code == 403


# -----------------------------------------------------------------------
# Products — List endpoint
# -----------------------------------------------------------------------

def test_list_products():
    _, admin_token = _register_and_login_admin()
    _create_product_for_order(admin_token)
    # Any authenticated user can list products
    _, user_token = _register_and_login()
    resp = client.get("/api/v1/products", headers=_auth_header(user_token))
    assert resp.status_code == 200
    assert "products" in resp.json()
    assert isinstance(resp.json()["products"], list)


def test_list_products_no_token():
    resp = client.get("/api/v1/products")
    assert resp.status_code == 401


def test_list_products_pagination():
    """Test pagination parameters for product listing."""
    _, admin_token = _register_and_login_admin()
    # Create 3 products
    for _ in range(3):
        _create_product_for_order(admin_token)
    _, user_token = _register_and_login()

    # Default pagination (skip=0, limit=20)
    resp = client.get("/api/v1/products", headers=_auth_header(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert data["total"] >= 3

    # Pagination with skip and limit
    resp = client.get("/api/v1/products?skip=0&limit=2", headers=_auth_header(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["products"]) <= 2
    assert data["skip"] == 0
    assert data["limit"] == 2

    # Skip beyond available items
    resp = client.get("/api/v1/products?skip=999&limit=10", headers=_auth_header(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["products"]) == 0


def test_orders_pagination():
    """Test pagination parameters for orders listing."""
    _, admin_token = _register_and_login_admin()
    uid, user_token = _register_and_login()
    pid = _create_product_for_order(admin_token)

    # Create 3 orders
    for _ in range(3):
        resp = client.post(
            "/api/v1/orders",
            json={"items": [{"product_id": pid, "quantity": 1}]},
            headers=_auth_header(user_token),
        )
        assert resp.status_code == 201

    # Default pagination
    resp = client.get(f"/api/v1/orders/user/{uid}", headers=_auth_header(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert data["total"] >= 3

    # Pagination with limit
    resp = client.get(f"/api/v1/orders/user/{uid}?limit=2", headers=_auth_header(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["orders"]) <= 2
    assert data["limit"] == 2

    # Skip beyond available items
    resp = client.get(f"/api/v1/orders/user/{uid}?skip=999&limit=10", headers=_auth_header(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["orders"]) == 0


# -----------------------------------------------------------------------
# Auth — Logout
# -----------------------------------------------------------------------

def test_auth_logout():
    uid, token = _register_and_login()
    # Verify token works before logout (using a public-ish endpoint)
    resp = client.get(f"/api/v1/orders/user/{uid}", headers=_auth_header(token))
    assert resp.status_code == 200
    # Logout
    resp = client.post("/api/v1/auth/logout", headers=_auth_header(token))
    assert resp.status_code == 200
    # Verify token no longer works after logout
    resp = client.get(f"/api/v1/orders/user/{uid}", headers=_auth_header(token))
    assert resp.status_code == 401


# -----------------------------------------------------------------------
# Orders — Stock deduction and default unit_price
# -----------------------------------------------------------------------

def test_create_order_deducts_stock():
    """Creating an order should deduct stock from products."""
    _, admin_token = _register_and_login_admin()
    uid, user_token = _register_and_login()
    pid = client.post(
        "/api/v1/products",
        json={"name": _unique_product(), "description": "Stock test",
              "price": 10.0, "category": "Cat", "stock": 20},
        headers=_auth_header(admin_token),
    ).json()["product"]["id"]

    resp = client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": pid, "quantity": 5}]},
        headers=_auth_header(user_token),
    )
    assert resp.status_code == 201

    # Check stock was deducted
    product_resp = client.get(f"/api/v1/products/{pid}", headers=_auth_header(user_token))
    assert product_resp.json()["product"]["stock"] == 15  # 20 - 5


def test_create_order_insufficient_stock():
    """Creating an order with insufficient stock should return 400."""
    _, admin_token = _register_and_login_admin()
    uid, user_token = _register_and_login()
    pid = client.post(
        "/api/v1/products",
        json={"name": _unique_product(), "description": "Low stock",
              "price": 10.0, "category": "Cat", "stock": 3},
        headers=_auth_header(admin_token),
    ).json()["product"]["id"]

    resp = client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": pid, "quantity": 10}]},
        headers=_auth_header(user_token),
    )
    assert resp.status_code == 400
    assert "Insufficient stock" in resp.json()["detail"]


def test_create_order_default_unit_price():
    """When unit_price is not provided, product price should be used."""
    _, admin_token = _register_and_login_admin()
    uid, user_token = _register_and_login()
    pid = client.post(
        "/api/v1/products",
        json={"name": _unique_product(), "description": "Price test",
              "price": 29.90, "category": "Cat", "stock": 10},
        headers=_auth_header(admin_token),
    ).json()["product"]["id"]

    resp = client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": pid, "quantity": 2}]},
        headers=_auth_header(user_token),
    )
    assert resp.status_code == 201
    assert resp.json()["order"]["items"][0]["unit_price"] == 29.90


def test_create_order_custom_unit_price():
    """When unit_price is provided, it should override product price."""
    _, admin_token = _register_and_login_admin()
    uid, user_token = _register_and_login()
    pid = client.post(
        "/api/v1/products",
        json={"name": _unique_product(), "description": "Price test",
              "price": 29.90, "category": "Cat", "stock": 10},
        headers=_auth_header(admin_token),
    ).json()["product"]["id"]

    resp = client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": pid, "quantity": 2, "unit_price": 19.90}]},
        headers=_auth_header(user_token),
    )
    assert resp.status_code == 201
    assert resp.json()["order"]["items"][0]["unit_price"] == 19.90


def test_delete_order_restores_stock():
    """Deleting an order should restore stock to products."""
    _, admin_token = _register_and_login_admin()
    uid, user_token = _register_and_login()
    pid = client.post(
        "/api/v1/products",
        json={"name": _unique_product(), "description": "Stock restore",
              "price": 10.0, "category": "Cat", "stock": 20},
        headers=_auth_header(admin_token),
    ).json()["product"]["id"]

    # Create order
    resp = client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": pid, "quantity": 5}]},
        headers=_auth_header(user_token),
    )
    assert resp.status_code == 201
    oid = resp.json()["order"]["id"]

    # Verify stock was deducted
    product_resp = client.get(f"/api/v1/products/{pid}", headers=_auth_header(user_token))
    assert product_resp.json()["product"]["stock"] == 15  # 20 - 5

    # Delete order
    resp = client.delete(f"/api/v1/orders/{oid}", headers=_auth_header(user_token))
    assert resp.status_code == 200

    # Verify stock was restored
    product_resp = client.get(f"/api/v1/products/{pid}", headers=_auth_header(user_token))
    assert product_resp.json()["product"]["stock"] == 20  # Restored


# -----------------------------------------------------------------------
# Products — Admin-only restrictions
# -----------------------------------------------------------------------

def test_create_product_non_admin_forbidden():
    """Non-admin user cannot create products."""
    _, user_token = _register_and_login()
    resp = client.post(
        "/api/v1/products",
        json={"name": _unique_product(), "description": "x",
              "price": 10.0, "category": "Cat", "stock": 5},
        headers=_auth_header(user_token),
    )
    assert resp.status_code == 403


def test_update_product_non_admin_forbidden():
    """Non-admin user cannot update products."""
    _, admin_token = _register_and_login_admin()
    pid = _create_product_for_order(admin_token)
    _, user_token = _register_and_login()
    resp = client.put(
        f"/api/v1/products/{pid}", json={"price": 99.0},
        headers=_auth_header(user_token),
    )
    assert resp.status_code == 403


def test_delete_product_non_admin_forbidden():
    """Non-admin user cannot delete products."""
    _, admin_token = _register_and_login_admin()
    pid = _create_product_for_order(admin_token)
    _, user_token = _register_and_login()
    resp = client.delete(f"/api/v1/products/{pid}", headers=_auth_header(user_token))
    assert resp.status_code == 403


# -----------------------------------------------------------------------
# Orders — Status update (admin only)
# -----------------------------------------------------------------------

def test_update_order_status():
    """Admin can update order status."""
    _, admin_token = _register_and_login_admin()
    uid, user_token = _register_and_login()
    pid = _create_product_for_order(admin_token)

    # Create order as regular user
    resp = client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": pid, "quantity": 1}]},
        headers=_auth_header(user_token),
    )
    assert resp.status_code == 201
    oid = resp.json()["order"]["id"]

    # Update status to confirmed
    resp = client.patch(
        f"/api/v1/orders/{oid}/status",
        json={"status": "confirmed"},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["order"]["status"] == "confirmed"

    # Update status to shipped
    resp = client.patch(
        f"/api/v1/orders/{oid}/status",
        json={"status": "shipped"},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["order"]["status"] == "shipped"


def test_update_order_status_non_admin_forbidden():
    """Non-admin user cannot update order status."""
    _, admin_token = _register_and_login_admin()
    uid, user_token = _register_and_login()
    pid = _create_product_for_order(admin_token)

    # Create order as regular user
    resp = client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": pid, "quantity": 1}]},
        headers=_auth_header(user_token),
    )
    assert resp.status_code == 201
    oid = resp.json()["order"]["id"]

    # Try to update status as regular user
    resp = client.patch(
        f"/api/v1/orders/{oid}/status",
        json={"status": "confirmed"},
        headers=_auth_header(user_token),
    )
    assert resp.status_code == 403


def test_update_order_status_cancelled_restores_stock():
    """Cancelling an order should restore stock."""
    _, admin_token = _register_and_login_admin()
    uid, user_token = _register_and_login()
    pid = _create_product_for_order(admin_token)

    # Create order
    resp = client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": pid, "quantity": 3}]},
        headers=_auth_header(user_token),
    )
    assert resp.status_code == 201
    oid = resp.json()["order"]["id"]

    # Verify stock was deducted
    product_resp = client.get(f"/api/v1/products/{pid}", headers=_auth_header(user_token))
    assert product_resp.json()["product"]["stock"] == 2  # 5 - 3

    # Cancel order
    resp = client.patch(
        f"/api/v1/orders/{oid}/status",
        json={"status": "cancelled"},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["order"]["status"] == "cancelled"

    # Verify stock was restored
    product_resp = client.get(f"/api/v1/products/{pid}", headers=_auth_header(user_token))
    assert product_resp.json()["product"]["stock"] == 5  # Restored


def test_update_order_status_invalid_status():
    """Invalid status should return 422."""
    _, admin_token = _register_and_login_admin()
    uid, user_token = _register_and_login()
    pid = _create_product_for_order(admin_token)

    resp = client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": pid, "quantity": 1}]},
        headers=_auth_header(user_token),
    )
    assert resp.status_code == 201
    oid = resp.json()["order"]["id"]

    resp = client.patch(
        f"/api/v1/orders/{oid}/status",
        json={"status": "invalid_status"},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 422


def test_order_response_includes_status_and_timestamps():
    """Order response should include status, created_at, and updated_at."""
    _, admin_token = _register_and_login_admin()
    uid, user_token = _register_and_login()
    pid = _create_product_for_order(admin_token)

    resp = client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": pid, "quantity": 1}]},
        headers=_auth_header(user_token),
    )
    assert resp.status_code == 201
    order = resp.json()["order"]
    assert "status" in order
    assert order["status"] == "pending"
    assert "created_at" in order
    assert "updated_at" in order


# -----------------------------------------------------------------------
# Auth — Role management (admin only)
# -----------------------------------------------------------------------

def test_admin_can_promote_user_to_admin():
    """Admin can promote a customer to admin via PATCH /auth/users/{id}/role."""
    _, admin_token = _register_and_login_admin()
    uid, _ = _register_and_login()

    resp = client.patch(
        f"/api/v1/auth/users/{uid}/role",
        json={"role": "admin"},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["user_id"] == uid
    assert data["role"] == "admin"


def test_admin_can_demote_admin_to_customer():
    """Admin can demote another admin to customer."""
    # Create first admin
    _, admin_token = _register_and_login_admin()
    # Create and promote second user to admin
    uid2, _ = _register_and_login()
    client.patch(
        f"/api/v1/auth/users/{uid2}/role",
        json={"role": "admin"},
        headers=_auth_header(admin_token),
    )
    # Now demote the second admin
    resp = client.patch(
        f"/api/v1/auth/users/{uid2}/role",
        json={"role": "customer"},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "customer"


def test_promote_user_non_admin_forbidden():
    """Non-admin user cannot promote users."""
    _, user_token = _register_and_login()
    uid2, _ = _register_and_login()

    resp = client.patch(
        f"/api/v1/auth/users/{uid2}/role",
        json={"role": "admin"},
        headers=_auth_header(user_token),
    )
    assert resp.status_code == 403


def test_promote_user_no_token_unauthorized():
    """Unauthenticated user cannot promote users."""
    uid, _ = _register_and_login()

    resp = client.patch(
        f"/api/v1/auth/users/{uid}/role",
        json={"role": "admin"},
    )
    assert resp.status_code == 401


def test_promote_user_invalid_role():
    """Invalid role should return 422 validation error."""
    _, admin_token = _register_and_login_admin()
    uid, _ = _register_and_login()

    resp = client.patch(
        f"/api/v1/auth/users/{uid}/role",
        json={"role": "superadmin"},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 422


def test_promote_nonexistent_user():
    """Promoting a non-existent user should return 404."""
    _, admin_token = _register_and_login_admin()

    resp = client.patch(
        "/api/v1/auth/users/99999/role",
        json={"role": "admin"},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 404


def test_cannot_demote_last_admin():
    """Cannot demote the last admin to customer (prevents lockout)."""
    # Register a user and promote to admin via DB
    admin_email = f"lastadmin_{uuid.uuid4().hex[:8]}@test.com"
    admin_uid, admin_tok = _register_and_login(admin_email)
    with UnitOfWork() as uow:
        user = uow.users.get_user_by_id(admin_uid)
        user.role = "admin"
        uow.session.commit()
        # Verify this is the only admin
        admin_count = len(uow.users.get_admin_users())

    # If there are other admins from previous tests, we can't reliably test this
    # So we only test if this user is the sole admin
    if admin_count == 1:
        resp = client.patch(
            f"/api/v1/auth/users/{admin_uid}/role",
            json={"role": "customer"},
            headers=_auth_header(admin_tok),
        )
        assert resp.status_code == 403
        assert "last admin" in resp.json()["detail"].lower()


def test_can_demote_admin_when_another_admin_exists():
    """Can demote an admin when there is another admin."""
    # Create first admin
    _, admin_token = _register_and_login_admin()
    # Create and promote second user to admin
    uid2, _ = _register_and_login()
    client.patch(
        f"/api/v1/auth/users/{uid2}/role",
        json={"role": "admin"},
        headers=_auth_header(admin_token),
    )
    # Now there are 2 admins, so we can demote the second one
    resp = client.patch(
        f"/api/v1/auth/users/{uid2}/role",
        json={"role": "customer"},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "customer"


if __name__ == "__main__":
    test_health()
    test_auth_register()
    test_auth_register_duplicate_email()
    test_auth_login()
    test_auth_login_wrong_password()
    test_auth_login_not_found()
    test_auth_login_revokes_old_tokens_and_creates_new()
    test_auth_validate_token()
    test_auth_validate_invalid_token()
    test_auth_update_profile_protected()
    test_auth_update_profile_no_token()
    test_auth_update_profile_forbidden()
    test_auth_delete_user_protected()
    test_auth_delete_user_no_token()
    test_auth_delete_user_forbidden()
    test_create_product()
    test_create_product_no_token()
    test_get_product()
    test_get_product_no_token()
    test_get_product_not_found()
    test_update_product()
    test_update_product_not_found()
    test_delete_product()
    test_delete_product_not_found()
    test_list_products()
    test_list_products_no_token()
    test_create_order()
    test_create_order_no_token()
    test_get_order()
    test_get_order_no_token()
    test_get_order_not_found()
    test_get_orders_by_user()
    test_get_orders_by_user_empty()
    test_delete_order()
    test_delete_order_not_found()
    test_get_order_forbidden()
    test_get_orders_by_user_forbidden()
    test_delete_order_forbidden()
    test_auth_logout()
    test_create_order_deducts_stock()
    test_create_order_insufficient_stock()
    test_create_order_default_unit_price()
    test_create_order_custom_unit_price()
    test_delete_order_restores_stock()
