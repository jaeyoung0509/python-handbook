# Added in Python 3.10: ParamSpec, TypeGuard, and better union syntax ergonomics.
# Python 3.10에서 추가: ParamSpec, TypeGuard, 그리고 더 자연스러운 union 문법.
# Why: decorators and runtime validators were hard to type precisely before 3.10.
# 왜: 3.10 이전에는 데코레이터와 런타임 검증 함수를 정확히 타입 지정하기가 불편했다.
# Use when: preserving call signatures, narrowing types after checks, and preventing silent zip bugs.
# 언제 쓰나: 호출 시그니처 보존, 검사 뒤 타입 좁히기, zip 관련 조용한 버그 방지에 좋다.

from collections.abc import Callable
from typing import ParamSpec, TypeAlias, TypeGuard, TypeVar

P = ParamSpec("P")
R = TypeVar("R")
NumberLike: TypeAlias = int | float


def traced(func: Callable[P, R]) -> Callable[P, R]:
    # ParamSpec keeps the wrapped function's parameter list instead of collapsing it to Any.
    # ParamSpec은 래핑된 함수의 인자 목록을 Any로 무너뜨리지 않고 그대로 보존한다.
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"calling {func!r} args={args} kwargs={kwargs}")
        return func(*args, **kwargs)

    return wrapper


def is_str_list(values: list[object]) -> TypeGuard[list[str]]:
    # TypeGuard tells the type checker that a True result narrows list[object] to list[str].
    # TypeGuard는 True일 때 list[object]를 list[str]로 좁혀도 된다고 타입 체커에 알려준다.
    return all(isinstance(value, str) for value in values)


@traced
def add(x: NumberLike, y: NumberLike) -> NumberLike:
    return x + y


def main() -> None:
    print(add(2, 3.5))

    values: list[object] = ["python", "typing", "3.10"]
    if is_str_list(values):
        print("upper-cased:", [value.upper() for value in values])

    left = [1, 2, 3]
    right = ["a", "b", "c"]
    # strict=True is best when the two iterables must stay perfectly aligned.
    # strict=True는 두 iterable 길이가 반드시 일치해야 하는 데이터 처리에서 특히 중요하다.
    print("strict zip:", list(zip(left, right, strict=True)))


if __name__ == "__main__":
    main()
