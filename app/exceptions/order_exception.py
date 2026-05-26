from .base_exception import AppException


class OrderException(AppException):
    """Base exception for order-related errors."""
    pass


class OrderNotFoundError(OrderException):
    def __init__(self, order_id: int = None):
        super().__init__(
            message="Order not found",
            status_code=404,
        )
        self.order_id = order_id


class InsufficientStockError(OrderException):
    def __init__(self, product_name: str = None, available: int = 0, requested: int = 0):
        super().__init__(
            message=f"Insufficient stock for product '{product_name}': available {available}, requested {requested}",
            status_code=400,
        )
        self.product_name = product_name
        self.available = available
        self.requested = requested


class InvalidOrderStatusError(OrderException):
    def __init__(self, status: str = None):
        super().__init__(
            message=f"Invalid order status: '{status}'. Valid statuses: pending, confirmed, shipped, delivered, cancelled",
            status_code=400,
        )
        self.status = status
