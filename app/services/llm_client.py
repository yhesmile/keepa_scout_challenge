from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx

from app.config import Settings


class LLMConfigurationError(RuntimeError):
    pass


class LLMResponseError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _credentials(self) -> tuple[str, str]:
        api_key, base_url = self.settings.get_openai_credentials()
        if not api_key:
            raise LLMConfigurationError(
                'LLM 未配置。请在 .env 中设置 OPENAI_API_KEY、DEEPSEEK_API_KEY 或 MOONSHOT_API_KEY。'
            )
        return api_key, (base_url or 'https://api.openai.com/v1').rstrip('/')

    async def complete_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
    ) -> str:
        api_key, base_url = self._credentials()
        payload = {
            'model': self.settings.resolved_llm_model,
            'temperature': temperature,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f'{base_url}/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        try:
            content = data['choices'][0]['message']['content']
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMResponseError('LLM 返回格式异常，无法读取 message.content。') from exc

        if isinstance(content, list):
            parts = [item.get('text', '') for item in content if isinstance(item, dict)]
            return ''.join(parts).strip()
        if not isinstance(content, str):
            raise LLMResponseError('LLM 返回的 content 不是字符串。')
        return content.strip()

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        content = await self.complete_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )
        return self._parse_json_object(content)

    @staticmethod
    def _parse_json_object(content: str) -> dict[str, Any]:
        raw = content.strip()
        if raw.startswith('```'):
            raw = raw.strip('`')
            if raw.startswith('json'):
                raw = raw[4:].strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find('{')
            end = raw.rfind('}')
            if start == -1 or end == -1 or end <= start:
                raise LLMResponseError(f'LLM 未返回合法 JSON：{content}')
            data = json.loads(raw[start:end + 1])
        if not isinstance(data, dict):
            raise LLMResponseError('LLM 返回的 JSON 不是对象。')
        return data


@lru_cache(maxsize=16)
def load_prompt(name: str) -> str:
    prompt_path = Path(__file__).resolve().parents[1] / 'prompts' / name
    return prompt_path.read_text(encoding='utf-8')
