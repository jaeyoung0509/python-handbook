from collections.abc import Callable
from typing import ParamSpec, TypeAlias, TypeGuard, TypeVar

P = ParamSpec("P")
R = TypeVar("R")
NumberLike: TypeAlias = int | float


def traced(func: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"calling {func!r} args={args} kwargs={kwargs}")
        return func(*args, **kwargs)

    return wrapper


def is_str_list(values: list[object]) -> TypeGuard[list[str]]:
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
    print("strict zip:", list(zip(left, right, strict=True)))


if __name__ == "__main__":
    main()
