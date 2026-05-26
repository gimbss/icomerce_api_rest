"""Tests for AuthService (business logic layer)."""
from unittest.mock import MagicMock
from app.database.unit_of_work import UnitOfWork
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    UserNotFoundError,
    EmailNotVerifiedError,
    InvalidVerificationCodeError,
    CannotDemoteLastAdminError,
)
import uuid


def _unique_email():
    return f"authsvc_{uuid.uuid4().hex[:8]}@test.com"


def _make_svc():
    """Create AuthService with a mock EmailService to avoid console output in tests."""
    mock_email = MagicMock(spec=EmailService)
    return AuthService(UnitOfWork(), email_service=mock_email)


def _verify_email(svc, email, user_id):
    """Helper to verify a user's email for testing."""
    with UnitOfWork() as uow:
        from app.models.email_verification import EmailVerification
        verification = uow.session.query(EmailVerification).filter(
            EmailVerification.user_id == user_id,
            EmailVerification.used == False,
        ).first()
        code = verification.code
    svc.verify_email(email, code)


def test_register_user_returns_user():
    svc = _make_svc()
    email = _unique_email()
    user = svc.register_user(email, "Pass@1234", "John")
    assert user.email == email
    assert user.name == "John"
    assert user.id is not None
    # Register should not return a token
    assert not hasattr(user, 'token')


def test_register_user_duplicate():
    svc = _make_svc()
    email = _unique_email()
    svc.register_user(email, "Pass@1111", "User1")
    try:
        svc.register_user(email, "Pass@2222", "User2")
        assert False, "Should raise EmailAlreadyRegisteredError"
    except EmailAlreadyRegisteredError as e:
        assert e.status_code == 409


def test_register_user_with_address():
    svc = _make_svc()
    email = _unique_email()
    user = svc.register_user(email, "Pass@1234", "User", address="Rua X, 123")
    assert user.address == "Rua X, 123"


def test_authenticate_user_success():
    svc = _make_svc()
    email = _unique_email()
    user = svc.register_user(email, "Secret@123", "Jane")
    _verify_email(svc, email, user.id)
    auth_user, token = svc.authenticate_user(email, "Secret@123")
    assert auth_user.email == email
    assert token.count(".") == 2


def test_authenticate_user_wrong_password():
    svc = _make_svc()
    email = _unique_email()
    user = svc.register_user(email, "Correct@123", "User")
    _verify_email(svc, email, user.id)
    try:
        svc.authenticate_user(email, "Wrong@1234")
        assert False
    except InvalidCredentialsError:
        pass


def test_authenticate_user_not_found():
    svc = _make_svc()
    try:
        svc.authenticate_user("ghost@test.com", "Ghost@123")
        assert False
    except InvalidCredentialsError:
        pass


def test_validate_token_success():
    svc = _make_svc()
    email = _unique_email()
    user = svc.register_user(email, "Pass@1234", "User")
    _verify_email(svc, email, user.id)
    _, token = svc.authenticate_user(email, "Pass@1234")  # login to get token
    user_id = svc.validate_token(token)
    assert user_id == user.id


def test_validate_token_invalid():
    svc = _make_svc()
    try:
        svc.validate_token("garbage.token.here")
        assert False
    except InvalidCredentialsError:
        pass


def test_update_user_profile():
    svc = _make_svc()
    email = _unique_email()
    user = svc.register_user(email, "Pass@1234", "Old Name")
    updated = svc.update_user_profile(user.id, name="New Name")
    assert updated.name == "New Name"
    assert updated.email == email  # unchanged


def test_update_user_profile_password():
    svc = _make_svc()
    email = _unique_email()
    user = svc.register_user(email, "OldPass@1", "User")
    _verify_email(svc, email, user.id)
    svc.update_user_profile(user.id, password="NewPass@1")
    # Should authenticate with new password
    svc.authenticate_user(email, "NewPass@1")
    # Old password should fail
    try:
        svc.authenticate_user(email, "OldPass@1")
        assert False
    except InvalidCredentialsError:
        pass


def test_update_user_profile_not_found():
    svc = _make_svc()
    try:
        svc.update_user_profile(99999, name="Ghost")
        assert False
    except UserNotFoundError:
        pass


def test_update_user_profile_duplicate_email():
    svc = _make_svc()
    email1 = _unique_email()
    email2 = _unique_email()
    user1 = svc.register_user(email1, "Pass@1111", "User1")
    svc.register_user(email2, "Pass@2222", "User2")
    # This should work (changing to own email is fine)
    svc.update_user_profile(user1.id, email=email1)
    # Changing to another user's email should fail
    try:
        svc.update_user_profile(user1.id, email=email2)
        assert False
    except EmailAlreadyRegisteredError:
        pass


def test_delete_user():
    svc = _make_svc()
    email = _unique_email()
    user = svc.register_user(email, "Pass@1234", "To Delete")
    _verify_email(svc, email, user.id)
    result = svc.delete_user(user.id)
    assert result is True
    try:
        svc.authenticate_user(email, "Pass@1234")
        assert False
    except (InvalidCredentialsError, EmailNotVerifiedError):
        pass


def test_delete_user_not_found():
    svc = _make_svc()
    try:
        svc.delete_user(99999)
        assert False
    except UserNotFoundError:
        pass


def test_register_user_is_not_verified():
    """New users should not be verified by default."""
    svc = _make_svc()
    email = _unique_email()
    user = svc.register_user(email, "Pass@1234", "Unverified")
    assert user.is_verified is False


def test_verify_email_success():
    """Verifying email should set is_verified to True."""
    svc = _make_svc()
    email = _unique_email()
    user = svc.register_user(email, "Pass@1234", "Verify Tester")
    assert user.is_verified is False

    _verify_email(svc, email, user.id)

    # Now user should be able to login
    auth_user, token = svc.authenticate_user(email, "Pass@1234")
    assert auth_user.is_verified is True


def test_verify_email_invalid_code():
    """Invalid verification code should raise InvalidVerificationCodeError."""
    svc = _make_svc()
    email = _unique_email()
    svc.register_user(email, "Pass@1234", "Verify Tester")
    try:
        svc.verify_email(email, "ZZZZZZ")
        assert False, "Should raise InvalidVerificationCodeError"
    except InvalidVerificationCodeError:
        pass


def test_login_unverified_user():
    """Unverified users should not be able to login."""
    svc = _make_svc()
    email = _unique_email()
    svc.register_user(email, "Pass@1234", "Unverified User")
    try:
        svc.authenticate_user(email, "Pass@1234")
        assert False, "Should raise EmailNotVerifiedError"
    except EmailNotVerifiedError:
        pass


def test_resend_verification():
    """Resending verification should create a new code."""
    svc = _make_svc()
    email = _unique_email()
    user = svc.register_user(email, "Pass@1234", "Resend Tester")
    user_id = svc.resend_verification(email)
    assert user_id == user.id


def test_resend_verification_nonexistent_email():
    """Resending verification for nonexistent email should return 0 (no error)."""
    svc = _make_svc()
    user_id = svc.resend_verification("nonexistent@test.com")
    assert user_id == 0


# -----------------------------------------------------------------------
# Role management — AuthService.update_user_role
# -----------------------------------------------------------------------

def test_update_user_role_promote_to_admin():
    """Admin can promote a customer to admin."""
    svc = _make_svc()
    email = _unique_email()
    user = svc.register_user(email, "Pass@1234", "Future Admin")
    _verify_email(svc, email, user.id)

    updated = svc.update_user_role(user.id, "admin", admin_user_id=1)
    assert updated.role == "admin"


def test_update_user_role_demote_to_customer():
    """Admin can demote another admin to customer when multiple admins exist."""
    svc = _make_svc()
    # Create two users and promote both to admin
    email1 = _unique_email()
    email2 = _unique_email()
    user1 = svc.register_user(email1, "Pass@1234", "Admin 1")
    user2 = svc.register_user(email2, "Pass@2345", "Admin 2")
    _verify_email(svc, email1, user1.id)
    _verify_email(svc, email2, user2.id)

    # Promote both to admin
    svc.update_user_role(user1.id, "admin", admin_user_id=1)
    svc.update_user_role(user2.id, "admin", admin_user_id=1)

    # Now demote user2 (there's still user1 as admin)
    updated = svc.update_user_role(user2.id, "customer", admin_user_id=user1.id)
    assert updated.role == "customer"


def test_update_user_role_cannot_demote_last_admin():
    """Cannot demote the last admin to customer."""
    svc = _make_svc()
    email = _unique_email()
    user = svc.register_user(email, "Pass@1234", "Only Admin")
    _verify_email(svc, email, user.id)

    # Promote to admin
    svc.update_user_role(user.id, "admin", admin_user_id=1)

    # Verify this is the only admin
    with UnitOfWork() as uow:
        admin_count = len(uow.users.get_admin_users())

    # Only test if this user is the sole admin
    if admin_count == 1:
        try:
            svc.update_user_role(user.id, "customer", admin_user_id=user.id)
            assert False, "Should raise CannotDemoteLastAdminError"
        except CannotDemoteLastAdminError:
            pass


def test_update_user_role_user_not_found():
    """Updating role of non-existent user should raise UserNotFoundError."""
    svc = _make_svc()
    try:
        svc.update_user_role(99999, "admin", admin_user_id=1)
        assert False, "Should raise UserNotFoundError"
    except UserNotFoundError:
        pass


if __name__ == "__main__":
    test_register_user_returns_user()
    test_register_user_duplicate()
    test_register_user_with_address()
    test_register_user_is_not_verified()
    test_authenticate_user_success()
    test_authenticate_user_wrong_password()
    test_authenticate_user_not_found()
    test_login_unverified_user()
    test_verify_email_success()
    test_verify_email_invalid_code()
    test_validate_token_success()
    test_validate_token_invalid()
    test_update_user_profile()
    test_update_user_profile_password()
    test_update_user_profile_not_found()
    test_update_user_profile_duplicate_email()
    test_delete_user()
    test_delete_user_not_found()
    test_resend_verification()
    test_resend_verification_nonexistent_email()
    print("\n>>> TODOS OS TESTES DO AUTH SERVICE PASSARAM <<<")
