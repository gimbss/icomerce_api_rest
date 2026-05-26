from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )

    price: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    items = relationship(
        'OrderItem',
        back_populates='product',
        passive_deletes=True
    )

    def __str__(self):
        return f'ID: {self.id}, Name: {self.name}, Price: {self.price}, Category: {self.category}, Stock: {self.stock}'

    def __repr__(self):
        return f'Product(id={self.id!r}, name={self.name!r})'