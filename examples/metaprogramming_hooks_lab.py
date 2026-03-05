# Metaprogramming hook lab: __set_name__, __init_subclass__, class decorator, metaclass.
# 메타프로그래밍 훅 실험: __set_name__, __init_subclass__, class decorator, metaclass.
# Why: choose the smallest hook that solves the design problem.
# 왜: 문제를 해결하는 가장 작은 훅을 고르는 감각을 익히기 위함.
# Use when: designing declarative registration or class-level policy without overusing metaclasses.
# 언제 쓰나: 선언형 등록/클래스 정책을 만들 때 metaclass 남용을 피하고 싶을 때.

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, ClassVar


class PositiveInt:
    def __set_name__(self, owner: type, name: str) -> None:
        self.private_name = f"_{name}"

    def __get__(self, instance: object | None, owner: type | None = None) -> object:
        if instance is None:
            return self
        return getattr(instance, self.private_name)

    def __set__(self, instance: object, value: int) -> None:
        if value <= 0:
            raise ValueError("value must be positive")
        setattr(instance, self.private_name, value)


class Item:
    stock = PositiveInt()

    def __init__(self, stock: int) -> None:
        self.stock = stock


class HandlerBase:
    registry: dict[str, type["HandlerBase"]] = {}

    def __init_subclass__(cls, *, key: str | None = None, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if key is not None:
            HandlerBase.registry[key] = cls


class JsonHandler(HandlerBase, key="json"):
    pass


class CsvHandler(HandlerBase, key="csv"):
    pass


def tagged(name: str) -> Callable[[type], type]:
    def decorator(cls: type) -> type:
        tag_attr = "tag"
        setattr(cls, tag_attr, name)
        return dataclass(slots=True)(cls)

    return decorator


@tagged("billing")
class BillingConfig:
    tag: ClassVar[str]
    retries: int = 3
    timeout_seconds: int = 2


class NoMutableDefaults(type):
    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
    ) -> type:
        for key, value in namespace.items():
            if isinstance(value, (list, dict, set)):
                raise TypeError(f"{name}.{key} has mutable class default")
        return super().__new__(mcls, name, bases, namespace)


class SafePolicy(metaclass=NoMutableDefaults):
    retries = 3
    timeout_seconds = 10


def main() -> None:
    item = Item(stock=5)
    print("descriptor stock:", item.stock)

    print("subclass registry:", sorted(HandlerBase.registry))

    config = BillingConfig()
    print("class decorator tag:", BillingConfig.tag)
    print("class decorator dataclass:", config)

    print("metaclass policy class:", SafePolicy.__name__)


if __name__ == "__main__":
    main()
