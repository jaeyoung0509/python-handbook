# Added in Python 3.11: tomllib in the standard library.
# Python 3.11에서 추가: 표준 라이브러리 TOML 파서 tomllib.
# Why: pyproject.toml became a core packaging/config file and projects needed a built-in parser.
# 왜: pyproject.toml이 핵심 설정 파일이 되면서 내장 TOML 파서 필요성이 커졌다.
# Use when: reading TOML config without pulling in a third-party dependency.
# 언제 쓰나: 외부 의존성 없이 TOML 설정을 읽고 싶을 때 좋다.

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
    # tomllib.loads keeps the example small; use tomllib.load for real files.
    # 예제를 짧게 보이기 위해 loads를 썼고, 실제 파일은 tomllib.load가 더 자연스럽다.
    parsed = tomllib.loads(DOCUMENT)
    pprint(parsed)


if __name__ == "__main__":
    main()
