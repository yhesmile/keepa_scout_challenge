from __future__ import annotations

from typing import Any

RULE_ORDER = ['referral_fee_pct', 'rank', 'buybox', 'amazon_pct', 'monthly_sold']


def evaluate_eligibility(product: dict[str, Any]) -> dict[str, Any]:
    referral_fee_pct = product.get('referral_fee_pct')
    sales_rank = product.get('sales_rank')
    monthly_sold = product.get('monthly_sold')
    buybox = product.get('buybox')
    amazon_buybox_pct = product.get('amazon_buybox_pct')

    checks = {
        'referral_fee_pct': {'pass': referral_fee_pct is not None and referral_fee_pct > 0, 'value': referral_fee_pct, 'threshold': 0},
        'rank': {'pass': (sales_rank is not None and sales_rank <= 100000) or (monthly_sold is not None and monthly_sold >= 100), 'value': sales_rank, 'threshold': 100000},
        'buybox': {'pass': buybox is not None and buybox >= 10, 'value': buybox, 'threshold': 10},
        'amazon_pct': {'pass': amazon_buybox_pct is not None and amazon_buybox_pct <= 80, 'value': amazon_buybox_pct, 'threshold': 80},
        'monthly_sold': {'pass': monthly_sold is None or monthly_sold >= 100, 'value': monthly_sold, 'threshold': 100},
    }
    filter_failed = next((rule for rule in RULE_ORDER if not checks[rule]['pass']), None)
    return {'checks': checks, 'eligible': filter_failed is None, 'filter_failed': filter_failed}
