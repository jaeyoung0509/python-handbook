import annotationlib


def build() -> Later:
    return Later()


class Later:
    def __repr__(self) -> str:
        return "Later()"


def main() -> None:
    print(
        "string annotations:",
        annotationlib.get_annotations(build, format=annotationlib.Format.STRING),
    )
    print("evaluated annotations:", build.__annotations__)
    print("call result:", build())


if __name__ == "__main__":
    main()
