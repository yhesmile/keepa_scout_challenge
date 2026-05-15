from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.repositories.asin_repository import AsinRepository
from app.schemas import BatchEligibilityRequest, EligibilityResponse
from app.services.eligibility import evaluate_eligibility

router = APIRouter(tags=['eligibility'])


def _to_response(row) -> EligibilityResponse:
    if row is None:
        return EligibilityResponse(asin='', title=None, eligible=False, filter_failed='not_found', checks={}, not_found=True)
    checks = evaluate_eligibility(
        {
            'referral_fee_pct': row.referral_fee_pct,
            'sales_rank': row.sales_rank,
            'monthly_sold': row.monthly_sold,
            'buybox': row.buybox,
            'amazon_buybox_pct': row.amazon_buybox_pct,
        }
    )['checks']
    return EligibilityResponse(
        asin=row.asin,
        title=row.title,
        eligible=row.eligible,
        filter_failed=row.filter_failed,
        checks=checks,
        computed_roi_pct=row.computed_roi_pct,
        supplier_cost=row.supplier_cost,
        buybox=row.buybox,
        amazon_buybox_pct=row.amazon_buybox_pct,
    )


@router.get('/eligibility/{asin}', response_model=EligibilityResponse)
async def get_eligibility(asin: str, session: AsyncSession = Depends(get_session)) -> EligibilityResponse:
    repository = AsinRepository(session)
    row = await repository.get_by_asin(asin.upper())
    if row is None:
        return EligibilityResponse(asin=asin.upper(), eligible=False, filter_failed='not_found', checks={}, not_found=True)
    return _to_response(row)


@router.post('/eligibility/batch', response_model=list[EligibilityResponse])
async def get_eligibility_batch(payload: BatchEligibilityRequest, session: AsyncSession = Depends(get_session)) -> list[EligibilityResponse]:
    repository = AsinRepository(session)
    rows = await repository.get_by_asins([asin.upper() for asin in payload.asins])
    row_map = {row.asin: row for row in rows}
    responses: list[EligibilityResponse] = []
    for asin in payload.asins:
        row = row_map.get(asin.upper())
        if row is None:
            responses.append(EligibilityResponse(asin=asin.upper(), eligible=False, filter_failed='not_found', checks={}, not_found=True))
        else:
            responses.append(_to_response(row))
    return responses
