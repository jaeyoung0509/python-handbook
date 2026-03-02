# Added in Python 3.12: sys.monitoring for low-overhead interpreter events.
# Python 3.12에서 추가: 저비용 인터프리터 이벤트 API인 sys.monitoring.
# Why: sys.settrace was too expensive for debuggers, profilers, and coverage tools.
# 왜: sys.settrace는 디버거, 프로파일러, 커버리지 도구 입장에서 비용이 너무 컸다.
# Use when: building tooling that needs call/line/return events without full tracing overhead.
# 언제 쓰나: 전체 trace 오버헤드 없이 call/line/return 이벤트를 보고 싶은 도구 작성 시 좋다.

import sys
from types import CodeType

TOOL_ID = 5


def on_line(code: CodeType, line_number: int) -> None:
    if code.co_name == "sample_work":
        print(f"LINE {line_number}: {code.co_name}")


def sample_work(limit: int) -> int:
    total = 0
    for value in range(limit):
        total += value
    return total


def main() -> None:
    # A tool id reserves one monitoring slot for your debugger/profiler-like tool.
    # tool id는 디버거/프로파일러 같은 도구가 사용할 monitoring 슬롯을 하나 예약한다.
    sys.monitoring.use_tool_id(TOOL_ID, "study-monitor")
    try:
        sys.monitoring.register_callback(
            TOOL_ID,
            sys.monitoring.events.LINE,
            on_line,
        )
        # Turn on only the events you need; that is where the lower overhead comes from.
        # 필요한 이벤트만 켜는 방식이기 때문에 기존 tracing보다 비용이 낮다.
        sys.monitoring.set_events(TOOL_ID, sys.monitoring.events.LINE)
        print("result:", sample_work(4))
    finally:
        sys.monitoring.set_events(TOOL_ID, 0)
        sys.monitoring.free_tool_id(TOOL_ID)


if __name__ == "__main__":
    main()
