from __future__ import annotations


def compute_payout(buybox: float, referral_fee_pct: float, fba_pick_pack_cents: int) -> float:
    referral = buybox * (referral_fee_pct / 100)
    fba = fba_pick_pack_cents / 100
    storage = 0.50
    return buybox - referral - fba - storage



def compute_roi(
    buybox: float | None,
    referral_pct: float | None,
    fba_pick_pack_cents: int | None,
    supplier_cost: float,
    n_items: int | None,
) -> float | None:
    if buybox is None or referral_pct is None or fba_pick_pack_cents is None:
        return None
    payout = compute_payout(buybox, referral_pct, fba_pick_pack_cents)
    cost = supplier_cost * max(n_items or 1, 1)
    return None if cost <= 0 else round(100 * (payout - cost) / cost, 2)
