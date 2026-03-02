from string.templatelib import Interpolation, Template


def main() -> None:
    language = "Python"
    version = 3.14
    template = t"{language} {version=}"

    print("template type:", type(template))
    print("strings:", template.strings)
    print("values:", template.values)

    for interpolation in template.interpolations:
        assert isinstance(interpolation, Interpolation)
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
