"""
Chapter 2: SDK와 LLM 통신 방식
================================

참고 코드:
  - agent.py L23-94   → run_agent_session() — 스트리밍 응답 처리
  - client.py L139-169 → ClaudeSDKClient(options=ClaudeCodeOptions(...))

핵심 개념: AI 모델과 어떻게 대화하는가? (단순 HTTP 요청 vs SDK의 차이)

이 파일에서는 원본 하네스가 Anthropic SDK를 쓰는 것과 동일한 패턴을
OpenAI API로 재현합니다.

이해해야 할 질문:
  Q1. AssistantMessage와 UserMessage가 번갈아 오는 이유는?
  Q2. ToolUseBlock이 나타났다는 것은 무슨 의미인가?
  Q3. max_turns=1000은 어디서 사용되고 왜 필요한가?

OpenAI 대응 개념:
  - Anthropic TextBlock      → OpenAI choice.message.content
  - Anthropic ToolUseBlock   → OpenAI choice.message.tool_calls
  - Anthropic 스트리밍       → OpenAI stream=True (chunk.choices[0].delta)
"""

from openai import OpenAI


# ---------------------------------------------------------------------------
# TODO 1: OpenAI 클라이언트 초기화
#   - OPENAI_API_KEY 환경변수를 어떻게 로딩하나?
#     (OpenAI() 생성자가 자동으로 환경변수를 읽는다 — 확인해보세요)
#   - 원본 하네스의 client.py에서 Anthropic 클라이언트를 초기화하는 방식과 비교
#
# 힌트: from openai import OpenAI → client = OpenAI()
# ---------------------------------------------------------------------------
from openai import OpenAI
import os 
from dotenv import load_dotenv

load_dotenv()



def create_client() -> OpenAI:
    client = OpenAI()
    return client



# ---------------------------------------------------------------------------
# TODO 2: 단순 1회 호출 (non-streaming)
#   - client.chat.completions.create()로 "print('hello world') 작성해줘" 요청
#   - model="gpt-4o-mini" 사용 (비용 절약)
#   - 응답의 어느 필드에서 텍스트를 꺼내야 하나?
#     → response.choices[0].message.content
#   - 원본 agent.py에서는 이 단계를 스트리밍으로 하지만,
#     먼저 non-streaming으로 구조를 파악할 것
# ---------------------------------------------------------------------------

def simple_chat(client: OpenAI, user_message: str) -> str:
    model = "gpt-4o-mini"
    response = client.chat.completions.create(
    model = model,
    messages = [{"role": "user", "content": user_message}])
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# TODO 3: 스트리밍 버전으로 재구현
#   - client.chat.completions.create(stream=True)를 사용
#   - agent.py L49의 async for 패턴과 비교:
#
#     [원본 하네스 — Anthropic]
#     async for msg in client.receive_response():
#         if block_type == "TextBlock":
#             print(block.text, end="", flush=True)
#
#     [OpenAI 대응]
#     for chunk in response:           # ← 동기 스트리밍
#         delta = chunk.choices[0].delta
#         if delta.content:
#             print(delta.content, end="", flush=True)
#
#   - flush=True가 왜 필요한가?
#     → Python의 print는 기본적으로 버퍼링됨.
#       flush=True 없으면 토큰이 쌓여서 한꺼번에 출력되어
#       "실시간 스트리밍" 효과가 사라진다.
# ---------------------------------------------------------------------------

def streaming_chat(client: OpenAI, user_message: str) -> str:
    model = "gpt-4o-mini"
    response = client.chat.completions.create(
    model = model,
    messages = [{"role": "user", "content": user_message}],
    stream = True)
    for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)


# ---------------------------------------------------------------------------
# TODO 4: Tool Use (Function Calling) 시뮬레이션
#   - OpenAI의 tools 파라미터로 함수 정의를 전달
#   - 원본 하네스에서 ToolUseBlock이 나타나면 도구를 실행하는 것처럼,
#     OpenAI에서도 tool_calls가 응답에 포함되면 처리해야 한다
#
#   [원본 하네스 — agent.py L60-67]
#   elif block_type == "ToolUseBlock":
#       print(f"\n[Tool: {block.name}]")
#       print(f"   Input: {block.input}")
#
#   [OpenAI 대응]
#   if message.tool_calls:
#       for tool_call in message.tool_calls:
#           print(f"\n[Tool: {tool_call.function.name}]")
#           print(f"   Input: {tool_call.function.arguments}")
#
#   - 아래 tools 정의를 completions.create()에 전달하고,
#     "서울 날씨 알려줘"라고 요청했을 때 tool_calls가 오는지 확인
#   - tool_calls가 왔을 때 content와 어떻게 구분되는지 직접 확인
# ---------------------------------------------------------------------------

# 도구 정의 (OpenAI Function Calling 스펙)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "주어진 도시의 현재 날씨를 조회합니다",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "날씨를 조회할 도시 이름 (예: Seoul, Tokyo)",
                    }
                },
                "required": ["city"],
            },
        },
    }
]


def tool_use_chat(client: OpenAI, user_message: str) -> None:
    """
    도구 호출이 포함된 채팅을 수행합니다.
    응답에서 content(텍스트)와 tool_calls(도구 호출)를 구분하여 처리합니다.

    agent.py의 run_agent_session()에서
    TextBlock과 ToolUseBlock을 구분하는 로직을 참고하세요.
    """
    response = client.chat.completions.create(
    model = "gpt-4o-mini",
    messages = [{"role": "user", "content": user_message}],
    tools = TOOLS)

    message = response.choices[0].message

    if message.tool_calls:
        for tool_call in message.tool_calls:
            print(f"\n[AI가 도구를 호출했습니다!]")
            print(f"도구 이름: {tool_call.function.name}")
            print(f"도구에 전달할 인자(arguments): {tool_call.function.arguments}")
            print(message)
    elif message.content:
        # AI가 그냥 텍스트로 답변한 경우
        print(f"일반 텍스트 응답: {message.content}")
    
    

# ---------------------------------------------------------------------------
# 실행 진입점
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    client = create_client()

    print("=" * 60)
    print("  TODO 2: Non-Streaming 호출")
    print("=" * 60)
    print(simple_chat(client, "Python으로 print('hello world')를 작성해줘"))

    print("\n" + "=" * 60)
    print("  TODO 3: Streaming 호출")
    print("=" * 60)
    streaming_chat(client, "Python으로 print('hello world')를 작성해줘")

    print("\n" + "=" * 60)
    print("  TODO 4: Tool Use (Function Calling)")
    print("=" * 60)
    tool_use_chat(client, "서울 날씨 알려줘")
