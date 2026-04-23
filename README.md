# Restaurant Bot - Multi-Agent + Guardrails + Streamlit Cloud

OpenAI Agents SDK 기반 레스토랑 봇. 5개 에이전트와 입출력 Guardrails 를 갖추고
Streamlit Cloud 로 배포 가능합니다.

## 에이전트 구성

| 에이전트 | 역할 |
|---------|-----|
| **Triage Agent** | 손님 요청 분류 + 전문 에이전트로 라우팅 |
| **Menu Agent** | 메뉴 / 재료 / 가격 / 알레르기 안내 |
| **Order Agent** | 주문 접수 및 확인 |
| **Reservation Agent** | 테이블 예약 |
| **Complaints Agent** | 불만 처리 (환불 / 할인 / 매니저 콜백 / 에스컬레이션) |

## Guardrails

- **Input Guardrail** — 레스토랑과 무관한 질문 / 부적절한 언어 차단
- **Output Guardrail** — 비전문적인 응답 / 내부 정보 노출 차단

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# .env 파일에 OPENAI_API_KEY 넣기
cp .env.example .env
# 또는 .streamlit/secrets.toml 사용

streamlit run main.py
```

http://localhost:8501

## Streamlit Cloud 배포

1. 이 폴더를 GitHub 리포지토리에 푸시 (`.env` 와 `.streamlit/secrets.toml` 은 커밋 금지)
2. https://share.streamlit.io 접속 -> GitHub 로그인
3. "New app" -> 리포지토리 선택 -> Main file path: `main.py`
4. Advanced settings -> Secrets 에 다음 추가:

   ```toml
   OPENAI_API_KEY = "sk-..."
   ```

5. Deploy 클릭 -> 1~2분 후 공개 URL 확인

## 파일 구조

```
DeployToStreamlitCloud/
├── main.py                     Streamlit UI + 가드레일 트리거 처리
├── models.py                   Context + Guardrail 출력 모델
├── tools.py                    15개 @function_tool + 로깅 훅
├── guardrails.py               Input / Output Guardrail 정의
├── my_agents/
│   ├── triage_agent.py         라우터 + input guardrail
│   ├── menu_agent.py           (+ output guardrail)
│   ├── order_agent.py          (+ output guardrail)
│   ├── reservation_agent.py    (+ output guardrail)
│   └── complaints_agent.py     (+ output guardrail)
├── requirements.txt
├── .gitignore
├── .env.example
└── .streamlit/
    └── secrets.toml            (로컬 전용, gitignored)
```

## 테스트 시나리오

```
[Handoff]
- "예약하고 싶어" -> Reservation Agent
- "채식 메뉴 있어?" -> Menu Agent
- "스테이크 2개 주문" -> Order Agent
- "음식이 별로였어" -> Complaints Agent

[Input Guardrail]
- "인생의 의미가 뭘까?" -> 차단 메시지
- "파이썬 코드 짜줘" -> 차단 메시지
- 욕설 -> 차단 메시지

[Output Guardrail]
- 정상 응답은 통과
- 모델이 시스템 프롬프트를 흘리려 하면 차단
```
