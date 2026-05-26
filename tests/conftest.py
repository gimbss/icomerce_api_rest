"""Shared test configuration and fixtures for the iCommerce test suite."""
import os
import pytest
from fastapi.testclient import TestClient

# Ensure test environment variables are set before importing app modules
os.environ.setdefault("JWT_SECRET", "icomerce-super-secret-key-change-in-production")
os.environ.setdefault("JWT_EXPIRATION_HOURS", "24")
os.environ.setdefault("MAIL_BACKEND", "console")

from main import app


def _verify_user_email(client, email: str) -> str:
    """Helper to get the verification code for a user and verify their email.
    Returns the verification code used."""
    from app.database.unit_of_work import UnitOfWork
    from app.models.user import User
    from app.models.email_verification import EmailVerification
    from sqlalchemy import select

    with UnitOfWork() as uow:
        user = uow.session.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError(f"User with email {email} not found")
        verification = uow.session.query(EmailVerification).filter(
            EmailVerification.user_id == user.id,
            EmailVerification.used == False,
        ).first()
        if not verification:
            raise ValueError(f"No verification code found for {email}")
        code = verification.code

    resp = client.post("/api/v1/auth/validate", json={"email": email, "code": code})
    assert resp.status_code == 200, f"Verification failed: {resp.text}"
    return code


@pytest.fixture(scope="module")
def client():
    """Provide a TestClient instance for API integration tests."""
    return TestClient(app)


@pytest.fixture
def unique_email():
    """Generate a unique email address for testing."""
    import uuid
    def _generate(prefix="test"):
        return f"{prefix}_{uuid.uuid4().hex[:8]}@test.com"
    return _generate


@pytest.fixture
def unique_name():
    """Generate a unique name for testing."""
    import uuid
    def _generate(prefix="TestProd"):
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    return _generate


@pytest.fixture
def registered_user(client):
    """Register a user, verify email, and return (user_id, token) for authenticated requests."""
    import uuid
    email = f"fixture_{uuid.uuid4().hex[:8]}@test.com"
    resp = client.post("/api/v1/auth/register", json={
        "email": email, "password": "Test@1234", "name": "Fixture User"
    })
    assert resp.status_code == 201
    uid = resp.json()["user_id"]

    # Verify email before login
    _verify_user_email(client, email)

    resp = client.post("/api/v1/auth/login", json={
        "email": email, "password": "Test@1234"
    })
    assert resp.status_code == 200
    token = resp.json()["token"]
    return uid, token


@pytest.fixture
def auth_headers(registered_user):
    """Return authorization headers for authenticated requests."""
    _, token = registered_user
    return {"Authorization": f"Bearer {token}"}