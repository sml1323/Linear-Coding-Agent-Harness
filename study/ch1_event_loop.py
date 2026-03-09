"""
Chapter 1: 진입점과 이벤트 루프 이해
=====================================

참고 코드:
  - autonomous_agent_demo.py  → main(), parse_args()
  - agent.py L97-187          → run_autonomous_agent()의 while True 루프

핵심 개념: Python asyncio가 왜 필요한가?

이해해야 할 질문:
  Q1. asyncio.run()과 async def가 없으면 왜 안 되는가?
  Q2. while True 안에서 매번 create_client()를 새로 하는 이유가 뭔가?
  Q3. KeyboardInterrupt를 잡는 이유는?
"""

import asyncio


# ---------------------------------------------------------------------------
# TODO 1: async def fake_agent_session(iteration) 구현
#   - iteration 번호를 출력하고, asyncio.sleep()으로 AI 응답을 시뮬레이션
#   - 완료 후 "continue" 반환
#
# 힌트: agent.py의 run_agent_session()이 어떤 값을 반환하는지 확인해보세요.
# ---------------------------------------------------------------------------

async def fake_agent_session(iteration: int) -> str:
    print(f"현재 Iteration: {iteration}")
    await asyncio.sleep(1)
    return "continue"


# ---------------------------------------------------------------------------
# TODO 2: async def run_loop(max_iter=3) 구현
#   - while True 루프로 iteration을 증가시키면서 fake_agent_session 호출
#   - max_iter 초과 시 루프 종료
#   - 🤔 왜 매 루프마다 세션을 새로 만들까?
#       agent.py L159: client = create_client(project_dir, model)  ← 매 루프!
#       이 패턴이 존재하는 이유가 뭔지 생각해보세요.
# ---------------------------------------------------------------------------

async def run_loop(max_iter: int = 3) -> None:
    current_iter = 0
    while current_iter < max_iter:
        await fake_agent_session(current_iter)
        current_iter += 1
    
    




# ---------------------------------------------------------------------------
# TODO 3: asyncio.run()으로 진입점 작성
#   - KeyboardInterrupt를 잡아서 graceful하게 종료되도록 처리
#
# 참고: autonomous_agent_demo.py L110-123
#   try:
#       asyncio.run(run_autonomous_agent(...))
#   except KeyboardInterrupt:
#       print("Interrupted by user")
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        
        asyncio.run(run_loop())
    except KeyboardInterrupt:
        print("Interrupted by user")

