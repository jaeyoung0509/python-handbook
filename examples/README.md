# Examples

모든 예제는 `.venv`의 Python 3.14.3에서 확인했다.

## 3.10

- `py310_pattern_matching.py`: `match/case`, 시퀀스/매핑/클래스 패턴
- `py310_typing_and_zip_strict.py`: `|` 유니언, `ParamSpec`, `TypeGuard`, `zip(strict=True)`

## 3.11

- `py311_exception_groups_and_taskgroup.py`: `ExceptionGroup`, `except*`, `asyncio.TaskGroup`
- `py311_tomllib.py`: 표준 라이브러리 TOML 파서

## 3.12

- `py312_type_params.py`: 새 제네릭 문법과 `type` 별칭
- `py312_sys_monitoring.py`: 저비용 인터프리터 이벤트 관측

## 3.13

- `py313_type_defaults_and_deprecated.py`: 타입 파라미터 기본값과 `warnings.deprecated`
- `py313_runtime_modes.py`: GIL/JIT 런타임 모드 탐지

## 3.14

- `py314_annotationlib.py`: 지연 평가 어노테이션과 `annotationlib`
- `py314_template_strings.py`: `t"..."`와 `string.templatelib`
- `py314_interpreter_pool.py`: `InterpreterPoolExecutor`

예시 실행:

```bash
./.venv/bin/python examples/py312_type_params.py
./.venv/bin/python examples/py313_runtime_modes.py
./.venv/bin/python examples/py314_template_strings.py
```
