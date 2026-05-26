from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Token(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(primary_key=True)

    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    revoked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    user = relationship("User", back_populates="tokens")

    def __repr__(self):
        return (
            f"Token(id={self.id!r}, user_id={self.user_id!r}, "
            f"revoked={self.revoked!r})"
        )
