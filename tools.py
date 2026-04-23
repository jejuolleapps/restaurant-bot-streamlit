"""레스토랑 봇이 사용하는 Mock 도구들."""

import random

import streamlit as st
from agents import Agent, AgentHooks, RunContextWrapper, Tool, function_tool

from models import RestaurantContext


# =============================================================================
# 메뉴 관련 도구
# =============================================================================

MENU_DB = {
    "스테이크": {
        "가격": 45000,
        "재료": ["소고기 안심", "버터", "로즈마리", "마늘", "소금", "후추"],
        "알레르기": ["유제품"],
        "채식": False,
    },
    "토마토 파스타": {
        "가격": 18000,
        "재료": ["파스타", "토마토", "바질", "올리브오일", "마늘"],
        "알레르기": ["밀(글루텐)"],
        "채식": True,
    },
    "버섯 리조또": {
        "가격": 22000,
        "재료": ["쌀", "표고버섯", "양송이", "파마산 치즈", "버터"],
        "알레르기": ["유제품"],
        "채식": True,
    },
    "시저 샐러드": {
        "가격": 15000,
        "재료": ["로메인", "시저드레싱", "크루통", "파마산 치즈", "안초비"],
        "알레르기": ["유제품", "생선", "밀(글루텐)", "계란"],
        "채식": False,
    },
    "연어 스테이크": {
        "가격": 32000,
        "재료": ["노르웨이 연어", "레몬", "딜", "버터"],
        "알레르기": ["생선", "유제품"],
        "채식": False,
    },
    "비건 부다볼": {
        "가격": 19000,
        "재료": ["현미", "병아리콩", "아보카도", "케일", "퀴노아", "두부"],
        "알레르기": ["콩"],
        "채식": True,
    },
}


@function_tool
def get_menu_list() -> str:
    """현재 제공되는 모든 메뉴 목록과 가격을 반환합니다."""
    lines = ["[오늘의 메뉴]"]
    for name, info in MENU_DB.items():
        tag = "(채식)" if info["채식"] else "      "
        lines.append(f"{tag} {name} - {info['가격']:,}원")
    return "\n".join(lines)


@function_tool
def get_menu_detail(menu_name: str) -> str:
    """특정 메뉴의 재료, 가격, 알레르기 정보를 반환합니다.

    Args:
        menu_name: 조회하려는 메뉴 이름
    """
    for name, info in MENU_DB.items():
        if menu_name in name or name in menu_name:
            allergens = ", ".join(info["알레르기"]) if info["알레르기"] else "없음"
            ingredients = ", ".join(info["재료"])
            veg = "채식 가능" if info["채식"] else "육류 포함"
            return (
                f"[{name}] ({info['가격']:,}원)\n"
                f"- 재료: {ingredients}\n"
                f"- 알레르기 유발: {allergens}\n"
                f"- 구분: {veg}"
            )
    return f"'{menu_name}' 메뉴를 찾을 수 없습니다. 메뉴 목록을 확인해 주세요."


@function_tool
def find_vegetarian_menu() -> str:
    """채식(비건/베지테리언) 가능 메뉴만 골라서 반환합니다."""
    veg = [name for name, info in MENU_DB.items() if info["채식"]]
    if not veg:
        return "죄송합니다. 현재 채식 메뉴가 준비되어 있지 않습니다."
    return "[채식 가능 메뉴]\n" + "\n".join(f"- {n}" for n in veg)


@function_tool
def check_allergy(allergen: str) -> str:
    """특정 알레르기 유발 성분이 들어간 메뉴를 찾아줍니다.

    Args:
        allergen: 확인하려는 알레르기 성분 (예: 유제품, 밀, 생선)
    """
    has = [name for name, info in MENU_DB.items() if any(allergen in a for a in info["알레르기"])]
    safe = [name for name, info in MENU_DB.items() if not any(allergen in a for a in info["알레르기"])]
    result = [f"[주의] '{allergen}' 포함 메뉴:"]
    result.append(", ".join(has) if has else "없음")
    result.append(f"\n[안전] '{allergen}' 없는 메뉴:")
    result.append(", ".join(safe) if safe else "없음")
    return "\n".join(result)


# =============================================================================
# 주문 관련 도구
# =============================================================================


@function_tool
def place_order(
    context: RunContextWrapper[RestaurantContext],
    items: str,
    table_number: int,
) -> str:
    """손님의 주문을 접수합니다.

    Args:
        items: 주문 항목들 (쉼표로 구분)
        table_number: 테이블 번호
    """
    order_id = f"ORD-{random.randint(10000, 99999)}"
    prep_time = random.randint(15, 30)
    return (
        f"[주문 접수 완료]\n"
        f"- 주문번호: {order_id}\n"
        f"- 테이블: {table_number}번\n"
        f"- 주문: {items}\n"
        f"- 예상 조리시간: {prep_time}분\n"
        f"- 손님: {context.context.customer_name}"
    )


@function_tool
def confirm_order(order_id: str) -> str:
    """주문 번호로 주문 내역을 확인합니다.

    Args:
        order_id: 확인하려는 주문 번호
    """
    return (
        f"[주문 확인]\n"
        f"- 주문번호: {order_id}\n"
        f"- 상태: 조리 중\n"
        f"- 예상 완료: 약 15분 후"
    )


# =============================================================================
# 예약 관련 도구
# =============================================================================


@function_tool
def make_reservation(
    context: RunContextWrapper[RestaurantContext],
    party_size: int,
    date: str,
    time: str,
) -> str:
    """레스토랑 테이블을 예약합니다.

    Args:
        party_size: 인원수
        date: 예약 날짜 (예: '2026-04-25')
        time: 예약 시간 (예: '19:00')
    """
    reservation_id = f"RES-{random.randint(10000, 99999)}"
    table_no = random.randint(1, 20)
    vip_note = " (VIP 테이블 배정)" if context.context.is_vip else ""
    return (
        f"[예약 완료]{vip_note}\n"
        f"- 예약번호: {reservation_id}\n"
        f"- 이름: {context.context.customer_name}\n"
        f"- 인원: {party_size}명\n"
        f"- 일시: {date} {time}\n"
        f"- 테이블: {table_no}번\n"
        f"- 예약 확정 문자가 발송됩니다."
    )


@function_tool
def check_availability(date: str, time: str, party_size: int) -> str:
    """특정 날짜/시간에 테이블 예약이 가능한지 확인합니다.

    Args:
        date: 확인하려는 날짜
        time: 확인하려는 시간
        party_size: 인원수
    """
    available = random.choice([True, True, True, False])
    if available:
        return f"[가능] {date} {time} - {party_size}명 예약 가능합니다."
    alt_times = ["18:00", "20:30", "21:00"]
    return (
        f"[불가] {date} {time}은(는) 이미 마감되었습니다.\n"
        f"대체 가능 시간: {', '.join(alt_times)}"
    )


@function_tool
def cancel_reservation(reservation_id: str) -> str:
    """예약을 취소합니다.

    Args:
        reservation_id: 취소할 예약 번호
    """
    return f"예약번호 {reservation_id}이(가) 취소되었습니다."


# =============================================================================
# 불만 처리 관련 도구
# =============================================================================


@function_tool
def offer_refund(
    context: RunContextWrapper[RestaurantContext],
    amount: int,
    reason: str,
) -> str:
    """손님에게 환불을 제공합니다.

    Args:
        amount: 환불 금액 (원)
        reason: 환불 사유
    """
    refund_id = f"RFD-{random.randint(10000, 99999)}"
    return (
        f"[환불 처리]\n"
        f"- 환불번호: {refund_id}\n"
        f"- 금액: {amount:,}원\n"
        f"- 사유: {reason}\n"
        f"- 손님: {context.context.customer_name}\n"
        f"- 3영업일 이내 결제수단으로 환불됩니다."
    )


@function_tool
def offer_discount(
    context: RunContextWrapper[RestaurantContext],
    percent: int,
    reason: str,
) -> str:
    """다음 방문 시 사용 가능한 할인을 제공합니다.

    Args:
        percent: 할인율 (예: 20, 30, 50)
        reason: 할인 제공 사유
    """
    coupon_id = f"CPN-{random.randint(10000, 99999)}"
    return (
        f"[할인 쿠폰 발급]\n"
        f"- 쿠폰번호: {coupon_id}\n"
        f"- 할인율: {percent}%\n"
        f"- 사유: {reason}\n"
        f"- 손님: {context.context.customer_name}\n"
        f"- 유효기간: 발급일로부터 60일"
    )


@function_tool
def schedule_manager_callback(
    context: RunContextWrapper[RestaurantContext],
    phone: str,
    issue_summary: str,
) -> str:
    """매니저가 손님에게 직접 연락하도록 콜백을 예약합니다.

    Args:
        phone: 손님 연락처
        issue_summary: 문제 요약
    """
    callback_id = f"CBK-{random.randint(10000, 99999)}"
    return (
        f"[매니저 콜백 예약]\n"
        f"- 접수번호: {callback_id}\n"
        f"- 연락처: {phone}\n"
        f"- 손님: {context.context.customer_name}\n"
        f"- 문제 요약: {issue_summary}\n"
        f"- 24시간 이내 매니저가 직접 연락드립니다."
    )


@function_tool
def escalate_severe_complaint(
    context: RunContextWrapper[RestaurantContext],
    summary: str,
    priority: str,
) -> str:
    """심각한 불만을 본사/CS팀에 에스컬레이션합니다.

    Args:
        summary: 불만 요약
        priority: 우선순위 (low / medium / high / critical)
    """
    ticket_id = f"ESC-{random.randint(10000, 99999)}"
    hours = {"critical": 1, "high": 2, "medium": 4, "low": 8}.get(priority.lower(), 4)
    return (
        f"[본사 에스컬레이션]\n"
        f"- 티켓번호: {ticket_id}\n"
        f"- 우선순위: {priority.upper()}\n"
        f"- 요약: {summary}\n"
        f"- 손님: {context.context.customer_name}\n"
        f"- 담당자 배정 예상: {hours}시간 이내"
    )


# =============================================================================
# 에이전트 활동 로깅 훅
# =============================================================================


class AgentLoggingHooks(AgentHooks):
    """사이드바에 에이전트 활동과 handoff를 실시간 표시."""

    async def on_tool_start(
        self,
        context: RunContextWrapper[RestaurantContext],
        agent: Agent[RestaurantContext],
        tool: Tool,
    ):
        with st.sidebar:
            st.write(f"**{agent.name}** 도구 시작: `{tool.name}`")

    async def on_tool_end(
        self,
        context: RunContextWrapper[RestaurantContext],
        agent: Agent[RestaurantContext],
        tool: Tool,
        result: str,
    ):
        with st.sidebar:
            st.write(f"**{agent.name}** 도구 완료: `{tool.name}`")
            st.code(result)

    async def on_handoff(
        self,
        context: RunContextWrapper[RestaurantContext],
        agent: Agent[RestaurantContext],
        source: Agent[RestaurantContext],
    ):
        with st.sidebar:
            st.success(f"Handoff: **{source.name}** -> **{agent.name}**")

    async def on_start(
        self,
        context: RunContextWrapper[RestaurantContext],
        agent: Agent[RestaurantContext],
    ):
        with st.sidebar:
            st.write(f"**{agent.name}** 활성화")

    async def on_end(
        self,
        context: RunContextWrapper[RestaurantContext],
        agent: Agent[RestaurantContext],
        output,
    ):
        with st.sidebar:
            st.write(f"**{agent.name}** 응답 완료")
