"""Test exception hierarchy and custom behavior."""
from app.exceptions.base_exception import AppException
from app.exceptions import (
    AuthException,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    UserNotFoundError,
    ProductException,
    ProductNotFoundError,
    OrderException,
    OrderNotFoundError,
    InsufficientStockError,
)


def test_app_exception_defaults():
    e = AppException()
    assert str(e) == "An error occurred"
    assert e.status_code == 400


def test_app_exception_custom():
    e = AppException("Custom error", 418)
    assert str(e) == "Custom error"
    assert e.status_code == 418


def test_auth_hierarchy():
    assert issubclass(EmailAlreadyRegisteredError, AuthException)
    assert issubclass(InvalidCredentialsError, AuthException)
    assert issubclass(UserNotFoundError, AuthException)
    assert issubclass(AuthException, AppException)


def test_product_hierarchy():
    assert issubclass(ProductNotFoundError, ProductException)
    assert issubclass(ProductException, AppException)


def test_order_hierarchy():
    assert issubclass(OrderNotFoundError, OrderException)
    assert issubclass(OrderException, AppException)


def test_email_already_registered():
    e = EmailAlreadyRegisteredError("user@test.com")
    assert str(e) == "Email already registered"
    assert e.status_code == 409
    assert e.email == "user@test.com"


def test_invalid_credentials_default():
    e = InvalidCredentialsError()
    assert str(e) == "Invalid email or password"
    assert e.status_code == 401


def test_invalid_credentials_custom():
    e = InvalidCredentialsError("Token expired")
    assert str(e) == "Token expired"
    assert e.status_code == 401


def test_user_not_found():
    e = UserNotFoundError(42)
    assert str(e) == "User not found"
    assert e.status_code == 404
    assert e.user_id == 42


def test_user_not_found_default():
    e = UserNotFoundError()
    assert e.user_id is None


def test_product_not_found():
    e = ProductNotFoundError(10)
    assert str(e) == "Product not found"
    assert e.status_code == 404
    assert e.product_id == 10


def test_order_not_found():
    e = OrderNotFoundError(5)
    assert str(e) == "Order not found"
    assert e.status_code == 404
    assert e.order_id == 5


def test_insufficient_stock_error():
    e = InsufficientStockError("Widget", available=5, requested=10)
    assert "Widget" in str(e)
    assert "5" in str(e)
    assert "10" in str(e)
    assert e.status_code == 400
    assert e.product_name == "Widget"
    assert e.available == 5
    assert e.requested == 10


def test_insufficient_stock_hierarchy():
    assert issubclass(InsufficientStockError, OrderException)
    assert issubclass(InsufficientStockError, AppException)


if __name__ == "__main__":
    test_app_exception_defaults()
    test_app_exception_custom()
    test_auth_hierarchy()
    test_product_hierarchy()
    test_order_hierarchy()
    test_email_already_registered()
    test_invalid_credentials_default()
    test_invalid_credentials_custom()
    test_user_not_found()
    test_user_not_found_default()
    test_product_not_found()
    test_order_not_found()
    test_insufficient_stock_error()
    test_insufficient_stock_hierarchy()
    test_product_not_found()
    test_order_not_found()
    print("\n>>> TODOS OS TESTES DE EXCEPTIONS PASSARAM <<<")
