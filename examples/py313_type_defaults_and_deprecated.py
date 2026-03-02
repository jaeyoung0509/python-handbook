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
    snapshot = locals()
    snapshot["value"] = 99
    return value, snapshot["value"], locals()["value"]


def main() -> None:
    warnings.simplefilter("always", DeprecationWarning)

    cache = Cache[int]()
    cache.put(1, "python")
    print("cache:", cache.store)

    for parameter in Cache.__type_params__:
        print("type param:", parameter, "default:", getattr(parameter, "__default__", None))

    print("deprecated call:", fetch_user(7))  # ty: ignore[deprecated]
    print("locals snapshot:", locals_snapshot_demo())


if __name__ == "__main__":
    main()
