from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.dependencies import get_ask_service
from app.schemas import AskRequest, AskResponse
from app.services.ask_service import AskService

router = APIRouter(tags=['ask'])


@router.post('/ask', response_model=AskResponse)
async def ask_question(payload: AskRequest, session: AsyncSession = Depends(get_session), ask_service: AskService = Depends(get_ask_service)) -> AskResponse:
    result = await ask_service.answer_question(session, payload.question)
    return AskResponse(**result)
