"""Tests for TokenRepository."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from app.database.unit_of_work import UnitOfWork
from app.repositories.token_repository import TokenRepository
from app.security.jwt import JwtService
import uuid


def _unique_email():
    return f"tokenrepo_{uuid.uuid4().hex[:8]}@test.com"


def _setup_user(uow):
    return uow.users.create_user(
        email=_unique_email(), password="x", name="Token Tester"
    )


def _make_token_str(user_id: int, hours: int = 24) -> str:
    svc = JwtService()
    token, _ = svc.create_token(user_id, hours)
    return token


def test_save_and_find_valid_token():
    with UnitOfWork() as uow:
        user = _setup_user(uow)
        token_str = _make_token_str(user.id)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        repo = TokenRepository(uow.session)
        saved = repo.save_token(token_str, user.id, expires_at)
        assert saved.id is not None
        assert saved.revoked is False
        assert saved.user_id == user.id

        found = repo.find_valid_token(token_str)
        assert found is not None
        assert found.id == saved.id


def test_find_valid_token_revoked():
    with UnitOfWork() as uow:
        user = _setup_user(uow)
        token_str = _make_token_str(user.id)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        repo = TokenRepository(uow.session)
        repo.save_token(token_str, user.id, expires_at)
        repo.revoke_token(token_str)

        found = repo.find_valid_token(token_str)
        assert found is None, "Revoked token should not be found"


def test_find_valid_token_expired():
    with UnitOfWork() as uow:
        user = _setup_user(uow)
        token_str = _make_token_str(user.id, hours=0)
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        repo = TokenRepository(uow.session)
        repo.save_token(token_str, user.id, expires_at)

        found = repo.find_valid_token(token_str)
        assert found is None, "Expired token should not be found"


def test_revoke_token_not_found():
    with UnitOfWork() as uow:
        repo = uow.tokens
        result = repo.revoke_token("this-token-does-not-exist")
        assert result is False


def test_revoke_all_user_tokens():
    with UnitOfWork() as uow:
        user = _setup_user(uow)
        repo = TokenRepository(uow.session)

        t1 = _make_token_str(user.id)
        t2 = _make_token_str(user.id)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        repo.save_token(t1, user.id, expires_at)
        repo.save_token(t2, user.id, expires_at)

        count = repo.revoke_all_user_tokens(user.id)
        assert count == 2

        assert repo.find_valid_token(t1) is None
        assert repo.find_valid_token(t2) is None


def test_revoke_all_user_tokens_empty():
    with UnitOfWork() as uow:
        user = _setup_user(uow)
        repo = TokenRepository(uow.session)
        count = repo.revoke_all_user_tokens(user.id)
        assert count == 0


def test_delete_expired_tokens():
    with UnitOfWork() as uow:
        user = _setup_user(uow)
        repo = TokenRepository(uow.session)

        # Valid token (24h)
        valid_token = _make_token_str(user.id, 24)
        repo.save_token(valid_token, user.id,
                        datetime.now(timezone.utc) + timedelta(hours=24))

        # Expired token (-1h)
        expired_token = _make_token_str(user.id, 0)
        repo.save_token(expired_token, user.id,
                        datetime.now(timezone.utc) - timedelta(hours=1))

        deleted = repo.delete_expired_tokens()
        assert deleted >= 1

        # Valid token should still exist
        assert repo.find_valid_token(valid_token) is not None


def test_token_hash_consistency():
    h1 = TokenRepository._hash("test-token")
    h2 = TokenRepository._hash("test-token")
    expected = sha256("test-token".encode()).hexdigest()
    assert h1 == h2 == expected
    assert TokenRepository._hash("other") != h1


if __name__ == "__main__":
    test_save_and_find_valid_token()
    test_find_valid_token_revoked()
    test_find_valid_token_expired()
    test_revoke_token_not_found()
    test_revoke_all_user_tokens()
    test_revoke_all_user_tokens_empty()
    test_delete_expired_tokens()
    test_token_hash_consistency()
    print("\n>>> TODOS OS TESTES DE TOKEN REPOSITORY PASSARAM <<<")
