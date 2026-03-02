# Added in Python 3.14: template strings via t"...".
# Python 3.14에서 추가: t"..." 형태의 template string.
# Why: f-strings immediately render to str, but some tools need the interpolation structure itself.
# 왜: f-string은 즉시 str이 되지만, 어떤 도구는 보간 구조 자체를 보존해야 한다.
# Use when: building templating, logging, i18n, or safe rendering layers that inspect expressions.
# 언제 쓰나: 템플릿 엔진, 로깅, i18n, 안전한 렌더링 계층 구현에 좋다.

from string.templatelib import Interpolation, Template


def main() -> None:
    language = "Python"
    version = 3.14
    # Unlike f"...", t"..." preserves the pieces and expressions as a Template object.
    # f-string과 달리 t-string은 조각과 표현식을 Template 객체로 보존한다.
    template = t"{language} {version=}"

    print("template type:", type(template))
    print("strings:", template.strings)
    print("values:", template.values)

    for interpolation in template.interpolations:
        assert isinstance(interpolation, Interpolation)
        # Each interpolation keeps both the computed value and the original expression text.
        # 각 interpolation은 계산된 값과 원래 표현식 문자열을 함께 들고 있다.
        print(
            "interpolation:",
            {
                "expression": interpolation.expression,
                "value": interpolation.value,
                "conversion": interpolation.conversion,
                "format_spec": interpolation.format_spec,
            },
        )

    assert isinstance(template, Template)


if __name__ == "__main__":
    main()
