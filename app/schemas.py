from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EligibilityCheckValue(BaseModel):
    passed: bool = Field(alias='pass')
    value: Any = None
    threshold: float | int | None = None

    model_config = {'populate_by_name': True}


class EligibilityResponse(BaseModel):
    asin: str
    title: str | None = None
    eligible: bool
    filter_failed: str | None = None
    checks: dict[str, EligibilityCheckValue]
    computed_roi_pct: float | None = None
    supplier_cost: float | None = None
    buybox: float | None = None
    amazon_buybox_pct: float | None = None
    not_found: bool = False


class BatchEligibilityRequest(BaseModel):
    asins: list[str]


class UpcResponse(BaseModel):
    input: str
    normalized: list[str]
    asins: list[str]


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sql: str | None = None
    out_of_scope: bool = False
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str
    sql: str | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)
    session_state: dict[str, Any] = Field(default_factory=dict)
    intent: dict[str, Any] = Field(default_factory=dict)
