# Runtime vs Static

## 왜 중요한가

Python typing은 정적 타입 체커용 정보이면서 동시에 일부 프레임워크의 런타임 metadata이기도 하다. 이 둘을 구분하지 못하면 혼란이 커진다.

## 이 장에서 채울 것

- 타입 체커가 보는 세계
- 런타임이 보는 어노테이션
- `Annotated` metadata
- `annotationlib`
- Pydantic / FastAPI가 어노테이션을 소비하는 방식

## 핵심 질문

- 타입 체커가 아는 것과 런타임이 아는 것은 왜 다른가?
- 어떤 annotation은 "타입"이고 어떤 annotation은 "metadata"인가?
