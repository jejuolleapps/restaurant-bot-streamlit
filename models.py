from pydantic import BaseModel
from typing import Optional


class RestaurantContext(BaseModel):
    """레스토랑 손님 정보 컨텍스트."""

    customer_name: str = "손님"
    is_vip: bool = False
    phone: Optional[str] = None


class HandoffData(BaseModel):
    """Triage 에이전트가 전문 에이전트로 handoff할 때 전달하는 데이터."""

    to_agent_name: str
    request_type: str
    request_description: str
    reason: str


class InputGuardRailOutput(BaseModel):
    """Input Guardrail 판정 결과."""

    is_off_topic: bool
    is_inappropriate: bool
    reason: str


class OutputGuardRailOutput(BaseModel):
    """Output Guardrail 판정 결과."""

    is_unprofessional: bool
    leaks_internal_info: bool
    reason: str
