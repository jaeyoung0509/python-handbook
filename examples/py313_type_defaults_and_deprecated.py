# Added in Python 3.13: generic defaults, clearer locals() semantics, and warnings.deprecated.
# Python 3.13에서 추가: 제네릭 기본값, 더 명확해진 locals() 의미, warnings.deprecated.
# Why: generic APIs often need sensible defaults, and deprecations should reach tools and runtime together.
# 왜: 제네릭 API는 합리적인 기본값이 필요하고, deprecation 정보는 도구와 런타임에 함께 전달되는 편이 좋다.
# Use when: smoothing generic APIs, marking migrations, and understanding how locals() behaves in functions.
# 언제 쓰나: 제네릭 API 사용성 개선, API 이전 표시, 함수 내부 locals 동작 이해에 좋다.

import warnings


class Cache[K, V = str]:
    def __init__(self) -> None:
        self.store: dict[K, V] = {}

    def put(self, key: K, value: V) -> None:
        self.store[key] = value


@warnings.deprecated("use fetch_user_v2() instead")
def fetch_user(user_id: int) -> dict[str, str]:
    return {"id": str(user_id), "name": "legacy-user"}


def locals_snapshot_demo() -> tuple[int, int, int]:
    value = 10
    # locals() is not a writable "portal" into fast locals; treat it like a snapshot-like mapping.
    # locals()는 실제 fast locals를 직접 수정하는 통로가 아니라 snapshot에 가까운 매핑으로 보는 편이 안전하다.
    snapshot = locals()
    snapshot["value"] = 99
    return value, snapshot["value"], locals()["value"]


def main() -> None:
    warnings.simplefilter("always", DeprecationWarning)

    cache = Cache[int]()
    # V defaults to str here, so Cache[int] means Cache[int, str].
    # 여기서는 V의 기본값이 str이라서 Cache[int]는 사실상 Cache[int, str]처럼 동작한다.
    cache.put(1, "python")
    print("cache:", cache.store)

    for parameter in Cache.__type_params__:
        print("type param:", parameter, "default:", getattr(parameter, "__default__", None))

    # The warning is intentional here because the example is demonstrating the deprecation marker.
    # 여기서는 deprecation marker 시연이 목적이라 의도적으로 경고를 발생시킨다.
    print("deprecated call:", fetch_user(7))  # ty: ignore[deprecated]
    print("locals snapshot:", locals_snapshot_demo())


if __name__ == "__main__":
    main()
