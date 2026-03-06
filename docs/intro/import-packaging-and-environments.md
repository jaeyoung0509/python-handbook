# Import, Packaging, and Environment

<p class="lead">Python에서는 import, package layout, build metadata, virtual environment가 따로 노는 주제가 아니다. 이 네 가지는 "코드를 어떻게 찾고", "어떻게 설치하고", "어떤 인터프리터에서 실행할지"를 함께 결정한다. 이 축이 흐리면 circular import, `python -m` 오해, editable install 착시, 로컬에서는 되는데 배포에서 깨지는 문제가 반복된다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: import system은 실행 그래프를 만들고, packaging은 설치 가능한 아티팩트를 만들며, virtual environment는 의존성 격리를 만든다. 대부분의 Python 프로젝트 문제는 이 세 층을 섞어서 생각할 때 생긴다.</p>
</div>

<MermaidDiagram
  caption="Python 실행은 소스 파일 하나를 여는 것이 아니라, interpreter startup, `sys.path`, module spec, loader, package metadata가 함께 맞물리는 과정이다."
  chart="flowchart LR; A[&quot;Interpreter startup&quot;] --> B[&quot;sys.path construction&quot;]; B --> C[&quot;finder / loader&quot;]; C --> D[&quot;module spec&quot;]; D --> E[&quot;sys.modules cache&quot;]; E --> F[&quot;package import or entry point&quot;]; F --> G[&quot;runtime side effects&quot;];"
/>

## 왜 이 축이 중요한가

- `import`는 단순 파일 include가 아니라 module object 생성과 cache 등록 과정이다.
- package layout은 "어디서 import가 성공하느냐"를 바꾼다.
- `pyproject.toml`은 build backend, project metadata, entry point를 결정한다.
- `venv`는 같은 프로젝트라도 어떤 site-packages를 보게 되는지 바꾼다.

즉, Python 프로젝트는 source tree만 이해해서는 부족하다. interpreter가 그 tree를 어떤 규칙으로 읽는지까지 알아야 한다.

## 1) 실행 문맥: `python file.py`와 `python -m package.module`은 다르다

이 차이를 모르면 relative import 에러를 반복하게 된다.

| 실행 방식 | `sys.path[0]` 기준 | package context | 보통 언제 쓰나 |
| --- | --- | --- | --- |
| `python script.py` | 스크립트 파일이 있는 디렉터리 | 약함 | 단발성 스크립트, 실험 코드 |
| `python -m package.module` | 현재 작업 디렉터리 | 강함 | 패키지 내부 모듈 실행 |
| console script entry point | 설치된 환경의 wrapper | 강함 | 배포된 CLI |

```py
# src/myapp/cli.py
from .service import main

if __name__ == "__main__":
    main()
```

`cli.py`를 파일 경로로 직접 실행하면 `from .service import main` 같은 relative import가 실패할 수 있다. 반면 `python -m myapp.cli`는 package context를 세운 뒤 실행하므로 같은 코드가 정상 동작한다.

<p class="code-caption">Python은 파일 경로를 실행할 때와 패키지 모듈을 실행할 때 import 기준점을 다르게 둔다. 애플리케이션 코드를 패키지 내부에 넣는다면 `python -m ...` 또는 console script 기준으로 생각하는 편이 안전하다.</p>

## 2) import system은 실제로 어떻게 동작하나

import 한 줄이 일어날 때 내부에서는 대체로 이런 순서를 따른다.

1. `sys.modules`에서 이미 로드된 모듈이 있는지 확인한다.
2. 없으면 finder가 module spec을 찾는다.
3. loader가 module object를 만들고 코드를 실행한다.
4. 실행 결과 module object가 `sys.modules`에 남는다.

### `sys.modules`: import cache의 핵심

- 같은 프로세스 안에서 같은 모듈은 보통 한 번만 import code가 실행된다.
- 두 번째 import는 파일을 다시 읽기보다 기존 module object를 재사용한다.
- `importlib.reload()`는 reload용 도구이지, 설계 문제를 덮는 해법이 아니다.

이 cache 때문에 top-level side effect가 과하면 앱 시작 순서가 import 순서에 묶인다.

### `sys.path`: 어디를 import 대상으로 볼 것인가

`sys.path`는 보통 아래 요소들의 조합으로 만들어진다.

- 실행한 스크립트 디렉터리 또는 현재 작업 디렉터리
- 표준 라이브러리 경로
- 현재 interpreter의 site-packages
- `PYTHONPATH`가 있다면 그 경로

여기서 중요한 점은 "프로젝트 루트처럼 보이는 경로"와 "실제로 import 가능한 경로"가 다를 수 있다는 것이다.

## 3) circular import는 왜 생기나

circular import의 본질은 두 파일이 서로를 import한다는 사실 자체보다, 두 모듈이 초기화 중간 상태에서 서로의 이름을 필요로 한다는 점에 있다.

### 전형적인 실패 패턴

```py
# users/service.py
from users.repository import UserRepository

SERVICE_NAME = "users"
```

```py
# users/repository.py
from users.service import SERVICE_NAME
```

`service.py`가 아직 끝까지 실행되지 않았는데 `repository.py`가 `SERVICE_NAME`을 찾으러 들어오면 partially initialized module 상태가 드러난다.

### 보통 더 나은 해법

- shared type / constant를 별도 module로 뺀다.
- import를 함수 내부로 숨기기 전에 module 경계를 다시 본다.
- route, service, repository, schema가 서로 순환 참조하지 않도록 계층을 정리한다.

함수 내부 import는 응급처치일 수는 있어도 구조 문제를 자주 숨긴다.

## 4) package layout: flat보다 `src/` 레이아웃이 왜 자주 권장되나

```text
project/
  pyproject.toml
  src/
    myapp/
      __init__.py
      __main__.py
      cli.py
      service.py
  tests/
```

`src/` layout이 주는 가장 큰 장점은 "설치된 패키지"와 "현재 작업 디렉터리"를 구분하게 만든다는 점이다.

### `src/` layout이 좋은 이유

- 로컬에서 우연히 import되던 코드가 배포에서 깨지는 문제를 빨리 드러낸다.
- editable install을 했다는 전제를 더 분명하게 만든다.
- tests가 소스 트리를 직접 주워다 쓰는 착시를 줄인다.

### `__init__.py`는 언제 필요한가

- 전통적인 package로 만들려면 둔다.
- namespace package가 목적이라면 없을 수도 있다.
- 대부분의 서비스 코드베이스에서는 명시적인 `__init__.py`가 더 읽기 쉽다.

namespace package는 강력하지만, import 추론과 도구 설정이 더 복잡해질 수 있다.

## 5) `pyproject.toml`: Python 프로젝트의 계약서

현대 Python packaging의 중심은 `pyproject.toml`이다.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "myapp"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = ["fastapi>=0.135", "sqlalchemy>=2.0"]

[project.scripts]
myapp = "myapp.cli:main"
```

여기서 같이 결정되는 것:

- build backend는 무엇인가
- 배포 metadata는 무엇인가
- 어떤 Python 버전을 요구하는가
- CLI entry point는 무엇인가

### wheel vs sdist

| 아티팩트 | 의미 | 언제 중요하나 |
| --- | --- | --- |
| wheel | 설치용 빌드 결과물 | 재현 가능한 설치, 빠른 배포 |
| sdist | 소스 배포본 | build 과정 검증, 배포 파이프라인 |

실무에서는 "내 로컬에서는 된다"가 아니라 "빌드된 wheel이 어디서나 같은 방식으로 설치된다"가 더 중요하다.

### editable install이 실제로 뜻하는 것

editable install(PEP 660)은 source tree와 설치 환경을 느슨하게 연결해 준다. 개발 중에는 편하지만, 이 때문에 "설치 안 해도 import가 되네?"라는 착시가 생기기 쉽다.

editable install은 편의 장치지, packaging 이해를 대체하지 않는다.

## 6) virtual environment는 무엇을 격리하고 무엇은 격리하지 않나

`venv`는 interpreter와 site-packages 관점을 분리한다.

- 격리하는 것: 설치된 패키지 집합, 실행용 Python binary 경로, script entry point 위치
- 격리하지 않는 것: 운영체제 프로세스, 파일시스템, 환경변수 자체, 네트워크 접근

### 실무에서 중요한 확인 포인트

- `sys.prefix != sys.base_prefix`면 보통 virtual environment 안이다.
- `which python`과 `python -V`보다 `python -c "import sys; print(sys.executable)"`가 더 정확할 때가 많다.
- VS Code, pytest, CI가 같은 interpreter를 보는지 항상 확인해야 한다.

## 7) entry point와 CLI는 어떻게 이어지나

`[project.scripts]`에 아래처럼 선언하면:

```toml
[project.scripts]
myapp = "myapp.cli:main"
```

설치 시 `myapp` 실행 파일(wrapper)이 생긴다. 이 wrapper는 적절한 interpreter와 import path를 잡은 뒤 `myapp.cli:main`을 호출한다.

즉, 운영 CLI는 `python some/file.py`보다 entry point 실행 기준으로 설계하는 편이 더 견고하다.

## 8) 자주 깨지는 지점

### import 관련

- top-level에서 DB 연결, HTTP 호출, 설정 로딩 같은 side effect를 바로 실행한다.
- route와 repository가 서로 import한다.
- 테스트가 working directory 우연에 기대어 import된다.

### packaging 관련

- `pyproject.toml` metadata와 실제 package layout이 어긋난다.
- CLI는 파일 경로 실행을 기준으로 만들고, 배포는 console script로 한다.
- editable install만 기준으로 개발해 wheel 설치 검증이 없다.

### environment 관련

- shell의 Python, editor의 Python, CI의 Python이 서로 다르다.
- `.venv`를 쓰지만 `uv run`, `pytest`, `python`이 같은 interpreter를 보는지 확인하지 않는다.

## 추천 작업 규칙

<div class="doc-checklist">
  <div class="check-card">
    <h3>`src/` layout을 기본값으로 생각한다</h3>
    <p>설치와 import를 분리해서 로컬 착시를 줄인다.</p>
  </div>
  <div class="check-card">
    <h3>앱 코드는 `python -m` 기준으로도 실행 가능해야 한다</h3>
    <p>패키지 내부 상대 import를 파일 경로 실행에 기대지 않는다.</p>
  </div>
  <div class="check-card">
    <h3>top-level side effect를 최소화한다</h3>
    <p>import 시점과 런타임 초기화 시점을 분리한다.</p>
  </div>
  <div class="check-card">
    <h3>wheel 설치 검증을 한 번은 해본다</h3>
    <p>editable install만으로 packaging이 맞다고 가정하지 않는다.</p>
  </div>
</div>

## 이 저장소에서 같이 보면 좋은 곳

1. [Execution Model](/runtime/execution-model)
2. [Settings and Pydantic Settings](/playbooks/settings-and-pydantic-settings)
3. [ASGI와 Uvicorn](/fastapi/asgi-and-uvicorn)

실행 감각은 `examples/import_packaging_environment_lab.py`와 같이 보면 좋다.

## 공식 자료

- [The import system](https://docs.python.org/3/reference/import.html)
- [importlib](https://docs.python.org/3/library/importlib.html)
- [venv](https://docs.python.org/3/library/venv.html)
- [Packaging Python Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [PEP 451 - A ModuleSpec Type for the Import System](https://peps.python.org/pep-0451/)
- [PEP 517 - Build-system independent format](https://peps.python.org/pep-0517/)
- [PEP 621 - Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
- [PEP 660 - Editable installs](https://peps.python.org/pep-0660/)
