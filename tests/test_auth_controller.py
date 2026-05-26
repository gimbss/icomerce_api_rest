from unittest.mock import MagicMock
from app.database.unit_of_work import UnitOfWork
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.controllers.auth_controller import AuthController
import uuid


def _unique_email():
    return f"auth_{uuid.uuid4().hex[:8]}@test.com"


def _make_ctrl():
    uow = UnitOfWork()
    mock_email = MagicMock(spec=EmailService)
    service = AuthService(uow, email_service=mock_email)
    return AuthController(service)


def _verify_email_ctrl(ctrl, email, user_id):
    """Helper to verify a user's email for testing."""
    with UnitOfWork() as uow:
        from app.models.email_verification import EmailVerification
        verification = uow.session.query(EmailVerification).filter(
            EmailVerification.user_id == user_id,
            EmailVerification.used == False,
        ).first()
        code = verification.code
    ctrl.verify_email(email, code)


def test_register_user():
    email = _unique_email()
    ctrl = _make_ctrl()
    resp = ctrl.register_user(email, "Secret@123", "John Doe")
    assert resp["status"] == "success", resp
    assert "user_id" in resp
    assert isinstance(resp["user_id"], int)


def test_register_user_duplicate_email():
    email = _unique_email()
    ctrl = _make_ctrl()
    resp1 = ctrl.register_user(email, "Secret@111", "John")
    assert resp1["status"] == "success"

    resp2 = ctrl.register_user(email, "Other@4567", "John Copy")
    assert resp2["status"] == "error"
    assert resp2["message"] == "Email already registered"


def test_authenticate_user():
    email = _unique_email()
    ctrl = _make_ctrl()
    reg = ctrl.register_user(email, "MyPass@123", "Jane Doe")
    _verify_email_ctrl(ctrl, email, reg["user_id"])

    resp = ctrl.authenticate_user(email, "MyPass@123")
    assert resp["status"] == "success", resp
    assert "user_id" in resp


def test_authenticate_user_wrong_password():
    email = _unique_email()
    ctrl = _make_ctrl()
    reg = ctrl.register_user(email, "Correct@123", "User")
    _verify_email_ctrl(ctrl, email, reg["user_id"])

    resp = ctrl.authenticate_user(email, "Wrong@1234")
    assert resp["status"] == "error"
    assert resp["message"] == "Invalid email or password"


def test_authenticate_user_not_found():
    ctrl = _make_ctrl()
    resp = ctrl.authenticate_user("ghost@test.com", "Ghost@123")
    assert resp["status"] == "error"
    assert resp["message"] == "Invalid email or password"


def test_update_user_profile():
    email = _unique_email()
    ctrl = _make_ctrl()
    reg = ctrl.register_user(email, "Pass@1234", "Old Name")
    uid = reg["user_id"]

    resp = ctrl.update_user_profile(uid, name="New Name")
    assert resp["status"] == "success", resp
    assert resp["user_id"] == uid


def test_update_user_profile_duplicate_email():
    email1 = _unique_email()
    email2 = _unique_email()
    ctrl = _make_ctrl()
    reg1 = ctrl.register_user(email1, "Pass@1111", "User 1")
    reg2 = ctrl.register_user(email2, "Pass@2222", "User 2")
    _verify_email_ctrl(ctrl, email1, reg1["user_id"])
    _verify_email_ctrl(ctrl, email2, reg2["user_id"])

    # try to change user2 email to user1 email
    resp = ctrl.authenticate_user(email2, "Pass@2222")
    uid2 = resp["user_id"]
    resp2 = ctrl.update_user_profile(uid2, email=email1)
    assert resp2["status"] == "error"
    assert resp2["message"] == "Email already registered"


def test_update_user_profile_not_found():
    ctrl = _make_ctrl()
    resp = ctrl.update_user_profile(99999, name="Ghost")
    assert resp["status"] == "error"
    assert resp["message"] == "User not found"


def test_delete_user():
    email = _unique_email()
    ctrl = _make_ctrl()
    reg = ctrl.register_user(email, "Delete@123", "To Delete")
    uid = reg["user_id"]
    _verify_email_ctrl(ctrl, email, uid)

    resp = ctrl.delete_user(uid)
    assert resp["status"] == "success", resp
    assert resp["deleted"] is True

    # confirm auth fails
    auth = ctrl.authenticate_user(email, "Delete@123")
    assert auth["status"] == "error"


def test_delete_user_not_found():
    ctrl = _make_ctrl()
    resp = ctrl.delete_user(99999)
    assert resp["status"] == "error"
    assert resp["message"] == "User not found"


if __name__ == "__main__":
    test_register_user()
    test_register_user_duplicate_email()
    test_authenticate_user()
    test_authenticate_user_wrong_password()
    test_authenticate_user_not_found()
    test_update_user_profile()
    test_update_user_profile_duplicate_email()
    test_update_user_profile_not_found()
    test_delete_user()
    test_delete_user_not_found()
    print("\n>>> TODOS OS TESTES DO AUTH CONTROLLER PASSARAM <<<")
