from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hcp_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hcp_specialty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="structured")
    sentiment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Logged")
    follow_up_date: Mapped[str | None] = mapped_column(String(50), nullable=True)

    interaction_type: Mapped[str] = mapped_column(String(50), default="Meeting")
    interaction_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    interaction_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # JSON-encoded list[str], kept as Text for MySQL/Postgres/SQLite portability
    attendees: Mapped[str | None] = mapped_column(Text, nullable=True)
    materials_shared: Mapped[str | None] = mapped_column(Text, nullable=True)
    samples_distributed: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcomes: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_actions: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
