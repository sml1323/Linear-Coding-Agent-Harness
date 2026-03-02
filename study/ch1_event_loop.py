"""
Chapter 1: asyncio 이벤트 루프 이해
=====================================
핵심 개념: Python asyncio가 왜 필요한가?

대응 원본 코드:
  - autonomous_agent_demo.py : main() → asyncio.run(run_autonomous_agent(...))
  - agent.py L146-186        : while True 루프, create_client, await asyncio.sleep

실행 방법: python ch1_event_loop.py
"""

import asyncio


async def fake_agent_session(iteration: int) -> str:
    """
    실제 agent.py 의 run_agent_session() 을 단순화한 버전.
    AI API 호출 대신 sleep 으로 대기 시뮬레이션.
    """
    print(f"[Session {iteration}] 작업 시작...")
    await asyncio.sleep(1)                      # ← AI 응답 대기 (비동기!)
    print(f"[Session {iteration}] 작업 완료!")
    return "continue"


async def run_loop(max_iter: int = 3):
    """
    실제 agent.py 의 run_autonomous_agent() 를 단순화한 버전.

    질문 1: asyncio.sleep() vs time.sleep() 차이가 뭔가?
            time.sleep()으로 바꾸면 어떻게 되는지 직접 바꿔서 비교해보자.

    질문 2: while True 안에서 매번 새 컨텍스트(client)를 만드는 이유는?
            원본에서는 create_client()가 여기 위치에 있다.

    질문 3: KeyboardInterrupt 핸들링이 main()에 있는 이유는?
    """
    iteration = 0

    while True:
        iteration += 1

        # 최대 반복 횟수 체크 (원본 agent.py L150 대응)
        if iteration > max_iter:
            print(f"\n최대 반복({max_iter}회) 도달. 종료.")
            break

        # 세션 실행
        status = await fake_agent_session(iteration)

        # 상태에 따른 분기 (원본 agent.py L173-181 대응)
        if status == "continue":
            print(f"  → {3}초 후 다음 세션 시작...\n")
            await asyncio.sleep(0.5)            # 데모용 짧은 대기
        elif status == "error":
            print("  → 오류 발생! 재시도...")
            await asyncio.sleep(0.5)


def main():
    """
    원본 autonomous_agent_demo.py 의 main() 대응.
    asyncio.run() 이 이벤트 루프를 시작하는 진입점이다.
    """
    print("=" * 50)
    print("  AUTONOMOUS AGENT LOOP DEMO (Chapter 1)")
    print("=" * 50)
    print()

    try:
        asyncio.run(run_loop(max_iter=3))
    except KeyboardInterrupt:
        print("\n[Ctrl+C] 사용자가 중단했습니다.")
        print("재시작하려면 다시 실행하세요.")

    print("\n완료!")


if __name__ == "__main__":
    main()
