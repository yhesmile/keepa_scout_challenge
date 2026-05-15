from __future__ import annotations

import re


def isbn13_to_isbn10(code: str) -> str | None:
    if len(code) != 13 or not code.startswith('978'):
        return None
    core = code[3:-1]
    total = sum((10 - idx) * int(char) for idx, char in enumerate(core))
    remainder = 11 - (total % 11)
    check = 'X' if remainder == 10 else '0' if remainder == 11 else str(remainder)
    return core + check


def normalize_upc_candidates(raw_upc: str) -> list[str]:
    digits = re.sub(r'\D+', '', raw_upc)
    if not digits:
        return []

    candidates: list[str] = []

    def add(value: str | None) -> None:
        if value and value not in candidates:
            candidates.append(value)

    add(digits)
    if len(digits) == 11:
        add(digits.zfill(12))
    if len(digits) == 12 and digits.startswith('0'):
        add(digits[1:])
    if len(digits) in {13, 14}:
        add(digits.lstrip('0'))
        add(digits[-13:])
        add(digits[-12:])
    if len(digits) == 13:
        add(isbn13_to_isbn10(digits))
    if len(digits) == 14:
        for width in (13, 12, 11):
            if len(digits) > width:
                add(digits[-width:])
    if len(digits) < 12:
        add(digits.zfill(12))
    return candidates
