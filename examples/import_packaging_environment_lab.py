from __future__ import annotations

# What this lab adds / 이 예제가 추가하는 것:
# - Show how `python file.py` and `python -m package` differ.
# - `python file.py` 와 `python -m package` 실행 문맥 차이를 보여준다.
# - Show that imports are cached through `sys.modules`.
# - import가 `sys.modules` cache를 통해 재사용된다는 점을 보여준다.
# - Show what `pyproject.toml` and virtualenv metadata are solving.
# - `pyproject.toml` 과 가상환경 metadata가 어떤 문제를 푸는지 보여준다.
#
# Why it was added / 왜 추가되었나:
# - Import and packaging bugs are among the most common Python fundamentals gaps.
# - import/package 관련 버그는 Python fundamentals에서 가장 자주 비는 축 중 하나다.
# - Teams often treat source layout, install layout, and runtime interpreter as the same thing.
# - 소스 레이아웃, 설치 레이아웃, 실행 인터프리터를 같은 것으로 착각하는 경우가 많다.
#
# When to use this / 언제 보면 좋은가:
# - When relative imports break and the error looks random.
# - relative import가 랜덤하게 깨지는 것처럼 보일 때.
# - When local execution works but packaging or CI behaves differently.
# - 로컬 실행은 되는데 packaging 또는 CI 동작이 다를 때.
import importlib
import os
import subprocess
import sys
import tempfile
import textwrap
import tomllib
from pathlib import Path


def write_demo_package(root: Path) -> None:
    package_dir = root / "demo_pkg"
    package_dir.mkdir()

    (package_dir / "__init__.py").write_text(
        textwrap.dedent(
            """\
            package_label = "demo-pkg"
            """
        ),
        encoding="utf-8",
    )

    (package_dir / "helper.py").write_text(
        textwrap.dedent(
            """\
            def plus_one(value: int) -> int:
                return value + 1
            """
        ),
        encoding="utf-8",
    )

    (package_dir / "tool.py").write_text(
        textwrap.dedent(
            """\
            from .helper import plus_one


            def describe() -> str:
                return f"tool says {plus_one(41)}"


            if __name__ == "__main__":
                print(describe())
            """
        ),
        encoding="utf-8",
    )

    (package_dir / "__main__.py").write_text(
        textwrap.dedent(
            """\
            from .tool import describe

            print(f"python -m demo_pkg -> {describe()}")
            """
        ),
        encoding="utf-8",
    )

    (package_dir / "side_effect_module.py").write_text(
        textwrap.dedent(
            """\
            print("side_effect_module executed")
            counter = 1
            """
        ),
        encoding="utf-8",
    )


def demonstrate_module_cache(root: Path) -> None:
    print("== import cache via sys.modules ==")
    sys.path.insert(0, str(root))
    try:
        importlib.invalidate_caches()

        first_module = importlib.import_module("demo_pkg.side_effect_module")
        second_module = importlib.import_module("demo_pkg.side_effect_module")
        reloaded_module = importlib.reload(first_module)

        print(f"same module object on repeated import: {first_module is second_module}")
        print(f"reload keeps the module identity: {first_module is reloaded_module}")
        print(
            "module cached in sys.modules:",
            "demo_pkg.side_effect_module" in sys.modules,
        )
    finally:
        sys.path.pop(0)
        sys.modules.pop("demo_pkg.side_effect_module", None)
        sys.modules.pop("demo_pkg", None)


def run_subprocess(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cwd)
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def demonstrate_execution_context(root: Path) -> None:
    print("\n== execution context: file path vs module ==")
    script_result = run_subprocess(
        [sys.executable, str(root / "demo_pkg" / "tool.py")],
        cwd=root,
    )
    module_result = run_subprocess([sys.executable, "-m", "demo_pkg"], cwd=root)

    print(f"file execution exit code: {script_result.returncode}")
    print(f"file execution stderr head: {script_result.stderr.strip().splitlines()[0]}")
    print(f"module execution exit code: {module_result.returncode}")
    print(f"module execution stdout: {module_result.stdout.strip()}")


def demonstrate_pyproject_metadata() -> None:
    print("\n== pyproject metadata ==")
    pyproject_text = textwrap.dedent(
        """\
        [build-system]
        requires = ["hatchling"]
        build-backend = "hatchling.build"

        [project]
        name = "demo-pkg"
        version = "0.1.0"
        requires-python = ">=3.14"

        [project.scripts]
        demo-cli = "demo_pkg.tool:describe"
        """
    )
    metadata = tomllib.loads(pyproject_text)
    project_table = metadata["project"]
    scripts = project_table["scripts"]

    print(f"project name: {project_table['name']}")
    print(f"requires-python: {project_table['requires-python']}")
    print(f"declared entry point: demo-cli -> {scripts['demo-cli']}")


def demonstrate_virtual_environment_signal() -> None:
    print("\n== virtual environment signal ==")
    print(f"sys.executable: {sys.executable}")
    print(f"sys.prefix: {sys.prefix}")
    print(f"sys.base_prefix: {sys.base_prefix}")
    print(f"running inside virtualenv: {sys.prefix != sys.base_prefix}")


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        write_demo_package(root)
        demonstrate_module_cache(root)
        demonstrate_execution_context(root)
        demonstrate_pyproject_metadata()
        demonstrate_virtual_environment_signal()


if __name__ == "__main__":
    main()
