from app.database.unit_of_work import UnitOfWork
import uuid


def _unique_email():
    return f"order_{uuid.uuid4().hex[:12]}@example.com"


def _unique_name(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_create_order():
    with UnitOfWork() as uow:
        user = uow.users.create_user(
            email=_unique_email(), password="password", name="Order Tester"
        )
        product = uow.products.create_product(
            name=_unique_name("Product"), price=9.99,
            description="A test product", category="General", stock=10
        )
        product_2 = uow.products.create_product(
            name=_unique_name("Product 2"), price=19.99,
            description="Another test product", category="General", stock=5
        )
        order = uow.orders.create_order(
            user_id=user.id,
            items=[
                {"product_id": product.id, "quantity": 2},
                {"product_id": product_2.id, "quantity": 1}
            ]
        )
        assert order.user_id == user.id
        assert len(order.items) == 2
        assert order.items[0].product_id == product.id
        assert order.items[0].quantity == 2
        assert order.items[0].unit_price == 9.99
        assert order.items[1].product_id == product_2.id
        assert order.items[1].quantity == 1
        assert order.items[1].unit_price == 19.99


def test_create_order_custom_unit_price():
    with UnitOfWork() as uow:
        user = uow.users.create_user(
            email=_unique_email(), password="pass", name="Price Tester"
        )
        product = uow.products.create_product(
            name=_unique_name("P"), price=10.0,
            description="X", category="Cat", stock=5
        )
        order = uow.orders.create_order(
            user_id=user.id,
            items=[{"product_id": product.id, "quantity": 2, "unit_price": 7.50}]
        )
        assert order.items[0].unit_price == 7.50


def test_create_order_skip_invalid_product():
    with UnitOfWork() as uow:
        user = uow.users.create_user(
            email=_unique_email(), password="pass", name="Skip Tester"
        )
        order = uow.orders.create_order(
            user_id=user.id,
            items=[{"product_id": 99999, "quantity": 1}]  # invalid product
        )
        assert len(order.items) == 0


def test_get_order_by_id():
    with UnitOfWork() as uow:
        user = uow.users.create_user(
            email=_unique_email(), password="password", name="Order Tester"
        )
        product = uow.products.create_product(
            name=_unique_name("Product"), price=9.99,
            description="A test product", category="General", stock=10
        )
        product_2 = uow.products.create_product(
            name=_unique_name("Product 2"), price=19.99,
            description="Another test product", category="General", stock=5
        )
        order = uow.orders.create_order(
            user_id=user.id,
            items=[
                {"product_id": product.id, "quantity": 2},
                {"product_id": product_2.id, "quantity": 1}
            ]
        )
        retrieved_order = uow.orders.get_order_by_id(order.id)
        assert retrieved_order.id == order.id
        assert retrieved_order.user_id == order.user_id
        assert len(retrieved_order.items) == 2
        assert retrieved_order.items[0].product_id == order.items[0].product_id
        assert retrieved_order.items[0].quantity == order.items[0].quantity
        assert retrieved_order.items[0].unit_price == order.items[0].unit_price
        assert retrieved_order.items[1].product_id == order.items[1].product_id
        assert retrieved_order.items[1].quantity == order.items[1].quantity
        assert retrieved_order.items[1].unit_price == order.items[1].unit_price


def test_get_order_by_id_not_found():
    with UnitOfWork() as uow:
        assert uow.orders.get_order_by_id(99999) is None


def test_get_orders_by_user_id_empty():
    with UnitOfWork() as uow:
        orders, total = uow.orders.get_orders_by_user_id(99999)
        assert orders == []
        assert total == 0


def test_delete_order():
    with UnitOfWork() as uow:
        user = uow.users.create_user(
            email=_unique_email(), password="password", name="Order Tester"
        )
        product = uow.products.create_product(
            name=_unique_name("Product"), price=9.99,
            description="A test product", category="General", stock=10
        )
        product_2 = uow.products.create_product(
            name=_unique_name("Product 2"), price=19.99,
            description="Another test product", category="General", stock=5
        )
        order = uow.orders.create_order(
            user_id=user.id,
            items=[
                {"product_id": product.id, "quantity": 2},
                {"product_id": product_2.id, "quantity": 1}
            ]
        )
        deleted = uow.orders.delete_order(order.id)
        assert deleted
        assert uow.orders.get_order_by_id(order.id) is None


def test_delete_order_not_found():
    with UnitOfWork() as uow:
        assert uow.orders.delete_order(99999) is False


def test_create_order_deducts_stock():
    """Stock should be deducted when an order is created."""
    with UnitOfWork() as uow:
        user = uow.users.create_user(
            email=_unique_email(), password="password", name="Stock Tester"
        )
        product = uow.products.create_product(
            name=_unique_name("Product"), price=9.99,
            description="A test product", category="General", stock=10
        )
        uow.orders.create_order(
            user_id=user.id,
            items=[{"product_id": product.id, "quantity": 3}]
        )
        # Refresh product from DB
        updated_product = uow.products.get_product_by_id(product.id)
        assert updated_product.stock == 7  # 10 - 3


def test_create_order_deducts_stock_multiple_items():
    """Stock should be deducted for each item in the order."""
    with UnitOfWork() as uow:
        user = uow.users.create_user(
            email=_unique_email(), password="password", name="Stock Tester"
        )
        p1 = uow.products.create_product(
            name=_unique_name("P1"), price=10.0,
            description="Product 1", category="General", stock=20
        )
        p2 = uow.products.create_product(
            name=_unique_name("P2"), price=15.0,
            description="Product 2", category="General", stock=10
        )
        uow.orders.create_order(
            user_id=user.id,
            items=[
                {"product_id": p1.id, "quantity": 5},
                {"product_id": p2.id, "quantity": 3},
            ]
        )
        updated_p1 = uow.products.get_product_by_id(p1.id)
        updated_p2 = uow.products.get_product_by_id(p2.id)
        assert updated_p1.stock == 15  # 20 - 5
        assert updated_p2.stock == 7   # 10 - 3


def test_create_order_insufficient_stock():
    """Should raise InsufficientStockError when stock is insufficient."""
    from app.exceptions.order_exception import InsufficientStockError
    with UnitOfWork() as uow:
        user = uow.users.create_user(
            email=_unique_email(), password="password", name="Stock Tester"
        )
        product = uow.products.create_product(
            name=_unique_name("Product"), price=9.99,
            description="A test product", category="General", stock=5
        )
        try:
            uow.orders.create_order(
                user_id=user.id,
                items=[{"product_id": product.id, "quantity": 10}]
            )
            assert False, "Should have raised InsufficientStockError"
        except InsufficientStockError as e:
            assert e.status_code == 400
            assert product.name in str(e)
            assert e.available == 5
            assert e.requested == 10


def test_create_order_default_unit_price():
    """When unit_price is not provided, product price should be used."""
    with UnitOfWork() as uow:
        user = uow.users.create_user(
            email=_unique_email(), password="password", name="Price Tester"
        )
        product = uow.products.create_product(
            name=_unique_name("Product"), price=25.99,
            description="A test product", category="General", stock=10
        )
        order = uow.orders.create_order(
            user_id=user.id,
            items=[{"product_id": product.id, "quantity": 2}]
        )
        assert order.items[0].unit_price == 25.99  # Uses product price


def test_create_order_custom_unit_price():
    """When unit_price is provided, it should override product price."""
    with UnitOfWork() as uow:
        user = uow.users.create_user(
            email=_unique_email(), password="password", name="Price Tester"
        )
        product = uow.products.create_product(
            name=_unique_name("Product"), price=25.99,
            description="A test product", category="General", stock=10
        )
        order = uow.orders.create_order(
            user_id=user.id,
            items=[{"product_id": product.id, "quantity": 2, "unit_price": 19.99}]
        )
        assert order.items[0].unit_price == 19.99  # Uses custom price


def test_delete_order_restores_stock():
    """Stock should be restored when an order is deleted."""
    with UnitOfWork() as uow:
        user = uow.users.create_user(
            email=_unique_email(), password="password", name="Stock Tester"
        )
        product = uow.products.create_product(
            name=_unique_name("Product"), price=9.99,
            description="A test product", category="General", stock=10
        )
        order = uow.orders.create_order(
            user_id=user.id,
            items=[{"product_id": product.id, "quantity": 3}]
        )
        # Stock was deducted
        updated_product = uow.products.get_product_by_id(product.id)
        assert updated_product.stock == 7  # 10 - 3

        # Delete order restores stock
        uow.orders.delete_order(order.id)
        restored_product = uow.products.get_product_by_id(product.id)
        assert restored_product.stock == 10  # Restored to original


if __name__ == "__main__":
    test_create_order()
    test_create_order_custom_unit_price()
    test_create_order_skip_invalid_product()
    test_get_order_by_id()
    test_get_order_by_id_not_found()
    test_get_orders_by_user_id_empty()
    test_delete_order()
    test_delete_order_not_found()
    test_create_order_deducts_stock()
    test_create_order_deducts_stock_multiple_items()
    test_create_order_insufficient_stock()
    test_create_order_default_unit_price()
    test_create_order_custom_unit_price()
    test_delete_order_restores_stock()
    test_delete_order_not_found()
    print("\n>>> TODOS OS TESTES DE ORDER REPOSITORY PASSARAM <<<")