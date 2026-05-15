from __future__ import annotations

from typing import Any

from sqlalchemy import text, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AsinSnapshot

UPSERT_COLUMNS = [
    'title', 'brand', 'supplier_cost', 'buybox', 'sales_rank', 'monthly_sold', 'amazon_buybox_pct',
    'referral_fee_pct', 'fba_pick_pack_cents', 'number_of_items', 'package_quantity',
    'eligible', 'filter_failed', 'computed_roi_pct', 'keepa_raw_json', 'updated_at',
]


class AsinRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_many(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        stmt = insert(AsinSnapshot).values(rows)
        updates = {column: getattr(stmt.excluded, column) for column in UPSERT_COLUMNS}
        await self.session.execute(stmt.on_conflict_do_update(index_elements=[AsinSnapshot.asin], set_=updates))
        await self.session.commit()

    async def get_by_asin(self, asin: str) -> AsinSnapshot | None:
        return await self.session.get(AsinSnapshot, asin)

    async def get_by_asins(self, asins: list[str]) -> list[AsinSnapshot]:
        result = await self.session.execute(select(AsinSnapshot).where(AsinSnapshot.asin.in_(asins)))
        return list(result.scalars())

    async def run_select(self, sql: str) -> list[dict[str, Any]]:
        result = await self.session.execute(text(sql))
        return [dict(row) for row in result.mappings().all()]
