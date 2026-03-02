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
    sys.monitoring.use_tool_id(TOOL_ID, "study-monitor")
    try:
        sys.monitoring.register_callback(
            TOOL_ID,
            sys.monitoring.events.LINE,
            on_line,
        )
        sys.monitoring.set_events(TOOL_ID, sys.monitoring.events.LINE)
        print("result:", sample_work(4))
    finally:
        sys.monitoring.set_events(TOOL_ID, 0)
        sys.monitoring.free_tool_id(TOOL_ID)


if __name__ == "__main__":
    main()
