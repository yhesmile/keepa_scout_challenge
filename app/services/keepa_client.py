from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Iterable
from typing import Any

import httpx

from app.config import Settings


class KeepaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._keys = deque(settings.keepa_keys)

    def _require_key(self) -> str:
        if not self._keys:
            raise RuntimeError('Missing KEEPA_API_KEYS configuration.')
        return self._keys[0]

    def _rotate_key(self) -> str:
        self._keys.rotate(-1)
        return self._require_key()

    async def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        retries = max(len(self._keys), 1) * 3
        async with httpx.AsyncClient(base_url=self.settings.keepa_base_url, timeout=30.0) as client:
            for attempt in range(retries):
                params = {**params, 'key': self._require_key(), 'domain': self.settings.keepa_domain}
                response = await client.get(endpoint, params=params)
                if response.status_code == 200:
                    return response.json()
                if response.status_code in {402, 429}:
                    self._rotate_key()
                    await asyncio.sleep(min(attempt + 1, 3))
                    continue
                response.raise_for_status()
        raise RuntimeError(f'Keepa request failed after retries: {endpoint}')

    async def get_token_status(self) -> dict[str, Any]:
        return await self._request('/token', {})

    async def get_products_by_asins(self, asins: Iterable[str]) -> list[dict[str, Any]]:
        asin_list = [asin.strip() for asin in asins if asin and asin.strip()]
        if not asin_list:
            return []
        payload = await self._request('/product', {'asin': ','.join(asin_list), 'stats': 90, 'buybox': 1, 'fbafees': 1, 'history': 0})
        return payload.get('products', [])

    async def get_products_by_code(self, code: str) -> list[dict[str, Any]]:
        payload = await self._request('/product', {'code': code, 'buybox': 1, 'fbafees': 1, 'history': 0})
        return payload.get('products', [])
