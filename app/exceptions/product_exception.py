from .base_exception import AppException


class ProductException(AppException):
    """Base exception for product-related errors."""
    pass


class ProductNotFoundError(ProductException):
    def __init__(self, product_id: int = None):
        super().__init__(
            message="Product not found",
            status_code=404,
        )
        self.product_id = product_id


class ProductHasOrdersError(ProductException):
    def __init__(self, product_id: int = None):
        super().__init__(
            message="Cannot delete product: it is referenced by existing orders",
            status_code=409,
        )
        self.product_id = product_id
