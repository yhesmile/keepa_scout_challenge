from app.services.eligibility import evaluate_eligibility
from app.services.roi import compute_roi


def test_eligibility_passes_expected_rule_set() -> None:
    result = evaluate_eligibility(
        {
            'referral_fee_pct': 15,
            'sales_rank': 88003,
            'monthly_sold': None,
            'buybox': 29.99,
            'amazon_buybox_pct': 12.7,
        }
    )
    assert result['eligible'] is True
    assert result['filter_failed'] is None



def test_compute_roi_matches_challenge_formula() -> None:
    roi = compute_roi(29.99, 15, 450, 9.27, 1)
    assert round(roi, 1) == 121.0
