type Row[T] = dict[str, T]


class Box[T]:
    def __init__(self, value: T) -> None:
        self.value = value

    def unwrap(self) -> T:
        return self.value


def first[T](items: list[T]) -> T:
    return items[0]


def main() -> None:
    row: Row[int] = {"age": 30, "score": 97}
    box = Box("python")

    print("row:", row)
    print("box:", box.unwrap())
    print("first:", first([10, 20, 30]))
    print("Box type params:", Box.__type_params__)
    print("first type params:", first.__type_params__)


if __name__ == "__main__":
    main()
