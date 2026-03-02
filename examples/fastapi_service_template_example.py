# Modern FastAPI service boundaries with DTOs, services, repositories, and one session per request.
# 현대 FastAPI 서비스 경계: DTO, service, repository, 요청당 하나의 session.
# Why: production FastAPI code gets messy when routes own validation, transactions, and ORM details together.
# 왜: route가 validation, transaction, ORM 세부 구현을 한꺼번에 쥐면 FastAPI 서비스가 금방 꼬인다.
# Use when: learning how request DTOs, services, repositories, and response DTOs should fit together.
# 언제 쓰나: request DTO, service, repository, response DTO를 어떻게 분리할지 감을 잡을 때 좋다.

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))


class CreateUserRequest(BaseModel):
    email: str
    name: str = Field(min_length=1, max_length=80)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str


class DuplicateEmail(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(email)


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> UserRecord | None:
        stmt = select(UserRecord).where(UserRecord.email == email)
        return self.session.scalar(stmt)

    def get(self, user_id: int) -> UserRecord | None:
        return self.session.get(UserRecord, user_id)

    def add(self, record: UserRecord) -> None:
        self.session.add(record)


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def create_user(self, payload: CreateUserRequest) -> UserResponse:
        with self.session.begin():
            if self.users.get_by_email(payload.email) is not None:
                raise DuplicateEmail(payload.email)

            record = UserRecord(email=payload.email, name=payload.name)
            self.users.add(record)

            # Flush obtains generated values while keeping transaction ownership here.
            # flush는 생성된 값을 얻되, transaction 소유권은 service에 남겨둔다.
            self.session.flush()
            return UserResponse.model_validate(record)

    def get_user(self, user_id: int) -> UserResponse | None:
        record = self.users.get(user_id)
        if record is None:
            return None
        return UserResponse.model_validate(record)


engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionFactory = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)
Base.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()


def get_user_service(
    session: Annotated[Session, Depends(get_session)],
) -> UserService:
    return UserService(session)


router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    try:
        return service.create_user(payload)
    except DuplicateEmail as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"duplicate email: {exc.email}",
        ) from exc


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    user = service.get_user(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user not found",
        )
    return user


app = FastAPI(title="FastAPI Service Template Example")
app.include_router(router)


def main() -> None:
    with TestClient(app) as client:
        created = client.post(
            "/users",
            json={"email": "neo@example.com", "name": "Neo"},
        )
        duplicate = client.post(
            "/users",
            json={"email": "neo@example.com", "name": "Neo Again"},
        )
        fetched = client.get("/users/1")

    print("create:", created.status_code, created.json())
    print("duplicate:", duplicate.status_code, duplicate.json())
    print("get:", fetched.status_code, fetched.json())


if __name__ == "__main__":
    main()
