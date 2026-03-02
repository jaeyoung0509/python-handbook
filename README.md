# python-deep

CPython 3.10~3.14 변화와 내부 동작을 깊게 따라가는 학습 저장소입니다.

## 문서

- `docs/python-3.10-3.14-deep-dive.md`: 3.10~3.14 버전별 핵심 변화, 왜 들어왔는지, 런타임/타입 시스템 관점의 의미
- `docs/cpython-vs-go-runtime.md`: CPython 내부 동작과 Go 런타임 비교

## 예제

- `examples/README.md`: 버전별 예제 설명과 실행 방법

모든 예제는 저장소의 `.venv`에 있는 Python 3.14.3 기준으로 점검했습니다.

예시 실행:

```bash
./.venv/bin/python examples/py310_pattern_matching.py
./.venv/bin/python examples/py311_exception_groups_and_taskgroup.py
./.venv/bin/python examples/py314_interpreter_pool.py
```
