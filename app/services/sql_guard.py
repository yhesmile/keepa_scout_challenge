from __future__ import annotations

import re

BLOCKED = re.compile(r'\b(drop|insert|update|delete|create|alter|truncate|attach|pragma)\b', re.IGNORECASE)


def validate_select_sql(sql: str) -> bool:
    if not sql:
        return False
    stripped = sql.strip().rstrip(';')
    if ';' in stripped:
        return False
    if not stripped.lower().startswith('select'):
        return False
    return BLOCKED.search(stripped) is None
