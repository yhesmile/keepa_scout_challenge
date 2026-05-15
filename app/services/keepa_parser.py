from __future__ import annotations

import json
from typing import Any

AMAZON_SELLER_ID = 'ATVPDKIKX0DER'
SALES_RANK_INDEX = 3
BUY_BOX_INDEX = 18


def _clean_price(value: Any) -> float | None:
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if value < 0:
        return None
    return round(value / 100, 2) if value > 100 else round(value, 2)


def _clean_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        value = int(value)
    except (TypeError, ValueError):
        return None
    return None if value < 0 else value


def _from_stats_current(stats: dict[str, Any] | None, index: int) -> Any:
    if not isinstance(stats, dict):
        return None
    current = stats.get('current')
    if isinstance(current, list) and len(current) > index:
        return current[index]
    return None


def compute_amazon_buybox_pct(product: dict[str, Any]) -> float | None:
    stats = product.get('stats') or {}
    buybox_stats = stats.get('buyBoxStats') if isinstance(stats, dict) else None
    if isinstance(buybox_stats, dict):
        amazon_stats = buybox_stats.get(AMAZON_SELLER_ID)
        if isinstance(amazon_stats, dict):
            percent = amazon_stats.get('percentageWon') or amazon_stats.get('buyBoxPercentage')
            if percent is not None:
                return round(float(percent), 2)
        percent = buybox_stats.get('amazonPercentage')
        if percent is not None:
            return round(float(percent), 2)

    history = product.get('buyBoxSellerIdHistory') or []
    if not isinstance(history, list) or len(history) < 2:
        return None

    pairs: list[tuple[int, str]] = []
    for index in range(0, len(history) - 1, 2):
        try:
            timestamp = int(history[index])
        except (TypeError, ValueError):
            continue
        seller_id = str(history[index + 1])
        pairs.append((timestamp, seller_id))
    if len(pairs) < 1:
        return None

    end_timestamp = _clean_int(product.get('lastUpdate')) or pairs[-1][0]
    total_duration = 0
    amazon_duration = 0
    for idx, (timestamp, seller_id) in enumerate(pairs):
        next_timestamp = pairs[idx + 1][0] if idx + 1 < len(pairs) else end_timestamp
        duration = max(next_timestamp - timestamp, 0)
        total_duration += duration
        if seller_id == AMAZON_SELLER_ID:
            amazon_duration += duration
    if total_duration <= 0:
        return None
    return round(100 * amazon_duration / total_duration, 2)


def parse_product(product: dict[str, Any], supplier_cost: float) -> dict[str, Any]:
    stats = product.get('stats') if isinstance(product.get('stats'), dict) else {}
    buybox = (
        _clean_price(product.get('buyBoxPrice'))
        or _clean_price(product.get('buyBoxCurrentPrice'))
        or _clean_price(_from_stats_current(stats, BUY_BOX_INDEX))
    )
    sales_rank = _clean_int(product.get('salesRankReference')) or _clean_int(product.get('salesRank')) or _clean_int(_from_stats_current(stats, SALES_RANK_INDEX))
    monthly_sold = _clean_int(product.get('monthlySold'))
    referral_fee_pct = product.get('referralFeePercent')
    try:
        referral_fee_pct = round(float(referral_fee_pct), 2) if referral_fee_pct is not None else None
    except (TypeError, ValueError):
        referral_fee_pct = None
    fba_fees = product.get('fbaFees') if isinstance(product.get('fbaFees'), dict) else {}
    fba_pick_pack_cents = _clean_int(fba_fees.get('pickAndPackFee'))

    return {
        'asin': product.get('asin'),
        'title': product.get('title'),
        'brand': product.get('brand'),
        'supplier_cost': supplier_cost,
        'buybox': buybox,
        'sales_rank': sales_rank,
        'monthly_sold': monthly_sold,
        'amazon_buybox_pct': compute_amazon_buybox_pct(product),
        'referral_fee_pct': referral_fee_pct,
        'fba_pick_pack_cents': fba_pick_pack_cents,
        'number_of_items': _clean_int(product.get('numberOfItems')),
        'package_quantity': _clean_int(product.get('packageQuantity')),
        'keepa_raw_json': json.dumps(product, ensure_ascii=True),
    }
