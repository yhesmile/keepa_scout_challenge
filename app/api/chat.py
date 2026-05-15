from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.dependencies import get_chat_service
from app.schemas import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(tags=['chat'])


@router.post('/chat', response_model=ChatResponse)
async def chat(payload: ChatRequest, session: AsyncSession = Depends(get_session), chat_service: ChatService = Depends(get_chat_service)) -> ChatResponse:
    result = await chat_service.handle_turn(session, payload.session_id, payload.message)
    return ChatResponse(**result)
