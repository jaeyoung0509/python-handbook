---
layout: home

hero:
  name: Python Handbook
  text: Python 3.14부터 FastAPI, Pydantic, SQLAlchemy 2.0까지
  tagline: Pythonic code, typing, CPython runtime, asyncio, web backend, data validation, ORM을 한 흐름으로 읽는 문서 사이트
  actions:
    - theme: brand
      text: Start Reading
      link: /intro/
    - theme: alt
      text: Explore Runtime
      link: /runtime/

features:
  - title: Pythonic Python
    details: data model, descriptor, decorator, context manager, metaclass를 Python 3.14 감각으로 다시 잡습니다.
  - title: Modern Typing
    details: Annotated, generics, protocols, narrowing, runtime introspection을 실무 중심으로 정리합니다.
  - title: CPython Runtime
    details: bytecode, specialization, memory, GC, GIL, subinterpreter를 내부 동작 관점에서 설명합니다.
  - title: Asyncio
    details: event loop, cancellation, TaskGroup, backpressure, testing을 서비스 코드 관점에서 다룹니다.
  - title: FastAPI and Pydantic
    details: 잘 쓰는 구조와 validation pipeline, pydantic-core 내부 감각까지 연결합니다.
  - title: SQLAlchemy 2.0
    details: Core, ORM, Session, loading strategy, async, migration pattern을 깊게 다룹니다.
---

## What This Site Is

이 사이트는 "Python 3.14 기준으로 다시 배우는 현대 Python"을 목표로 한다.

핵심 방향:

- 버전별 기능 나열보다 주제별 이해를 우선한다.
- 문법 설명에서 끝내지 않고 내부 동작과 실전 패턴까지 연결한다.
- FastAPI, Pydantic, SQLAlchemy 2.0을 따로 떼지 않고 Python 본체와 이어서 설명한다.

## Recommended Path

1. [Intro](/intro/)에서 전체 구조와 읽는 순서를 잡는다.
2. [Pythonic](/pythonic/)과 [Typing](/typing/)으로 언어 감각을 다시 만든다.
3. [Runtime](/runtime/)과 [Asyncio](/asyncio/)로 내부 모델을 잡는다.
4. [FastAPI](/fastapi/), [Pydantic](/pydantic/), [SQLAlchemy](/sqlalchemy/)를 실전 스택으로 읽는다.

## Current Status

- 기존 `Python 3.10~3.14` 변화 문서와 `CPython vs Go runtime` 문서는 이미 포함되어 있다.
- 나머지 섹션은 지금부터 장 단위로 확장하기 위한 문서 뼈대를 제공한다.
- 이 구조를 기준으로 문서를 하나씩 "Python 핸드북" 형태로 채워가면 된다.
