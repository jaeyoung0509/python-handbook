from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Engine, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


def get_environment_label() -> str:
    return "prod"


def get_session(request: Request) -> Generator[Session, None, None]:
    session_factory: sessionmaker[Session] = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def create_app(session_factory: sessionmaker[Session]) -> FastAPI:
    app = FastAPI()
    app.state.session_factory = session_factory

    @app.get("/meta")
    def read_meta(
        environment: Annotated[str, Depends(get_environment_label)],
    ) -> dict[str, str]:
        return {"environment": environment}

    @app.get("/users", response_model=list[UserResponse])
    def list_users(
        session: Annotated[Session, Depends(get_session)],
    ) -> list[UserResponse]:
        stmt = select(UserRecord).order_by(UserRecord.id)
        return [UserResponse.model_validate(row) for row in session.scalars(stmt)]

    return app


@pytest.fixture
def engine() -> Generator[Engine, None, None]:
    test_engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    try:
        yield test_engine
    finally:
        Base.metadata.drop_all(test_engine)
        test_engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )


@pytest.fixture
def seed_users(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        session.add_all(
            [
                UserRecord(name="neo"),
                UserRecord(name="trinity"),
            ]
        )
        session.commit()


@pytest.fixture
def app(
    session_factory: sessionmaker[Session],
    seed_users: None,
) -> Generator[FastAPI, None, None]:
    application = create_app(session_factory)

    def get_test_environment_label() -> str:
        return "test"

    application.dependency_overrides[get_environment_label] = get_test_environment_label
    try:
        yield application
    finally:
        application.dependency_overrides.clear()


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def test_seed_fixture_and_client_lifecycle(client: TestClient) -> None:
    response = client.get("/users")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "neo"},
        {"id": 2, "name": "trinity"},
    ]


def test_dependency_override_is_applied(client: TestClient) -> None:
    response = client.get("/meta")

    assert response.status_code == 200
    assert response.json() == {"environment": "test"}
