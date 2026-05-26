"""Tests for PasswordService and JwtService (security layer)."""
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
from os import getenv
from dotenv import load_dotenv

from app.security.password import PasswordService
from app.security.jwt import JwtService, _get_secret, _get_expiration_hours
from app.exceptions.auth_exception import InvalidCredentialsError

load_dotenv()

# ---------------------------------------------------------------------------
# PasswordService
# ---------------------------------------------------------------------------

ps = PasswordService()


def test_password_hash_and_verify():
    hashed = ps.hash("my_secret_pass")
    assert hashed != "my_secret_pass"
    assert ps.verify(hashed, "my_secret_pass") is True
    assert ps.verify(hashed, "wrong_pass") is False


def test_password_different_hashes():
    """Same password produces different hashes (argon2 salt)."""
    h1 = ps.hash("same")
    h2 = ps.hash("same")
    assert h1 != h2
    assert ps.verify(h1, "same") is True
    assert ps.verify(h2, "same") is True


def test_password_verify_empty():
    hashed = ps.hash("abc")
    assert ps.verify(hashed, "") is False
    assert ps.verify(hashed, "   ") is False


def test_password_verify_invalid_hash():
    assert ps.verify("not-a-valid-hash", "x") is False


# ---------------------------------------------------------------------------
# JwtService
# ---------------------------------------------------------------------------

jwt_svc = JwtService()
SECRET = _get_secret()


def test_jwt_create_token_returns_tuple():
    token, expires_at = jwt_svc.create_token(42)
    assert isinstance(token, str)
    assert token.count(".") == 2
    assert isinstance(expires_at, datetime)
    assert expires_at.tzinfo is not None


def test_jwt_token_has_jti():
    token, _ = jwt_svc.create_token(1)
    payload = pyjwt.decode(token, SECRET, algorithms=["HS256"])
    assert "jti" in payload
    assert len(payload["jti"]) == 32  # uuid4 hex


def test_jwt_validate_token():
    token, _ = jwt_svc.create_token(99)
    payload = jwt_svc.validate_token(token)
    assert payload["sub"] == "99"


def test_jwt_get_user_id_from_token():
    token, _ = jwt_svc.create_token(77)
    uid = jwt_svc.get_user_id_from_token(token)
    assert uid == 77


def test_jwt_validate_invalid_token():
    try:
        jwt_svc.validate_token("invalid.jwt.string")
        assert False, "Should have raised"
    except InvalidCredentialsError as e:
        assert "Invalid token" in str(e)
        assert e.status_code == 401


def test_jwt_validate_expired_token():
    payload = {
        "jti": "test-jti",
        "sub": "1",
        "iat": datetime.now(timezone.utc) - timedelta(hours=48),
        "exp": datetime.now(timezone.utc) - timedelta(hours=24),
    }
    expired = pyjwt.encode(payload, SECRET, algorithm="HS256")
    try:
        jwt_svc.validate_token(expired)
        assert False, "Should have raised"
    except InvalidCredentialsError as e:
        assert "Token expired" in str(e)
        assert e.status_code == 401


def test_jwt_custom_expiration():
    token, expires_at = jwt_svc.create_token(1, expires_in_hours=1)
    diff = (expires_at - datetime.now(timezone.utc)).total_seconds()
    assert 3500 < diff < 3700  # ~1h


def test_jwt_get_expiration_hours_default():
    hours = _get_expiration_hours()
    assert isinstance(hours, int)
    assert hours > 0


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_password_hash_and_verify()
    test_password_different_hashes()
    test_password_verify_empty()
    test_password_verify_invalid_hash()
    test_jwt_create_token_returns_tuple()
    test_jwt_token_has_jti()
    test_jwt_validate_token()
    test_jwt_get_user_id_from_token()
    test_jwt_validate_invalid_token()
    test_jwt_validate_expired_token()
    test_jwt_custom_expiration()
    test_jwt_get_expiration_hours_default()
    print("\n>>> TODOS OS TESTES DE SECURITY PASSARAM <<<")
