from app.database.unit_of_work import UnitOfWork

import uuid


def _unique_email():
    return f"user_{uuid.uuid4().hex[:12]}@example.com"


def test_create_user():
    email = _unique_email()
    with UnitOfWork() as uow:
        user = uow.users.create_user(email=email, password="password", name="Test User")
        assert user.email == email
        assert user.name == "Test User"
        assert user.password == "password"


def test_create_user_with_address():
    email = _unique_email()
    with UnitOfWork() as uow:
        user = uow.users.create_user(email=email, password="pass", name="Addr User", address="Rua ABC, 123")
        assert user.address == "Rua ABC, 123"


def test_get_user_by_id():
    email = _unique_email()
    with UnitOfWork() as uow:
        user = uow.users.create_user(email=email, password="password", name="Test User")
        retrieved_user = uow.users.get_user_by_id(user.id)
        assert retrieved_user.id == user.id
        assert retrieved_user.email == user.email
        assert retrieved_user.name == user.name


def test_get_user_by_id_not_found():
    with UnitOfWork() as uow:
        assert uow.users.get_user_by_id(99999) is None


def test_get_user_by_email():
    email = _unique_email()
    with UnitOfWork() as uow:
        uow.users.create_user(email=email, password="pass", name="Email Test")
        found = uow.users.get_user_by_email(email)
        assert found is not None
        assert found.email == email
        assert uow.users.get_user_by_email("ghost@test.com") is None


def test_update_user():
    email = _unique_email()
    updated_email = f"updated_{uuid.uuid4().hex}@example.com"
    with UnitOfWork() as uow:
        user = uow.users.create_user(email=email, password="password", name="Test User")
        updated_user = uow.users.update_user(user.id, email=updated_email, name="Updated User")
        assert updated_user.email == updated_email
        assert updated_user.name == "Updated User"


def test_update_user_not_found():
    with UnitOfWork() as uow:
        assert uow.users.update_user(99999, name="Ghost") is None


def test_delete_user():
    email = _unique_email()
    with UnitOfWork() as uow:
        user = uow.users.create_user(email=email, password="password", name="Test User")
        deleted = uow.users.delete_user(user.id)
        assert deleted is True
        assert uow.users.get_user_by_id(user.id) is None


def test_delete_user_not_found():
    with UnitOfWork() as uow:
        assert uow.users.delete_user(99999) is False


if __name__ == "__main__":
    test_create_user()
    test_create_user_with_address()
    test_get_user_by_id()
    test_get_user_by_id_not_found()
    test_get_user_by_email()
    test_update_user()
    test_update_user_not_found()
    test_delete_user()
    test_delete_user_not_found()