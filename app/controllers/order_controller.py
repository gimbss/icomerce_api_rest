from app.database.unit_of_work import UnitOfWork
from app.exceptions.base_exception import AppException
from app.exceptions.order_exception import OrderNotFoundError, InsufficientStockError


class OrderController:
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

    def create_order(self, user_id: int, items: list):
        return self._run_in_uow(lambda uow: {
            "order": self._order_to_dict(
                uow.orders.create_order(user_id=user_id, items=items)
            )
        })

    def get_order_by_id(self, order_id: int):
        return self._run_in_uow(lambda uow: {
            "order": self._order_to_dict(
                uow.orders.get_order_by_id(order_id), expected=True
            )
        })

    def get_orders_by_user_id(self, user_id: int, skip: int = 0, limit: int = 20):
        def _op(uow):
            orders, total = uow.orders.get_orders_by_user_id(user_id, skip, limit)
            return {
                "orders": [self._order_to_dict(order) for order in orders],
                "skip": skip,
                "limit": limit,
                "total": total,
            }
        return self._run_in_uow(_op)

    def delete_order(self, order_id: int):
        return self._run_in_uow(lambda uow: {
            "deleted": uow.orders.delete_order(order_id)
        })

    def update_order_status(self, order_id: int, new_status: str):
        return self._run_in_uow(lambda uow: {
            "order": self._order_to_dict(
                uow.orders.update_order_status(order_id, new_status), expected=True
            )
        })

    def _order_to_dict(self, order, expected=False):
        if not order:
            if expected:
                raise OrderNotFoundError()
            return None
        return {
            "id": order.id,
            "user_id": order.user_id,
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            "items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                }
                for item in order.items
            ],
        }
