from app.database.unit_of_work import UnitOfWork
from app.exceptions.base_exception import AppException
from app.exceptions.product_exception import ProductNotFoundError


class ProductController:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _run_in_uow(self, operation):
        try:
            with self.uow as uow:
                result = operation(uow)
            return {"status": "success", **result}
        except AppException as e:
            return {"status": "error", "code": e.status_code, "message": e.message}
        except ValueError as e:
            return {"status": "error", "code": 400, "message": str(e)}
        except Exception:
            return {"status": "error", "code": 500, "message": "Internal server error"}

    def create_product(self, name: str, description: str, price: float, category: str, stock: int):
        return self._run_in_uow(lambda uow: {
            "product": self._product_to_dict(
                uow.products.create_product(
                    name=name, description=description,
                    price=price, category=category, stock=stock
                )
            )
        })

    def get_product_by_id(self, product_id: int):
        return self._run_in_uow(lambda uow: {
            "product": self._product_to_dict(
                uow.products.get_product_by_id(product_id), expected=True
            )
        })
    
    def get_products_by_category(self, category: str, skip: int = 0, limit: int = 20):
        def _op(uow):
            products, total = uow.products.get_products_by_category(category, skip, limit)
            return {
                "products": [self._product_to_dict(p) for p in products],
                "skip": skip,
                "limit": limit,
                "total": total,
            }
        return self._run_in_uow(_op)

    def update_product(self, product_id: int, name: str = None, description: str = None,
                       price: float = None, category: str = None, stock: int = None):
        return self._run_in_uow(lambda uow: {
            "product": self._product_to_dict(
                uow.products.update_product(
                    product_id, name=name, description=description,
                    price=price, category=category, stock=stock
                ), expected=True
            )
        })

    def list_products(self, skip: int = 0, limit: int = 20):
        def _op(uow):
            products, total = uow.products.list_products(skip, limit)
            return {
                "products": [self._product_to_dict(p) for p in products],
                "skip": skip,
                "limit": limit,
                "total": total,
            }
        return self._run_in_uow(_op)

    def delete_product(self, product_id: int):
        return self._run_in_uow(lambda uow: {
            "deleted": uow.products.delete_product(product_id)
        })

    def _product_to_dict(self, product, expected=False):
        if not product:
            if expected:
                raise ProductNotFoundError()
            return None
        return {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "category": product.category,
            "stock": product.stock,
        }