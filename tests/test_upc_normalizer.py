from app.services.upc_normalizer import normalize_upc_candidates


def test_normalize_upc_handles_11_digit_case() -> None:
    candidates = normalize_upc_candidates('70537500052')
    assert '70537500052' in candidates
    assert '070537500052' in candidates



def test_normalize_upc_strips_dirty_characters() -> None:
    candidates = normalize_upc_candidates('070-537-500-052')
    assert candidates[0] == '070537500052'
