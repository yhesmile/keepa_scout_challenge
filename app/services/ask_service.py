from __future__ import annotations

import json
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.asin_repository import AsinRepository
from app.services.llm_client import LLMClient, LLMConfigurationError, LLMResponseError, load_prompt
from app.services.sql_guard import validate_select_sql

OUT_OF_SCOPE_ANSWER = 'I can only help with Amazon ASIN arbitrage analysis.'


class AskService:
    def __init__(self, settings: Any) -> None:
        self.settings = settings
        self.llm_client = LLMClient(settings)

    @staticmethod
    def schema_context() -> str:
        return (
            'Table: asins\n'
            'Columns: asin, title, brand, supplier_cost, buybox, sales_rank, monthly_sold, '
            'amazon_buybox_pct, referral_fee_pct, fba_pick_pack_cents, number_of_items, '
            'package_quantity, eligible, filter_failed, computed_roi_pct, updated_at'
        )

    async def generate_sql(self, question: str) -> tuple[str | None, bool]:
        prompt = load_prompt('ask_sql.txt')
        user_prompt = (
            f'用户问题:\n{question}\n\n'
            f'数据库结构:\n{self.schema_context()}\n'
        )
        result = await self.llm_client.complete_json(
            system_prompt=prompt,
            user_prompt=user_prompt,
            temperature=0.0,
        )
        return result.get('sql'), bool(result.get('out_of_scope'))

    async def format_answer(self, question: str, sql: str, rows: list[dict[str, Any]]) -> str:
        prompt = load_prompt('ask_answer.txt')
        user_prompt = (
            f'用户问题:\n{question}\n\n'
            f'已执行 SQL:\n{sql}\n\n'
            f'查询结果 JSON:\n{json.dumps(rows, ensure_ascii=False)}\n'
        )
        return await self.llm_client.complete_text(
            system_prompt=prompt,
            user_prompt=user_prompt,
            temperature=0.2,
        )

    async def answer_question(self, session: AsyncSession, question: str) -> dict[str, Any]:
        try:
            sql, out_of_scope = await self.generate_sql(question)
        except LLMConfigurationError as exc:
            return {'answer': str(exc), 'sql': None, 'out_of_scope': False, 'rows': [], 'row_count': 0}
        except (LLMResponseError, httpx.HTTPError, Exception) as exc:  # type: ignore[name-defined]
            return {'answer': f'LLM 生成 SQL 失败：{exc}', 'sql': None, 'out_of_scope': False, 'rows': [], 'row_count': 0}

        if out_of_scope or sql is None:
            return {'answer': OUT_OF_SCOPE_ANSWER, 'sql': None, 'out_of_scope': True, 'rows': [], 'row_count': 0}
        if not validate_select_sql(sql):
            return {'answer': "I couldn't translate that question safely.", 'sql': None, 'out_of_scope': False, 'rows': [], 'row_count': 0}

        repository = AsinRepository(session)
        rows = await repository.run_select(sql)
        try:
            answer = await self.format_answer(question, sql, rows)
        except LLMConfigurationError as exc:
            answer = str(exc)
        except (LLMResponseError, Exception) as exc:
            answer = f'LLM 生成回答失败，但 SQL 已执行成功。错误：{exc}'
        return {'answer': answer, 'sql': sql, 'out_of_scope': False, 'rows': rows, 'row_count': len(rows)}
