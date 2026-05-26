from app.database.unit_of_work import UnitOfWork
from app.controllers.product_controller import ProductController
import uuid


def _unique_name(prefix="Prod"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_create_product():
    name = _unique_name()
    with UnitOfWork() as uow:
        ctrl = ProductController(uow)
        resp = ctrl.create_product(
            name=name, description="Test description",
            price=29.90, category="Electronics", stock=50
        )
        assert resp["status"] == "success", resp
        assert resp["product"]["name"] == name
        assert resp["product"]["price"] == 29.90
        assert resp["product"]["description"] == "Test description"
        assert resp["product"]["category"] == "Electronics"
        assert resp["product"]["stock"] == 50
        assert "id" in resp["product"]


def test_get_product_by_id():
    name = _unique_name()
    with UnitOfWork() as uow:
        ctrl = ProductController(uow)
        created = ctrl.create_product(
            name=name, description="Test", price=15.0,
            category="Books", stock=10
        )
        pid = created["product"]["id"]

        resp = ctrl.get_product_by_id(pid)
        assert resp["status"] == "success", resp
        assert resp["product"]["id"] == pid
        assert resp["product"]["name"] == name
        assert resp["product"]["price"] == 15.0


def test_get_product_by_id_not_found():
    with UnitOfWork() as uow:
        ctrl = ProductController(uow)
        resp = ctrl.get_product_by_id(99999)
        assert resp["status"] == "error"
        assert resp["message"] == "Product not found"


def test_update_product():
    name = _unique_name()
    updated_name = _unique_name("Updated")
    with UnitOfWork() as uow:
        ctrl = ProductController(uow)
        created = ctrl.create_product(
            name=name, description="Original", price=10.0,
            category="Toys", stock=5
        )
        pid = created["product"]["id"]

        resp = ctrl.update_product(pid, name=updated_name, price=25.0)
        assert resp["status"] == "success", resp
        assert resp["product"]["name"] == updated_name
        assert resp["product"]["price"] == 25.0
        assert resp["product"]["description"] == "Original"  # kept unchanged
        assert resp["product"]["category"] == "Toys"
        assert resp["product"]["stock"] == 5


def test_update_product_not_found():
    with UnitOfWork() as uow:
        ctrl = ProductController(uow)
        resp = ctrl.update_product(99999, name="Ghost")
        assert resp["status"] == "error"
        assert resp["message"] == "Product not found"


def test_delete_product():
    name = _unique_name()
    with UnitOfWork() as uow:
        ctrl = ProductController(uow)
        created = ctrl.create_product(
            name=name, description="To delete", price=5.0,
            category="Misc", stock=1
        )
        pid = created["product"]["id"]

        resp = ctrl.delete_product(pid)
        assert resp["status"] == "success", resp
        assert resp["deleted"] is True

        # confirm it's gone
        lookup = ctrl.get_product_by_id(pid)
        assert lookup["status"] == "error"


def test_delete_product_not_found():
    with UnitOfWork() as uow:
        ctrl = ProductController(uow)
        resp = ctrl.delete_product(99999)
        assert resp["status"] == "success", resp
        assert resp["deleted"] is False


if __name__ == "__main__":
    test_create_product()
    test_get_product_by_id()
    test_get_product_by_id_not_found()
    test_update_product()
    test_update_product_not_found()
    test_delete_product()
    test_delete_product_not_found()
    print("\n>>> TODOS OS TESTES DO PRODUCT CONTROLLER PASSARAM <<<")
