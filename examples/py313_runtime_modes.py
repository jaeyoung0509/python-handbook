import sys


def main() -> None:
    print("GIL enabled:", sys._is_gil_enabled())

    jit = getattr(sys, "_jit", None)
    if jit is None:
        print("JIT support: unavailable")
        return

    print("JIT available:", jit.is_available())
    print("JIT enabled:", jit.is_enabled())


if __name__ == "__main__":
    main()
