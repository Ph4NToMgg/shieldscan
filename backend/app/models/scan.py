import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ScanResult(Base):
    """Stores the result of a website security scan."""

    __tablename__ = "scan_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    results: Mapped[dict] = mapped_column(JSON, nullable=False)
    ai_summary: Mapped[str] = mapped_column(Text, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> dict:
        """Serialize the model to a dictionary."""
        return {
            "id": str(self.id),
            "url": self.url,
            "score": self.score,
            "results": self.results,
            "ai_summary": self.ai_summary,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
        }
