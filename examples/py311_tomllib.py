import tomllib
from pprint import pprint

DOCUMENT = """
[project]
name = "python-deep"
requires-python = ">=3.14"

[tool.study]
topics = ["pattern-matching", "runtime", "typing"]
weekly_hours = 6
"""


def main() -> None:
    parsed = tomllib.loads(DOCUMENT)
    pprint(parsed)


if __name__ == "__main__":
    main()
