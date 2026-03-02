# python-deep

Python 3.14, typing, CPython runtime, asyncio, FastAPI, Pydantic, SQLAlchemy 2.0까지 깊게 다루는 학습 저장소입니다.

문서 사이트 브랜딩은 `Python Handbook`으로 잡고, VitePress 기반으로 읽기 좋은 핸드북 형태로 확장하고 있습니다.

## 문서

- `docs/python-3.10-3.14-deep-dive.md`: 3.10~3.14 버전별 핵심 변화, 왜 들어왔는지, 런타임/타입 시스템 관점의 의미
- `docs/cpython-vs-go-runtime.md`: CPython 내부 동작과 Go 런타임 비교
- `docs/`: VitePress 사이트 루트

## 예제

- `examples/README.md`: 버전별 예제 설명과 실행 방법

모든 예제는 저장소의 `.venv`에 있는 Python 3.14.3 기준으로 점검했습니다.

## 타입 체크

이 저장소는 VS Code에서 `pyright` 대신 `ty`를 쓰도록 워크스페이스 설정을 포함합니다.

- `uv run ty check`: 전체 워크스페이스 타입 체크
- `uv run ruff check .`: 엄격한 annotation/lint 체크
- `.vscode/settings.json`: `python.languageServer = "None"` + `ty.diagnosticMode = "workspace"`

## 문서 사이트 실행

```bash
npm install
npm run docs:dev
```

배포용 빌드:

```bash
npm run docs:build
```

예시 실행:

```bash
./.venv/bin/python examples/py310_pattern_matching.py
./.venv/bin/python examples/py311_exception_groups_and_taskgroup.py
./.venv/bin/python examples/py314_interpreter_pool.py
```
