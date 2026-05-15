from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AsinSnapshot(Base):
    __tablename__ = 'asins'
    __table_args__ = (
        Index('idx_asins_eligible', 'eligible'),
        Index('idx_asins_roi', 'computed_roi_pct'),
        Index('idx_asins_amazon_pct', 'amazon_buybox_pct'),
    )

    asin: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str | None] = mapped_column(Text())
    brand: Mapped[str | None] = mapped_column(String(255))
    supplier_cost: Mapped[float] = mapped_column(Float, nullable=False)
    buybox: Mapped[float | None] = mapped_column(Float)
    sales_rank: Mapped[int | None] = mapped_column(Integer)
    monthly_sold: Mapped[int | None] = mapped_column(Integer)
    amazon_buybox_pct: Mapped[float | None] = mapped_column(Float)
    referral_fee_pct: Mapped[float | None] = mapped_column(Float)
    fba_pick_pack_cents: Mapped[int | None] = mapped_column(Integer)
    number_of_items: Mapped[int | None] = mapped_column(Integer)
    package_quantity: Mapped[int | None] = mapped_column(Integer)
    eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    filter_failed: Mapped[str | None] = mapped_column(String(50))
    computed_roi_pct: Mapped[float | None] = mapped_column(Float)
    keepa_raw_json: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    session_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    state_json: Mapped[str] = mapped_column(Text, nullable=False, default='{}')
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
