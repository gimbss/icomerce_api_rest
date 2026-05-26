from datetime import datetime, timezone

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.exceptions.order_exception import InsufficientStockError, InvalidOrderStatusError

VALID_ORDER_STATUSES = ("pending", "confirmed", "shipped", "delivered", "cancelled")


class OrderRepository:
    def __init__(self, session):
        self.session = session

    def get_order_by_id(self, order_id):
        order = self.session.query(Order).filter(Order.id == order_id).first()
        return order

    def create_order(self, user_id, items):
        new_order = Order(user_id=user_id)
        self.session.add(new_order)
        self.session.flush()

        for item in items:
            product = self.session.query(Product).filter(Product.id == item['product_id']).first()
            if not product:
                continue

            quantity = item['quantity']

            if product.stock < quantity:
                raise InsufficientStockError(
                    product_name=product.name,
                    available=product.stock,
                    requested=quantity,
                )

            product.stock -= quantity

            unit_price = item.get('unit_price', product.price)

            order_item = OrderItem(
                quantity=quantity,
                unit_price=unit_price,
            )
            order_item.product = product
            order_item.order = new_order
            self.session.add(order_item)

        self.session.flush()
        return new_order

    def get_orders_by_user_id(self, user_id, skip: int = 0, limit: int = 20):
        total = self.session.query(Order).filter(Order.user_id == user_id).count()
        orders = self.session.query(Order).filter(Order.user_id == user_id).offset(skip).limit(limit).all()
        return orders, total

    def update_order_status(self, order_id, new_status):
        order = self.get_order_by_id(order_id)
        if not order:
            return None

        if new_status not in VALID_ORDER_STATUSES:
            raise InvalidOrderStatusError(new_status)

        old_status = order.status

        # If cancelling, restore stock
        if new_status == "cancelled" and old_status != "cancelled":
            for item in order.items:
                product = self.session.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    product.stock += item.quantity

        order.status = new_status
        order.updated_at = datetime.now(timezone.utc)
        self.session.add(order)
        return order

    def delete_order(self, order_id):
        order = self.get_order_by_id(order_id)
        if not order:
            return False

        for item in order.items:
            product = self.session.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock += item.quantity

        self.session.delete(order)
        self.session.flush()
        return True