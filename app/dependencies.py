from __future__ import annotations

from functools import lru_cache

from app.config import Settings, get_settings
from app.services.ask_service import AskService
from app.services.chat_service import ChatService
from app.services.keepa_client import KeepaClient


@lru_cache(maxsize=1)
def get_keepa_client() -> KeepaClient:
    return KeepaClient(get_settings())


@lru_cache(maxsize=1)
def get_ask_service() -> AskService:
    return AskService(get_settings())


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    return ChatService(get_settings())



def get_app_settings() -> Settings:
    return get_settings()
