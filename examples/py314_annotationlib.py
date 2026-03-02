# Added in Python 3.14: deferred annotation evaluation plus annotationlib.
# Python 3.14에서 추가: 지연 평가 어노테이션과 annotationlib.
# Why: frameworks need to inspect annotations without forcing early evaluation or string hacks.
# 왜: 프레임워크는 어노테이션을 너무 일찍 평가하지 않고도 안전하게 읽을 수 있어야 한다.
# Use when: reading forward references, dependency metadata, or framework annotations safely.
# 언제 쓰나: forward reference, 의존성 메타데이터, 프레임워크 어노테이션을 안전하게 읽을 때 좋다.

import annotationlib


def build() -> Later:
    return Later()


class Later:
    def __repr__(self) -> str:
        return "Later()"


def main() -> None:
    # STRING format lets tools inspect the original expression before resolving it to a runtime object.
    # STRING 포맷은 런타임 객체로 해석하기 전에 원래 표현식을 그대로 살펴보게 해준다.
    print(
        "string annotations:",
        annotationlib.get_annotations(build, format=annotationlib.Format.STRING),
    )
    print("evaluated annotations:", build.__annotations__)
    print("call result:", build())


if __name__ == "__main__":
    main()
