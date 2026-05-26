from sqlalchemy import Integer, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class OrderItem(Base):
    __tablename__ = 'order_items'

    id: Mapped[int] = mapped_column(primary_key=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey('orders.id')
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey('products.id')
    )

    quantity: Mapped[int] = mapped_column(
        Integer
    )

    unit_price: Mapped[float] = mapped_column(
        Float
    )

    order = relationship(
        'Order',
        back_populates='items'
    )

    product = relationship(
        'Product',
        back_populates='items'
    )

    def __str__(self):
        return f'OrderItem #{self.id} | Product: {self.product.name} | Qty: {self.quantity} | Unit: {self.unit_price}'

    def __repr__(self):
        return f'OrderItem(id={self.id!r}, product_id={self.product_id!r}, quantity={self.quantity!r})'