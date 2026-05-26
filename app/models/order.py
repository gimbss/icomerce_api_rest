from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship(
        'User',
        back_populates='orders'
    )

    items = relationship(
        'OrderItem',
        back_populates='order',
        cascade='all, delete-orphan'
    )

    def __str__(self):
        items_info = ', '.join(
            f'{item.product.name} x{item.quantity}' for item in self.items
        )
        return f'Order #{self.id} | User: {self.user.name} | Status: {self.status} | Items: [{items_info}]'

    def __repr__(self):
        return f'Order(id={self.id!r}, user_id={self.user_id!r}, status={self.status!r}, items_count={len(self.items)})'