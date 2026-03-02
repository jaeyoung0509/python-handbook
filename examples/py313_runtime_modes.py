# Added in Python 3.13: experimental free-threaded builds and an experimental JIT.
# Python 3.13에서 추가: 실험적 free-threaded 빌드와 실험적 JIT.
# Why: CPython is exploring better CPU parallelism and faster hot-path execution.
# 왜: CPython이 더 나은 CPU 병렬성과 더 빠른 hot path 실행을 탐색하기 시작했기 때문이다.
# Use when: inspecting the current runtime mode in benchmarks, experiments, and CI diagnostics.
# 언제 쓰나: 벤치마크, 실험, CI 진단에서 현재 런타임 모드를 확인할 때 좋다.

import sys


def main() -> None:
    print("GIL enabled:", sys._is_gil_enabled())

    jit = getattr(sys, "_jit", None)
    if jit is None:
        print("JIT support: unavailable")
        return

    # "available" means the build supports the JIT; "enabled" means the current process is using it.
    # available은 빌드가 JIT를 지원한다는 뜻이고, enabled는 현재 프로세스가 실제로 쓰고 있다는 뜻이다.
    print("JIT available:", jit.is_available())
    print("JIT enabled:", jit.is_enabled())


if __name__ == "__main__":
    main()
