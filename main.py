"""Restaurant Bot - Multi-Agent Handoff + Guardrails (Streamlit Cloud 용)."""

import asyncio
import os

import streamlit as st
from agents import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    Runner,
    SQLiteSession,
)
from agents.exceptions import MaxTurnsExceeded

# Streamlit Cloud 에선 st.secrets 로, 로컬에선 .env 로부터 읽기
try:
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
except Exception:
    pass

if not os.environ.get("OPENAI_API_KEY"):
    try:
        import dotenv

        dotenv.load_dotenv()
    except ImportError:
        pass

from models import RestaurantContext  # noqa: E402
from my_agents.triage_agent import triage_agent  # noqa: E402

# ---------------------------------------------------
# 페이지 설정
# ---------------------------------------------------
st.set_page_config(page_title="Restaurant Bot", page_icon=":fork_and_knife:")
st.title("Restaurant Bot")
st.caption(
    "Triage -> Menu / Order / Reservation / Complaints 전문 에이전트로 자동 연결됩니다. "
    "Input/Output Guardrails 로 부적절한 대화를 차단합니다."
)


# ---------------------------------------------------
# 손님 컨텍스트
# ---------------------------------------------------
if "customer_ctx" not in st.session_state:
    st.session_state["customer_ctx"] = RestaurantContext(
        customer_name="손님",
        is_vip=False,
    )
customer_ctx = st.session_state["customer_ctx"]


# ---------------------------------------------------
# 세션 메모리 (SQLite, in-memory for Streamlit Cloud)
# ---------------------------------------------------
if "session" not in st.session_state:
    # ":memory:" 를 쓰면 세션별 독립 메모리로 동작 (Streamlit Cloud 에서 안전)
    st.session_state["session"] = SQLiteSession(
        "restaurant-chat-history",
        ":memory:",
    )
session = st.session_state["session"]


# ---------------------------------------------------
# 현재 활성 에이전트 (handoff 에 따라 바뀜)
# ---------------------------------------------------
if "current_agent" not in st.session_state:
    st.session_state["current_agent"] = triage_agent


# ---------------------------------------------------
# 이전 대화 다시 그리기
# ---------------------------------------------------
async def paint_history() -> None:
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                content = message.get("content", "")
                if isinstance(content, str):
                    st.write(content)
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and "text" in part:
                            st.write(part["text"])


asyncio.run(paint_history())


# ---------------------------------------------------
# 에이전트 실행 (스트리밍)
# ---------------------------------------------------
AGENT_LABELS = {
    "Triage Agent": "안내 데스크",
    "Menu Agent": "메뉴 전문가",
    "Order Agent": "주문 담당",
    "Reservation Agent": "예약 담당",
    "Complaints Agent": "불만 처리 담당",
}


HANDOFF_TEXT_MARKERS = (
    "연결해 드릴게요",
    "연결해드릴게요",
    "담당에게 연결",
    "전문가에게 연결",
)


async def _stream_once(agent, user_message: str):
    """한 번의 스트림 실행. 반환: (any_handoff_happened, response_text, last_agent)."""
    current_agent_name = agent.name
    active_placeholder = st.empty()
    active_response = ""
    any_handoff_happened = False

    stream = Runner.run_streamed(
        agent,
        user_message,
        session=session,
        context=customer_ctx,
        max_turns=12,
    )

    async for event in stream.stream_events():
        if event.type == "agent_updated_stream_event":
            new_name = event.new_agent.name
            if new_name != current_agent_name:
                if active_response:
                    active_placeholder.write(
                        active_response.replace("$", "\\$")
                    )

                label = AGENT_LABELS.get(new_name, new_name)
                st.info(f"**{label}**(이)가 응답합니다")
                active_placeholder = st.empty()
                active_response = ""
                current_agent_name = new_name
                any_handoff_happened = True

                with st.sidebar:
                    st.success(f"연결: → **{new_name}**")

        elif event.type == "raw_response_event":
            if event.data.type == "response.output_text.delta":
                active_response += event.data.delta
                active_placeholder.write(
                    active_response.replace("$", "\\$")
                )

    if active_response:
        active_placeholder.write(active_response.replace("$", "\\$"))

    return any_handoff_happened, active_response, stream.last_agent


async def run_agent(user_message: str) -> None:
    with st.chat_message("ai"):
        start_agent = st.session_state["current_agent"]

        with st.sidebar:
            st.write(f"시작 에이전트: **{start_agent.name}**")

        try:
            any_handoff, text, last_agent = await _stream_once(
                start_agent, user_message
            )

            # 자동 재라우팅: handoff 텍스트는 나왔는데 실제 전환이 없고,
            # 시작이 Triage 가 아닌 경우 → Triage 로 한 번만 재시도.
            # 실제 handoff 가 있었던 경우(any_handoff=True)에는 재시도 하지 않아
            # 핑퐁을 유발하지 않음.
            need_retry = (
                not any_handoff
                and any(m in text for m in HANDOFF_TEXT_MARKERS)
                and start_agent.name != "Triage Agent"
            )

            if need_retry:
                st.info("자동으로 안내 데스크를 통해 다시 연결합니다...")
                with st.sidebar:
                    st.warning("자동 재라우팅 → Triage")

                any_handoff, text, last_agent = await _stream_once(
                    triage_agent, user_message
                )

            st.session_state["current_agent"] = last_agent

            with st.sidebar:
                st.write(f"최종 에이전트: **{last_agent.name}**")

            if not text:
                st.warning(
                    "응답이 생성되지 않았어요. 같은 질문을 다시 해주시거나, "
                    "사이드바의 '대화 초기화' 후 새로 시도해주세요."
                )

        except MaxTurnsExceeded:
            st.warning(
                "여러 전문가 사이에서 처리가 길어졌어요. "
                "사이드바의 '대화 초기화' 후 **한 가지 주제**(메뉴 / 주문 / 예약 / 불만)로 "
                "다시 질문해 주세요."
            )
            with st.sidebar:
                st.error("MaxTurnsExceeded — 대화 초기화 권장")

        except InputGuardrailTripwireTriggered:
            st.warning(
                "저는 레스토랑 관련 질문(메뉴 / 주문 / 예약 / 불만)에 대해서만 "
                "도와드리고 있어요. 부적절한 표현도 정중히 사양합니다. "
                "무엇을 도와드릴까요?"
            )
            with st.sidebar:
                st.error("Input Guardrail 발동")

        except OutputGuardrailTripwireTriggered:
            st.warning(
                "죄송합니다. 답변을 생성했지만 내부 기준에 맞지 않아 전달하지 "
                "못했습니다. 다른 방식으로 다시 질문해 주시겠어요?"
            )
            with st.sidebar:
                st.error("Output Guardrail 발동")

        except Exception as e:
            st.error(f"알 수 없는 오류: {type(e).__name__}")
            with st.sidebar:
                st.error(str(e)[:200])


# ---------------------------------------------------
# 채팅 입력
# ---------------------------------------------------
prompt = st.chat_input("무엇을 도와드릴까요? (메뉴 / 주문 / 예약 / 불만)")

if prompt:
    with st.chat_message("human"):
        st.write(prompt)
    asyncio.run(run_agent(prompt))


# ---------------------------------------------------
# 사이드바
# ---------------------------------------------------
with st.sidebar:
    st.header("설정")

    name_input = st.text_input("손님 이름", value=customer_ctx.customer_name)
    vip_input = st.checkbox("VIP 손님", value=customer_ctx.is_vip)
    if st.button("적용"):
        st.session_state["customer_ctx"] = RestaurantContext(
            customer_name=name_input,
            is_vip=vip_input,
        )
        st.rerun()

    st.divider()
    st.subheader("에이전트 구성")
    st.caption("- Triage Agent - 요청 분류 및 라우팅")
    st.caption("- Menu Agent - 메뉴/재료/알레르기")
    st.caption("- Order Agent - 주문 접수/확인")
    st.caption("- Reservation Agent - 테이블 예약")
    st.caption("- Complaints Agent - 불만 처리")
    st.caption("- Input/Output Guardrails 적용")

    st.divider()
    if st.button("대화 초기화 (Triage로 돌아가기)"):
        try:
            asyncio.run(session.clear_session())
        except Exception:
            pass
        # 세션 객체 자체를 새로 만들어 잔여 상태 완전 제거
        st.session_state["session"] = SQLiteSession(
            "restaurant-chat-history",
            ":memory:",
        )
        st.session_state["current_agent"] = triage_agent
        st.rerun()

    st.divider()
    st.subheader("활동 로그")
