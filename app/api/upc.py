from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_keepa_client
from app.schemas import UpcResponse
from app.services.keepa_client import KeepaClient
from app.services.upc_normalizer import normalize_upc_candidates

router = APIRouter(tags=['upc'])


@router.get('/upc', response_model=UpcResponse)
async def lookup_upc(upc: str = Query(...), keepa_client: KeepaClient = Depends(get_keepa_client)) -> UpcResponse:
    normalized = normalize_upc_candidates(upc)
    asins: list[str] = []
    for candidate in normalized:
        products = await keepa_client.get_products_by_code(candidate)
        for product in products:
            asin = product.get('asin')
            if asin and asin not in asins:
                asins.append(asin)
    return UpcResponse(input=upc, normalized=normalized, asins=asins)
