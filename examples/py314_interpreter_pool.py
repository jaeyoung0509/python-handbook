# Added in Python 3.14: InterpreterPoolExecutor over multiple subinterpreters.
# Python 3.14에서 추가: 여러 서브인터프리터를 쓰는 InterpreterPoolExecutor.
# Why: Python needed a middle ground between threads and processes for isolation plus parallel work.
# 왜: Python에는 thread와 process 사이에서 격리와 병렬성을 함께 노릴 중간 지점이 필요했다.
# Use when: exploring subinterpreter-based parallelism for pure-Python tasks with separable state.
# 언제 쓰나: 상태 공유가 적은 순수 Python 작업에서 subinterpreter 병렬성을 실험할 때 좋다.

from concurrent.futures import InterpreterPoolExecutor


def square(value: int) -> int:
    return value * value


def main() -> None:
    # Each worker runs in its own interpreter, so state sharing is more restricted than with threads.
    # 각 worker는 별도 interpreter에서 돌기 때문에 thread보다 상태 공유 제약이 더 크다.
    with InterpreterPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(square, [1, 2, 3, 4]))
    print(results)


if __name__ == "__main__":
    main()
