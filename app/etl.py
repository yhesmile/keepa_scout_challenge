from __future__ import annotations

import csv
from datetime import datetime, UTC
from pathlib import Path

from app.config import get_settings
from app.db import AsyncSessionLocal, init_db
from app.repositories.asin_repository import AsinRepository
from app.services.eligibility import evaluate_eligibility
from app.services.keepa_client import KeepaClient
from app.services.keepa_parser import parse_product
from app.services.roi import compute_roi


def _sample_csv_path() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    return repo_root / 'candidate_package' / 'data' / 'sample_asins.csv'


async def run_etl() -> None:
    settings = get_settings()
    await init_db()
    client = KeepaClient(settings)

    with _sample_csv_path().open('r', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))

    supplier_costs = {row['asin'].strip(): float(row['supplier_cost']) for row in rows}
    asins = list(supplier_costs.keys())
    batch_size = max(settings.keepa_batch_size, 1)
    upsert_rows: list[dict] = []

    for index in range(0, len(asins), batch_size):
        batch = asins[index:index + batch_size]
        products = await client.get_products_by_asins(batch)
        product_map = {product.get('asin'): product for product in products if product.get('asin')}
        for asin in batch:
            product = product_map.get(asin)
            if product is None:
                continue
            parsed = parse_product(product, supplier_costs[asin])
            parsed.update(evaluate_eligibility(parsed))
            parsed.pop('checks', None)
            parsed['computed_roi_pct'] = compute_roi(
                parsed.get('buybox'),
                parsed.get('referral_fee_pct'),
                parsed.get('fba_pick_pack_cents'),
                parsed['supplier_cost'],
                parsed.get('number_of_items'),
            )
            parsed['updated_at'] = datetime.now(UTC)
            upsert_rows.append(parsed)

    async with AsyncSessionLocal() as session:
        repository = AsinRepository(session)
        await repository.upsert_many(upsert_rows)


if __name__ == '__main__':
    import asyncio

    asyncio.run(run_etl())
