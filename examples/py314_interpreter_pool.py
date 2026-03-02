from concurrent.futures import InterpreterPoolExecutor


def square(value: int) -> int:
    return value * value


def main() -> None:
    with InterpreterPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(square, [1, 2, 3, 4]))
    print(results)


if __name__ == "__main__":
    main()
