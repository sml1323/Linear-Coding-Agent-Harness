# 하네스 엔지니어링 학습 로드맵

> **기반 코드**: `Linear-Coding-Agent-Harness` (Cole Medin)
> **목표**: 코드 한 줄 한 줄의 역할을 이해하고, 직접 미니 구현을 쌓아올린다.
> **진행 방식**: "Chapter N 진행할게. 스케폴딩 만들어줘" → 스케폴딩 받기 → TODO 직접 구현 → 이해해야 할 질문 Q&A

---

## 전체 구조 지도 (Big Picture)

```
autonomous_agent_demo.py   ← 진입점 (CLI 인수 파싱, asyncio 시작)
         │
         ▼
    agent.py               ← ✨ 핵심: 무한 루프, 세션 관리
    ├── client.py          ← SDK 클라이언트 설정, 보안 설정, MCP 연결
    ├── security.py        ← 배쉬 명령어 화이트리스트 검증 (Hook)
    ├── prompts.py         ← .md 프롬프트 파일 로더
    ├── progress.py        ← 진행 상태 조회 (Linear → 로컬 파일)
    └── linear_config.py   ← 상수 (마커 파일명 등)
```

---

## 📘 Chapter 1: 진입점과 이벤트 루프 이해

**핵심 개념**: Python `asyncio`가 왜 필요한가?

### 읽을 코드

- [`autonomous_agent_demo.py`](file:///Users/imseungmin/work/harness/Linear-Coding-Agent-Harness/autonomous_agent_demo.py) — `main()`, `parse_args()`
- [`agent.py`](file:///Users/imseungmin/work/harness/Linear-Coding-Agent-Harness/agent.py) L97-187 — `run_autonomous_agent()`의 `while True` 루프

### 핵심 라인 해부

```python
# agent.py L146 — 이것이 하네스의 심장박동
while True:
    iteration += 1
    client = create_client(project_dir, model)  # 매 루프 새 컨텍스트!
    async with client:
        status, response = await run_agent_session(client, prompt, project_dir)
    await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)  # 비동기 대기
```

### 이해해야 할 질문

1. `asyncio.run()`과 `async def`가 없으면 왜 안 되는가?
2. `while True` 안에서 매번 `create_client()`를 새로 하는 이유가 뭔가?
3. `KeyboardInterrupt`를 잡는 이유는?

### 🛠 미니 구현 (`ch1_event_loop.py`)

> **참고 파일**: `autonomous_agent_demo.py`, `agent.py` L97-187

```python
# ch1_event_loop.py
import asyncio

# TODO 1: async def fake_agent_session(iteration) 구현
#   - iteration 번호를 출력하고, asyncio.sleep()으로 AI 응답을 시뮬레이션
#   - 완료 후 "continue" 반환

# TODO 2: async def run_loop(max_iter=3) 구현
#   - while True 루프로 iteration을 증가시키면서 fake_agent_session 호출
#   - max_iter 초과 시 루프 종료
#   - 왜 매 루프마다 세션을 새로 만들까? (agent.py의 create_client() 패턴 참고)

# TODO 3: asyncio.run()으로 진입점 작성
#   - KeyboardInterrupt를 잡아서 graceful하게 종료되도록 처리
```

---

## 📘 Chapter 2: SDK와 LLM 통신 방식

**핵심 개념**: AI 모델과 어떻게 대화하는가? (단순 HTTP 요청 vs SDK의 차이)

### 읽을 코드

- [`agent.py`](file:///Users/imseungmin/work/harness/Linear-Coding-Agent-Harness/agent.py) L23-94 — `run_agent_session()`
- [`client.py`](file:///Users/imseungmin/work/harness/Linear-Coding-Agent-Harness/client.py) L139-169 — `ClaudeSDKClient(options=ClaudeCodeOptions(...))`

### 핵심 라인 해부

```python
# agent.py L49 — SDK는 스트리밍으로 응답을 받는다 (한 번에 받지 않음)
async for msg in client.receive_response():
    if msg_type == "AssistantMessage":
        for block in msg.content:
            if block_type == "TextBlock":
                print(block.text, end="", flush=True)   # 실시간 출력
            elif block_type == "ToolUseBlock":
                print(f"\n[Tool: {block.name}]")        # 도구 사용 감지!
```

### 이해해야 할 질문

1. `AssistantMessage`와 `UserMessage`가 번갈아 오는 이유는?
2. `ToolUseBlock`이 나타났다는 것은 무슨 의미인가?
3. `max_turns=1000`은 어디서 사용되고 왜 필요한가?

### 🛠 미니 구현 (`ch2_llm_chat.py`)

> **참고 파일**: `agent.py` L23-94, `client.py` L139-169

```python
# ch2_llm_chat.py
import anthropic

# TODO 1: Anthropic 클라이언트 초기화
#   - ANTHROPIC_API_KEY 환경변수를 어떻게 로딩하나? (agent.py, client.py 참고)

# TODO 2: 단순 1회 호출 (non-streaming)
#   - messages.create()로 "print('hello world') 작성해줘" 요청
#   - 응답의 어느 필드에서 텍스트를 꺼내야 하나? (구조 직접 탐색)

# TODO 3: 스트리밍 버전으로 재구현
#   - agent.py L49의 async for 패턴과 비교해서
#     동기 스트리밍(messages.stream)과 어떻게 다른지 직접 확인
#   - flush=True가 왜 필요한가?

# TODO 4: TextBlock vs ToolUseBlock 구분
#   - 응답 content 리스트를 순회하며 block type을 출력해보기
#   - agent.py L49-96의 처리 로직을 흉내내보기
```

---

## 📘 Chapter 3: 보안 훅 (Security Hook)

**핵심 개념**: AI가 위험한 명령을 실행하지 못하도록 코드 레벨에서 막는 방법

### 읽을 코드

- [`security.py`](file:///Users/imseungmin/work/harness/Linear-Coding-Agent-Harness/security.py) — 전체 (360줄)
- [`client.py`](file:///Users/imseungmin/work/harness/Linear-Coding-Agent-Harness/client.py) L160-164 — Hook 등록 방법

### 핵심 라인 해부

```python
# client.py L160-163 — 훅 등록: Bash 명령 실행 전 검사기 삽입
hooks={
    "PreToolUse": [
        HookMatcher(matcher="Bash", hooks=[bash_security_hook]),
    ],
},

# security.py L297-359 — 실제 검사 로직
async def bash_security_hook(input_data, ...):
    command = input_data["tool_input"]["command"]
    commands = extract_commands(command)       # 명령어 파싱
    for cmd in commands:
        if cmd not in ALLOWED_COMMANDS:        # 화이트리스트 체크
            return {"decision": "block", "reason": f"..."}
    return {}  # 허용
```

### 이해해야 할 질문

1. `rm -rf /`가 실행되면 어떤 경로로 차단되는가? `extract_commands()`를 직접 따라가 보라.
2. `COMMANDS_NEEDING_EXTRA_VALIDATION`에 있는 명령어들은 왜 한 번 더 검사가 필요한가?
3. 파싱 실패 시 `return []`을 반환해 차단하는 이유는? (Fail-safe 원칙)

### 🛠 미니 구현 (`ch3_security_hook.py`)

> **참고 파일**: `security.py` 전체, `client.py` L160-164

```python
# ch3_security_hook.py
ALLOWED = {"ls", "cat", "echo", "pwd"}

# TODO 1: extract_commands(command) 구현
#   - security.py의 extract_commands()를 보기 전에 먼저 직접 설계해보기
#   - "ls -al && rm -rf /" 같은 파이프/체이닝은 어떻게 분리해야 하나?

# TODO 2: my_security_check(command) 구현
#   - 빈 명령어, 허용 목록 외 명령어 처리 (fail-safe 원칙 적용)
#   - 반환값 형태: {"decision": "allow"} or {"decision": "block", "reason": "..."}

# TODO 3: 아래 테스트 케이스를 모두 통과시키세요
tests = [
    ("ls -al",                True),   # 허용
    ("rm -rf /",              False),  # 차단
    ("echo hello && rm foo",  False),  # 체이닝 → 차단
    ("cat README.md",         True),   # 허용
    ("",                      False),  # 빈 명령어 → 차단
]
for cmd, expected_allow in tests:
    # 직접 검증 로직 작성
    pass
```

---

## 📘 Chapter 4: 상태 관리와 세션 핸드오프 (Memory)

**핵심 개념**: 컨텍스트 윈도우가 터지지 않으면서 작업 기억을 유지하는 방법

### 읽을 코드

- [`progress.py`](file:///Users/imseungmin/work/harness/Linear-Coding-Agent-Harness/progress.py) — 전체
- [`linear_config.py`](file:///Users/imseungmin/work/harness/Linear-Coding-Agent-Harness/linear_config.py) — 마커 파일 상수
- [`agent.py`](file:///Users/imseungmin/work/harness/Linear-Coding-Agent-Harness/agent.py) L124-141 — 첫 실행 vs 재시작 분기

### 핵심 라인 해부

```python
# agent.py L126 — 이 한 줄이 "재시작 가능한 에이전트"의 핵심
is_first_run = not is_linear_initialized(project_dir)

# progress.py L37-48 — 마커 파일(.linear_project.json)로 상태 확인
def is_linear_initialized(project_dir: Path) -> bool:
    state = load_linear_project_state(project_dir)
    return state is not None and state.get("initialized", False)
```

### 이해해야 할 질문

1. 에이전트가 갑자기 꺼졌다가 재시작해도 왜 이어서 작업할 수 있나?
2. 세션 간 기억이 Linear 댓글/이슈(외부)에 저장되는 이유가 컨텍스트 윈도우와 무슨 관계인가?
3. `is_first_run`이 `False`로 변경되는 시점은 어디인가? (코드에서 찾기)

### 🛠 미니 구현 (`ch4_state_manager.py`)

> **참고 파일**: `progress.py` 전체, `linear_config.py`, `agent.py` L124-141

```python
# ch4_state_manager.py
import json
from pathlib import Path

STATE_FILE = Path("./agent_state.json")

# TODO 1: load_state() 구현
#   - STATE_FILE이 없으면 초기 상태 딕셔너리 반환 (어떤 필드가 필요한가?)
#   - progress.py의 load_linear_project_state()와 비교

# TODO 2: save_state(state) 구현
#   - JSON으로 직렬화해서 파일에 저장

# TODO 3: run_task(task_name) 구현
#   - 이미 완료된 태스크는 SKIP (idempotent 보장)
#   - 완료 후 상태 저장
#   - progress.py에서 is_linear_initialized()가 어떤 필드를 보는지 확인 후 동일 패턴 적용

# TODO 4: 아래를 실행했을 때 세 번째 호출이 SKIP되어야 합니다
#   프로그램을 종료 후 재실행해도 상태가 유지되는지 확인!
if __name__ == "__main__":
    run_task("DB 스키마 생성")
    run_task("로그인 API 구현")
    run_task("DB 스키마 생성")  # → [SKIP] 출력되어야 함
```

---

## 📘 Chapter 5: MCP (Model Context Protocol) 도구 연결

**핵심 개념**: AI에게 외부 세계(파일, 브라우저, Linear API)에 접근하는 도구를 주는 방법

### 읽을 코드

- [`client.py`](file:///Users/imseungmin/work/harness/Linear-Coding-Agent-Harness/client.py) L18-65 — 도구 목록 정의
- [`client.py`](file:///Users/imseungmin/work/harness/Linear-Coding-Agent-Harness/client.py) L148-159 — MCP 서버 연결

### 핵심 라인 해부

```python
# client.py L148-159 — MCP 서버를 두 개 연결
mcp_servers={
    # 로컬 프로세스로 실행되는 브라우저 자동화 서버
    "puppeteer": {"command": "npx", "args": ["puppeteer-mcp-server"]},
    # 원격 HTTP 서버로 연결되는 Linear 프로젝트 관리 API
    "linear": {
        "type": "http",
        "url": "https://mcp.linear.app/mcp",
        "headers": {"Authorization": f"Bearer {linear_api_key}"}
    }
},
```

### 이해해야 할 질문

1. `mcp__linear__list_issues` 같은 도구 이름의 `mcp__linear__` 접두사는 어디서 오는가?
2. `"command": "npx"` 방식과 `"type": "http"` 방식의 차이는?
3. AI가 도구를 호출하면 응답이 다시 AI에게 어떻게 전달되는가? (`ToolResultBlock` 추적)

### 🛠 미니 구현 (`ch5_mock_tools.py`)

> **참고 파일**: `client.py` L18-65, L148-159

```python
# ch5_mock_tools.py
import json

# TODO 1: MOCK_TOOLS 딕셔너리 정의
#   - client.py의 도구 목록(L18-65)을 보고, 어떤 도구들이 있는지 파악
#   - "list_issues", "update_issue" 최소 두 개를 흉내낼 것

# TODO 2: handle_tool_call(tool_name, tool_input) 구현
#   - dispatcher 패턴: tool_name에 따라 적절한 가짜 응답 반환
#   - 알 수 없는 도구일 때는 어떻게 처리해야 안전한가?
#   - agent.py에서 ToolResultBlock이 어떻게 다시 AI에 전달되는지 흐름 추적

# TODO 3: mcp__linear__ 접두사 시뮬레이션
#   - 도구 이름이 "mcp__linear__list_issues" 형태로 오면 어떻게 파싱할 것인가?

# TODO 4: 아래 시나리오를 시뮬레이션
scenario = [
    ("list_issues", {}),
    ("update_issue", {"id": "1", "status": "In Progress"}),
    ("unknown_tool",  {}),  # → 안전한 에러 처리
]
for tool_name, tool_input in scenario:
    # 직접 호출하고 결과 출력
    pass
```

---

## 📘 Chapter 6: 통합 - 미니 하네스 직접 만들기

**목표**: Ch1~5에서 배운 것을 하나의 파일로 조립한다. 이것이 진짜 이해의 증거.

```python
# ch6_mini_harness.py
# Ch1: asyncio 루프
# Ch2: OpenAI API 통신
# Ch3: 보안 훅
# Ch4: 파일 기반 상태 관리
# Ch5: 가짜 도구 디스패처

# TODO: 위 5개 챕터의 구현을 조합해서
#   - 메시지를 받아 AI에 전달하고
#   - 도구 호출이 오면 보안 훅으로 검사한 뒤 dispatcher에 전달하고
#   - 결과를 다시 AI에 넘기고
#   - 작업 완료 상태를 파일에 저장하는
#   나만의 미니 에이전트를 만들어보세요.
```

---

## 학습 진행 체크리스트

| Chapter | 개념                      | 대응 파일                              | 미니 구현              | 완료 |
| ------- | ------------------------- | -------------------------------------- | ---------------------- | ---- |
| 1       | asyncio 이벤트 루프       | `autonomous_agent_demo.py`, `agent.py` | `ch1_event_loop.py`    | [x]  |
| 2       | SDK + LLM 스트리밍 통신   | `agent.py`, `client.py`                | `ch2_llm_chat.py`      | [x]  |
| 3       | 보안 훅 (Bash Allowlist)  | `security.py`, `client.py`             | `ch3_security_hook.py` | [ ]  |
| 4       | 상태 관리 + 세션 핸드오프 | `progress.py`, `agent.py`              | `ch4_state_manager.py` | [ ]  |
| 5       | MCP 도구 연결             | `client.py`                            | `ch5_mock_tools.py`    | [ ]  |
| 6       | 전체 통합                 | 전체                                   | `ch6_mini_harness.py`  | [ ]  |

---

> [!TIP]
> 막히면 해당 챕터의 **이해해야 할 질문** 목록을 먼저 읽고, 원본 코드에서 답을 직접 찾아보세요. 그래도 모르면 그때 물어보는 것이 가장 효과적입니다.
