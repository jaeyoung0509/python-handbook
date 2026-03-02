# Execution Model

## 왜 중요한가

Python은 "해석되는 언어"라는 한 문장으로는 부족하다. parse, compile, code object, frame, bytecode 단위를 알아야 디버깅과 성능 감각이 생긴다.

## 이 장에서 채울 것

- source -> AST -> code object
- symbol table과 scope
- frame과 evaluation stack
- import가 실행 모델에 끼치는 영향

## 실전 연결

- circular import 이해
- closure / late binding 이해
- module import side effect 정리
