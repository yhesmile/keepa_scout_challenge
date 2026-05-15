from __future__ import annotations

import json
from datetime import datetime, UTC

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatSession


class SessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_state(self, session_id: str) -> dict:
        row = await self.session.get(ChatSession, session_id)
        return json.loads(row.state_json) if row else {}

    async def save_state(self, session_id: str, state: dict) -> None:
        row = await self.session.get(ChatSession, session_id)
        payload = json.dumps(state, ensure_ascii=True)
        if row is None:
            row = ChatSession(session_id=session_id, state_json=payload, updated_at=datetime.now(UTC))
            self.session.add(row)
        else:
            row.state_json = payload
            row.updated_at = datetime.now(UTC)
        await self.session.commit()
