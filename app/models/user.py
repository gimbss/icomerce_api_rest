from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False
    )

    address: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20),
        default="customer",
        nullable=False
    )

    orders = relationship(
        'Order',
        back_populates='user'
    )

    tokens = relationship(
        'Token',
        back_populates='user',
        cascade='all, delete-orphan'
    )

    email_verifications = relationship(
        'EmailVerification',
        back_populates='user',
        cascade='all, delete-orphan'
    )

    def __str__(self):
        return f'ID: {self.id}, Email: {self.email}, Name: {self.name}, Verified: {self.is_verified}'

    def __repr__(self):
        return f'User(id={self.id!r}, email={self.email!r}, is_verified={self.is_verified!r})'