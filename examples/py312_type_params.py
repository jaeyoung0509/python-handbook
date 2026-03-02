# Added in Python 3.12: type parameter syntax and the type alias statement.
# Python 3.12에서 추가: 타입 파라미터 문법과 type alias 문.
# Why: TypeVar + Generic boilerplate made generic APIs noisy and harder to read.
# 왜: TypeVar + Generic 조합은 제네릭 API를 장황하게 만들고 읽기 어렵게 했다.
# Use when: defining library-style containers, helpers, and aliases that should stay strongly typed.
# 언제 쓰나: 강한 타입 정보를 유지하는 컨테이너, 헬퍼 함수, 별칭 설계에 좋다.

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
    # __type_params__ is useful when studying what the compiler recorded for generic declarations.
    # __type_params__를 보면 컴파일러가 제네릭 선언에서 어떤 타입 파라미터를 기록했는지 볼 수 있다.
    print("Box type params:", Box.__type_params__)
    print("first type params:", first.__type_params__)


if __name__ == "__main__":
    main()
