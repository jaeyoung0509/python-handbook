# Request / Response Modeling

<p class="lead">FastAPI에서 schema는 단순 validation 도구가 아니라 API 계약 그 자체다. 입력 DTO, 내부 command, ORM entity, 응답 DTO를 한 타입으로 합치기 시작하면 versioning, 보안, lazy load, 직렬화 비용이 같이 꼬인다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: `request model != response model != ORM model`을 기본값으로 두는 편이 훨씬 안전하다. API는 명시적 입력과 명시적 출력을 가져야 하고, ORM은 그 사이의 내부 구현으로 남는 편이 좋다.</p>
</div>

## 경계를 분리해서 보면 단순해진다

<MermaidDiagram
  caption="입력 DTO, 서비스 입력, ORM 저장 모델, 응답 DTO를 구분하면 API 진화와 persistence 변경이 서로 덜 영향을 준다."
  chart="flowchart LR; A[Request JSON] --> B[Pydantic Request DTO]; B --> C[Service Command]; C --> D[ORM Model]; D --> E[Response DTO]; E --> F[Response JSON];"
/>

## 기본 패턴

```py
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=80)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str
    created_at: datetime


PageSize = Annotated[int, Query(ge=1, le=100)]
```

## 왜 request와 response를 나누나

- create 요청에는 `password`, `invite_code` 같은 write-only 필드가 들어갈 수 있다.
- 응답에는 `id`, `created_at`, `status` 같은 server-generated 필드가 필요하다.
- 내부 저장 모델은 `password_hash`, `deleted_at`, `version` 같은 persistence 전용 컬럼을 가질 수 있다.

## response_model은 "필터"이자 "계약"이다

```py
@router.post(
    "/users",
    response_model=UserResponse,
    status_code=201,
)
async def create_user(payload: CreateUserRequest) -> UserResponse:
    ...
```

<p class="code-caption">FastAPI의 `response_model`은 문서화용 장식이 아니라, 실제로 응답 데이터를 필터링하고 직렬화 계약을 고정하는 경계다. 그래서 ORM 객체를 그대로 반환하기보다 응답 DTO를 명시적으로 만드는 편이 안전하다.</p>

## API를 오래 버티게 만드는 설계 기준

<div class="doc-checklist">
  <div class="check-card">
    <h3>입력/출력 분리</h3>
    <p>하나의 schema를 create, update, read에 재활용하지 않는다. 필드의 의미가 다르기 때문이다.</p>
  </div>
  <div class="check-card">
    <h3>서버 소유 필드 명확화</h3>
    <p>`id`, `created_at`, `updated_at`, `version`은 응답에만 두고 요청에서 받지 않는 편이 안전하다.</p>
  </div>
  <div class="check-card">
    <h3>페이지네이션과 에러 shape 고정</h3>
    <p>리스트 응답, 에러 응답은 초기에 shape를 정해두는 편이 API 진화 비용을 크게 줄인다.</p>
  </div>
  <div class="check-card">
    <h3>ORM 누수 차단</h3>
    <p>응답 직렬화 시 lazy load가 터지지 않게 DTO를 명시적으로 조립한다.</p>
  </div>
</div>

## 실전 규칙

- `CreateXRequest`, `UpdateXRequest`, `XResponse`를 분리한다.
- 응답 DTO는 공개 계약이므로 persistence 컬럼에 종속되지 않게 만든다.
- `Annotated`와 `Query`, `Path`, `Header`를 써서 입력 제약을 시그니처에서 드러낸다.
- 리스트 응답은 `items + page info` 구조를 일관되게 유지한다.

## 공식 자료

- [FastAPI Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)
- [FastAPI Query Parameters and String Validations](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/)
