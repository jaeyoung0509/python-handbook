from dataclasses import dataclass


@dataclass
class Point:
    x: int
    y: int


def describe(value: object) -> str:
    match value:
        case {"kind": "event", "name": name, "payload": payload}:
            return f"event<{name}> payload={payload}"
        case [head, *tail]:
            return f"sequence head={head} tail={tail}"
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
