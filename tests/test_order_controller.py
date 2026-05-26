from app.database.unit_of_work import UnitOfWork
from app.controllers.order_controller import OrderController
import uuid


def _unique_email():
    return f"ord_ctrl_{uuid.uuid4().hex[:8]}@test.com"


def _unique_name(prefix="Prod"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _setup_user_and_products(uow):
    user = uow.users.create_user(
        email=_unique_email(), password="123", name="Tester"
    )
    p1 = uow.products.create_product(
        name=_unique_name("P1"), price=29.90,
        description="First", category="CatA", stock=10
    )
    p2 = uow.products.create_product(
        name=_unique_name("P2"), price=9.90,
        description="Second", category="CatB", stock=20
    )
    return user, p1, p2


def test_create_order():
    with UnitOfWork() as uow:
        user, p1, p2 = _setup_user_and_products(uow)
        ctrl = OrderController(uow)
        resp = ctrl.create_order(user.id, [
            {"product_id": p1.id, "quantity": 3},
            {"product_id": p2.id, "quantity": 2},
        ])
        assert resp["status"] == "success", resp
        assert len(resp["order"]["items"]) == 2
        assert resp["order"]["items"][0]["quantity"] == 3
        assert resp["order"]["items"][0]["unit_price"] == 29.90
        assert resp["order"]["items"][1]["quantity"] == 2
        assert resp["order"]["items"][1]["unit_price"] == 9.90
        assert resp["order"]["user_id"] == user.id
        assert "id" in resp["order"]


def test_get_order_by_id():
    with UnitOfWork() as uow:
        user, p1, p2 = _setup_user_and_products(uow)
        ctrl = OrderController(uow)
        created = ctrl.create_order(user.id, [
            {"product_id": p1.id, "quantity": 1},
            {"product_id": p2.id, "quantity": 4},
        ])
        oid = created["order"]["id"]

        resp = ctrl.get_order_by_id(oid)
        assert resp["status"] == "success", resp
        assert resp["order"]["id"] == oid
        assert len(resp["order"]["items"]) == 2
        assert resp["order"]["items"][0]["product_id"] == p1.id


def test_get_order_by_id_not_found():
    with UnitOfWork() as uow:
        ctrl = OrderController(uow)
        resp = ctrl.get_order_by_id(99999)
        assert resp["status"] == "error"
        assert resp["message"] == "Order not found"


def test_get_orders_by_user_id():
    with UnitOfWork() as uow:
        user, p1, p2 = _setup_user_and_products(uow)
        ctrl = OrderController(uow)
        ctrl.create_order(user.id, [{"product_id": p1.id, "quantity": 1}])
        ctrl.create_order(user.id, [{"product_id": p2.id, "quantity": 2}])

        resp = ctrl.get_orders_by_user_id(user.id)
        assert resp["status"] == "success", resp
        assert len(resp["orders"]) >= 2


def test_get_orders_by_user_id_empty():
    with UnitOfWork() as uow:
        user, _, _ = _setup_user_and_products(uow)
        ctrl = OrderController(uow)
        resp = ctrl.get_orders_by_user_id(user.id)
        assert resp["status"] == "success", resp
        assert resp["orders"] == []


def test_delete_order():
    with UnitOfWork() as uow:
        user, p1, p2 = _setup_user_and_products(uow)
        ctrl = OrderController(uow)
        created = ctrl.create_order(user.id, [
            {"product_id": p1.id, "quantity": 2},
            {"product_id": p2.id, "quantity": 1},
        ])
        oid = created["order"]["id"]

        resp = ctrl.delete_order(oid)
        assert resp["status"] == "success", resp
        assert resp["deleted"] is True

        # confirm it's gone
        lookup = ctrl.get_order_by_id(oid)
        assert lookup["status"] == "error"


def test_delete_order_not_found():
    with UnitOfWork() as uow:
        ctrl = OrderController(uow)
        resp = ctrl.delete_order(99999)
        assert resp["status"] == "success", resp
        assert resp["deleted"] is False


if __name__ == "__main__":
    test_create_order()
    test_get_order_by_id()
    test_get_order_by_id_not_found()
    test_get_orders_by_user_id()
    test_get_orders_by_user_id_empty()
    test_delete_order()
    test_delete_order_not_found()
    print("\n>>> TODOS OS TESTES DO ORDER CONTROLLER PASSARAM <<<")
