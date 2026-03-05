# CPython runtime lab: dis, ast, gc, tracemalloc, sys.monitoring.
# CPython 런타임 실험: dis, ast, gc, tracemalloc, sys.monitoring.
# Why: runtime intuition improves when execution/memory behavior is observed directly.
# 왜: 실행/메모리 동작을 직접 관찰해야 런타임 감각이 빨리 올라간다.
# Use when: deep-diving CPython internals beyond high-level concepts.
# 언제 쓰나: CPython 내부 동작을 개념이 아니라 실험으로 확인하고 싶을 때.

from __future__ import annotations

import ast
import dis
import gc
import tracemalloc
from dataclasses import dataclass
from types import CodeType


def add_loop(n: int) -> int:
    total = 0
    for i in range(n):
        total += i
    return total


def show_ast_and_bytecode() -> None:
    source = "def f(x):\n    return x + 1\n"
    tree = ast.parse(source)
    print("AST dump:", ast.dump(tree, indent=2))
    print("\nBytecode for add_loop:")
    dis.dis(add_loop)


@dataclass(slots=True)
class Node:
    name: str
    ref: "Node | None" = None


def cycle_gc_lab() -> None:
    gc.collect()
    before = gc.get_count()

    a = Node("a")
    b = Node("b")
    a.ref = b
    b.ref = a

    del a
    del b

    collected = gc.collect()
    after = gc.get_count()
    print("gc count before:", before)
    print("gc count after:", after)
    print("collected cycles:", collected)


def tracemalloc_lab() -> None:
    tracemalloc.start()
    payload = [bytes(4096) for _ in range(512)]
    _ = payload
    snapshot = tracemalloc.take_snapshot()
    top = snapshot.statistics("lineno")[:3]
    print("top allocations:")
    for stat in top:
        print(stat)
    tracemalloc.stop()


def sys_monitoring_lab() -> None:
    import sys

    if not hasattr(sys, "monitoring"):
        print("sys.monitoring is unavailable in this build")
        return

    monitoring = sys.monitoring
    tool_id = 5

    events = monitoring.events.PY_START | monitoring.events.PY_RETURN
    calls: list[str] = []

    def on_start(code: CodeType, instruction_offset: int) -> None:
        calls.append(f"start:{code.co_name}@{instruction_offset}")

    def on_return(code: CodeType, instruction_offset: int, retval: object) -> None:
        calls.append(f"return:{code.co_name}@{instruction_offset}")
        _ = retval

    try:
        monitoring.use_tool_id(tool_id, "runtime-lab")
    except ValueError as exc:
        print(f"sys.monitoring tool id unavailable: {exc}")
        return

    monitoring.register_callback(tool_id, monitoring.events.PY_START, on_start)
    monitoring.register_callback(tool_id, monitoring.events.PY_RETURN, on_return)
    monitoring.set_events(tool_id, events)
    try:
        add_loop(10)
        print("sys.monitoring events sample:", calls[:6])
    finally:
        monitoring.set_events(tool_id, 0)
        monitoring.register_callback(tool_id, monitoring.events.PY_START, None)
        monitoring.register_callback(tool_id, monitoring.events.PY_RETURN, None)
        monitoring.free_tool_id(tool_id)


def main() -> None:
    print("== AST + Bytecode ==")
    show_ast_and_bytecode()
    print("\n== GC Cycle Lab ==")
    cycle_gc_lab()
    print("\n== tracemalloc Lab ==")
    tracemalloc_lab()
    print("\n== sys.monitoring Lab ==")
    sys_monitoring_lab()


if __name__ == "__main__":
    main()
