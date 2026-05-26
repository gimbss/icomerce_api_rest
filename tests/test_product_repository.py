from app.database.unit_of_work import UnitOfWork
import uuid


def _unique_product_name(prefix="Prod"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_create_product():
    name = _unique_product_name()
    with UnitOfWork() as uow:
        product = uow.products.create_product(
            name=name, description="A test product",
            price=9.99, category="General", stock=10
        )
        assert product.name == name
        assert product.price == 9.99
        assert product.description == "A test product"
        assert product.category == "General"
        assert product.stock == 10


def test_create_product_no_description():
    name = _unique_product_name()
    with UnitOfWork() as uow:
        product = uow.products.create_product(
            name=name, description=None,
            price=5.0, category="Test", stock=0
        )
        assert product.description is None


def test_get_product_by_id():
    name = _unique_product_name()
    with UnitOfWork() as uow:
        product = uow.products.create_product(
            name=name, description="A test product",
            price=9.99, category="General", stock=10
        )
        retrieved_product = uow.products.get_product_by_id(product.id)
        assert retrieved_product.id == product.id
        assert retrieved_product.name == product.name
        assert retrieved_product.price == product.price
        assert retrieved_product.description == product.description
        assert retrieved_product.category == product.category
        assert retrieved_product.stock == product.stock


def test_get_product_by_id_not_found():
    with UnitOfWork() as uow:
        assert uow.products.get_product_by_id(99999) is None


def test_update_product():
    name = _unique_product_name()
    updated_name = _unique_product_name("Updated")
    with UnitOfWork() as uow:
        product = uow.products.create_product(
            name=name, description="A test product",
            price=9.99, category="General", stock=10
        )
        updated_product = uow.products.update_product(
            product.id, name=updated_name, price=19.99
        )
        assert updated_product.name == updated_name
        assert updated_product.price == 19.99
        assert updated_product.description == "A test product"


def test_update_product_not_found():
    with UnitOfWork() as uow:
        assert uow.products.update_product(99999, name="Ghost") is None


def test_delete_product():
    name = _unique_product_name()
    with UnitOfWork() as uow:
        product = uow.products.create_product(
            name=name, description="A test product",
            price=9.99, category="General", stock=10
        )
        deleted = uow.products.delete_product(product.id)
        assert deleted is True
        assert uow.products.get_product_by_id(product.id) is None


def test_delete_product_not_found():
    with UnitOfWork() as uow:
        assert uow.products.delete_product(99999) is False


if __name__ == "__main__":
    test_create_product()
    test_create_product_no_description()
    test_get_product_by_id()
    test_get_product_by_id_not_found()
    test_update_product()
    test_update_product_not_found()
    test_delete_product()
    test_delete_product_not_found()
    print("\n>>> TODOS OS TESTES DE PRODUCT REPOSITORY PASSARAM <<<")