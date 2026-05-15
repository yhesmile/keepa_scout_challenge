from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.asin_repository import AsinRepository
from app.repositories.session_repository import SessionRepository
from app.services.ask_service import OUT_OF_SCOPE_ANSWER
from app.services.llm_client import LLMClient, LLMConfigurationError, LLMResponseError, load_prompt


class ChatService:
    def __init__(self, settings: Any) -> None:
        self.settings = settings
        self.llm_client = LLMClient(settings)

    @staticmethod
    def _default_state() -> dict[str, Any]:
        return {'active_filters': {}, 'sort': 'roi_desc', 'limit': 20, 'last_result_asins': [], 'last_resolved_asin': None, 'user_constraints': {}}

    @staticmethod
    def _merge_state(saved: dict[str, Any]) -> dict[str, Any]:
        state = ChatService._default_state()
        for key, value in saved.items():
            if isinstance(state.get(key), dict) and isinstance(value, dict):
                state[key].update(value)
            else:
                state[key] = value
        return state

    @staticmethod
    def _topic_reset(state: dict[str, Any]) -> None:
        user_constraints = dict(state.get('user_constraints', {}))
        state['active_filters'] = {}
        state['sort'] = 'roi_desc'
        state['limit'] = 20
        state['last_result_asins'] = []
        state['last_resolved_asin'] = None
        state['user_constraints'] = user_constraints

    def _apply_intent(self, intent: dict[str, Any], state: dict[str, Any]) -> None:
        if intent.get('topic_reset'):
            self._topic_reset(state)

        budget = intent.get('budget_per_unit')
        if budget is not None:
            state['user_constraints']['budget_per_unit'] = budget
            state['active_filters']['max_supplier_cost'] = budget

        filters_to_clear = intent.get('filters_to_clear') or []
        for key in filters_to_clear:
            state['active_filters'].pop(key, None)

        filters_to_set = intent.get('filters_to_set') or {}
        for key, value in filters_to_set.items():
            if value is not None:
                state['active_filters'][key] = value

        if intent.get('sort') is not None:
            state['sort'] = intent['sort']
        if intent.get('limit') is not None:
            state['limit'] = max(int(intent['limit']), 1)

        budget = state['user_constraints'].get('budget_per_unit')
        if budget is not None:
            state['active_filters']['max_supplier_cost'] = budget

    @staticmethod
    def _build_list_sql(state: dict[str, Any]) -> str:
        where = []
        filters = state['active_filters']
        if filters.get('eligible_only'):
            where.append('eligible = 1')
        if filters.get('min_roi') is not None:
            where.append(f"computed_roi_pct >= {filters['min_roi']}")
        if filters.get('max_supplier_cost') is not None:
            where.append(f"supplier_cost <= {filters['max_supplier_cost']}")
        clause = f" WHERE {' AND '.join(where)}" if where else ''
        order = 'computed_roi_pct DESC' if state.get('sort') != 'amazon_pct_asc' else 'amazon_buybox_pct ASC'
        return 'SELECT asin, title, eligible, filter_failed, computed_roi_pct, buybox, amazon_buybox_pct, supplier_cost FROM asins' f'{clause} ORDER BY {order} LIMIT {int(state.get("limit", 20))}'

    @staticmethod
    def _detail_sql(asin: str) -> str:
        safe_asin = asin.replace("'", "''")
        return (
            'SELECT asin, title, eligible, filter_failed, computed_roi_pct, buybox, amazon_buybox_pct, supplier_cost '
            f"FROM asins WHERE asin = '{safe_asin}'"
        )

    async def _last_result_summary(self, repository: AsinRepository, state: dict[str, Any]) -> list[dict[str, Any]]:
        last_asins = state.get('last_result_asins', [])[:5]
        if not last_asins:
            return []
        rows = await repository.run_select(
            'SELECT asin, title, eligible, computed_roi_pct, buybox, amazon_buybox_pct, supplier_cost '
            f"FROM asins WHERE asin IN ({','.join(repr(asin) for asin in last_asins)})"
        )
        row_map = {row['asin']: row for row in rows}
        return [row_map[asin] for asin in last_asins if asin in row_map]

    async def _generate_intent(self, message: str, state: dict[str, Any], previous_results: list[dict[str, Any]]) -> dict[str, Any]:
        prompt = load_prompt('chat_intent.txt')
        user_prompt = (
            f'当前消息:\n{message}\n\n'
            f'当前 session_state JSON:\n{json.dumps(state, ensure_ascii=False)}\n\n'
            f'上一轮结果摘要 JSON:\n{json.dumps(previous_results, ensure_ascii=False)}\n'
        )
        intent = await self.llm_client.complete_json(
            system_prompt=prompt,
            user_prompt=user_prompt,
            temperature=0.0,
        )
        intent.setdefault('out_of_scope', False)
        intent.setdefault('topic_reset', False)
        intent.setdefault('mode', 'list')
        intent.setdefault('resolved_asin', None)
        intent.setdefault('budget_per_unit', None)
        intent.setdefault('filters_to_set', {})
        intent.setdefault('filters_to_clear', [])
        intent.setdefault('sort', None)
        intent.setdefault('limit', None)
        intent.setdefault('detail_focus', 'summary')
        return intent

    async def _generate_answer(
        self,
        *,
        message: str,
        intent: dict[str, Any],
        sql: str | None,
        results: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> str:
        prompt = load_prompt('chat_answer.txt')
        user_prompt = (
            f'用户消息:\n{message}\n\n'
            f'intent JSON:\n{json.dumps(intent, ensure_ascii=False)}\n\n'
            f'SQL:\n{sql}\n\n'
            f'结果 JSON:\n{json.dumps(results, ensure_ascii=False)}\n\n'
            f'当前 session_state JSON:\n{json.dumps(state, ensure_ascii=False)}\n'
        )
        return await self.llm_client.complete_text(
            system_prompt=prompt,
            user_prompt=user_prompt,
            temperature=0.2,
        )

    async def handle_turn(self, session: AsyncSession, session_id: str, message: str) -> dict[str, Any]:
        session_repository = SessionRepository(session)
        asin_repository = AsinRepository(session)
        state = self._merge_state(await session_repository.get_state(session_id))
        previous_results = await self._last_result_summary(asin_repository, state)

        try:
            intent = await self._generate_intent(message, state, previous_results)
        except LLMConfigurationError as exc:
            return {'answer': str(exc), 'sql': None, 'results': [], 'session_state': state, 'intent': {'intent': 'llm_not_configured'}}
        except (LLMResponseError, Exception) as exc:
            return {'answer': f'LLM 解析聊天意图失败：{exc}', 'sql': None, 'results': [], 'session_state': state, 'intent': {'intent': 'llm_error'}}

        if intent.get('out_of_scope'):
            await session_repository.save_state(session_id, state)
            return {'answer': OUT_OF_SCOPE_ANSWER, 'sql': None, 'results': [], 'session_state': state, 'intent': intent}

        self._apply_intent(intent, state)
        sql: str | None = None
        results: list[dict[str, Any]] = []

        if intent.get('mode') == 'detail':
            resolved_asin = intent.get('resolved_asin') or state.get('last_resolved_asin')
            if resolved_asin:
                sql = self._detail_sql(str(resolved_asin))
                results = await asin_repository.run_select(sql)
                state['last_resolved_asin'] = resolved_asin
                state['last_result_asins'] = [resolved_asin] if results else []
        elif intent.get('mode') == 'list':
            sql = self._build_list_sql(state)
            results = await asin_repository.run_select(sql)
            state['last_result_asins'] = [row['asin'] for row in results]
            if results:
                state['last_resolved_asin'] = results[0]['asin']

        await session_repository.save_state(session_id, state)

        try:
            answer = await self._generate_answer(
                message=message,
                intent=intent,
                sql=sql,
                results=results,
                state=state,
            )
        except LLMConfigurationError as exc:
            answer = str(exc)
        except (LLMResponseError, Exception) as exc:
            answer = f'LLM 生成聊天回答失败：{exc}'

        return {'answer': answer, 'sql': sql, 'results': results, 'session_state': state, 'intent': intent}
