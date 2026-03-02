# Added in Python 3.10: structural pattern matching.
# Python 3.10에서 추가: 구조적 패턴 매칭.
# Why: shape-based branching used to require long if/elif chains with isinstance checks.
# 왜: 데이터 형태 기준 분기는 예전엔 긴 if/elif + isinstance 검사로 풀어야 했다.
# Use when: dispatching JSON events, AST nodes, command messages, or protocol payloads.
# 언제 쓰나: JSON 이벤트, AST 노드, 명령 메시지, 프로토콜 payload 분기에 좋다.

from dataclasses import dataclass


@dataclass
class Point:
    x: int
    y: int


def describe(value: object) -> str:
    match value:
        # Mapping patterns are useful when incoming data is dict-shaped.
        # 매핑 패턴은 입력 데이터가 dict 형태일 때 특히 읽기 좋다.
        case {"kind": "event", "name": name, "payload": payload}:
            return f"event<{name}> payload={payload}"
        # Sequence patterns make "head + rest" parsing much cleaner.
        # 시퀀스 패턴은 "첫 원소 + 나머지" 분해를 훨씬 자연스럽게 만든다.
        case [head, *tail]:
            return f"sequence head={head} tail={tail}"
        # Class patterns pair well with dataclasses and domain objects.
        # 클래스 패턴은 dataclass나 도메인 객체 분기에 잘 맞는다.
        case Point(x, y) if x == y:
            return f"diagonal point ({x}, {y})"
        case Point(x, y):
            return f"point ({x}, {y})"
        case int() | float() as number if number >= 0:
            return f"non-negative number {number}"
        case _:
            return f"unknown<{type(value).__name__}>"


def main() -> None:
    samples = [
        {"kind": "event", "name": "user.created", "payload": {"id": 7}},
        [1, 2, 3, 4],
        Point(3, 3),
        Point(3, 5),
        2.5,
        None,
    ]
    for sample in samples:
        print(describe(sample))


if __name__ == "__main__":
    main()
