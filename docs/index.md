---
layout: home

hero:
  name: Python Handbook
  text: Python 3.14 기준으로 다시 읽는 현대 Python
  tagline: Pythonic code, typing, CPython runtime, asyncio, FastAPI, Pydantic, SQLAlchemy 2.0을 한 흐름으로 묶은 한국어/영어 핸드북
  actions:
    - theme: brand
      text: 한국어로 시작하기
      link: /intro/
    - theme: alt
      text: Read in English
      link: /en/

features:
  - title: Bilingual by Default
    details: 루트는 한국어, `/en/`은 영어로 제공해서 같은 주제를 두 언어로 오갈 수 있습니다.
  - title: Readable Chapters
    details: 빠른 요약, 그림, 코드 예시, 체크리스트를 고정 패턴으로 써서 바로 이해할 수 있게 만듭니다.
  - title: Pythonic to Backend Stack
    details: metaclass, typing, runtime, asyncio부터 FastAPI, Pydantic, SQLAlchemy 2.0까지 이어집니다.
---

## 이 사이트를 어떻게 읽으면 좋은가

<div class="quick-takeaway">
  <p><strong>핵심 방향</strong>: 버전별 릴리즈 노트 모음이 아니라, Python 3.14를 기준선으로 두고 언어 감각부터 런타임, 웹 백엔드 스택까지 연결해서 읽는 핸드북입니다.</p>
</div>

<div class="reading-grid">
  <div class="reading-card">
    <h3>1. Pythonic 감각부터</h3>
    <p>descriptor, decorator, context manager, metaclass를 순서대로 읽으면서 Python 특유의 객체 모델을 먼저 잡습니다.</p>
  </div>
  <div class="reading-card">
    <h3>2. Typing을 설계 도구로</h3>
    <p>Annotated, Protocol, generics, narrowing을 문법이 아니라 API 설계와 경계 모델링 관점에서 봅니다.</p>
  </div>
  <div class="reading-card">
    <h3>3. Runtime을 그림으로</h3>
    <p>frame, bytecode, specialization, GIL, GC를 한 장면으로 묶어서 성능과 동작 이유를 같이 이해합니다.</p>
  </div>
  <div class="reading-card">
    <h3>4. FastAPI 스택으로 연결</h3>
    <p>asyncio, FastAPI, Pydantic, SQLAlchemy 2.0을 하나의 서비스 구조 안에서 정리합니다.</p>
  </div>
</div>

## 지금 들어가면 좋은 페이지

1. [입문 개요](/intro/)에서 전체 지도를 먼저 봅니다.
2. [Execution Model](/runtime/execution-model)에서 "Python이 실제로 어떻게 실행되는가"를 잡습니다.
3. [Metaclasses](/pythonic/metaclasses)에서 클래스 생성 시점을 이해합니다.
4. [FastAPI Project Structure](/fastapi/project-structure)에서 서비스 코드 구조를 실전 관점으로 연결합니다.

## 문서 패턴

- 빠른 요약: 이 페이지에서 꼭 남겨야 할 한 문장을 먼저 제시합니다.
- 그림: 흐름도나 비교 그림으로 개념 관계를 먼저 잡습니다.
- 코드: 실제로 복붙해서 돌려볼 수 있는 예제를 붙입니다.
- 체크리스트: 언제 쓰면 좋은지, 어디서 오용되는지 정리합니다.

## 현재 상태

- 한국어 루트와 영어 `/en/` 구조를 모두 열어뒀습니다.
- 대표 페이지부터 그림과 코드 예시가 있는 형식으로 확장하고 있습니다.
- 긴 문서는 점점 장 단위로 쪼개면서 읽기 좋게 정리할 예정입니다.
