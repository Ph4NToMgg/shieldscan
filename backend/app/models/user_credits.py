"""User credits model for tracking scan usage."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserCredits(Base):
    """Tracks scan credits for authenticated users."""

    __tablename__ = "user_credits"

    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    credits_remaining: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    credits_total: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
