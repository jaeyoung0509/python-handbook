from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from types import TracebackType
from typing import Self

import pytest


@dataclass(frozen=True, slots=True)
class UserRecord:
    email: str
    name: str


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    email: str
    name: str


@dataclass(frozen=True, slots=True)
class UserRead:
    email: str
    name: str


class DuplicateEmail(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(email)


class AbstractUserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> UserRecord | None:
        raise NotImplementedError

    @abstractmethod
    def add(self, user: UserRecord) -> None:
        raise NotImplementedError


class AbstractUnitOfWork(ABC):
    @property
    @abstractmethod
    def users(self) -> AbstractUserRepository:
        raise NotImplementedError

    @abstractmethod
    def __enter__(self) -> Self:
        raise NotImplementedError

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError


class AbstractWelcomeNotifier(ABC):
    @abstractmethod
    def send(self, email: str, name: str) -> None:
        raise NotImplementedError


class FakeUserRepository(AbstractUserRepository):
    def __init__(self) -> None:
        self._items: dict[str, UserRecord] = {}

    def get_by_email(self, email: str) -> UserRecord | None:
        return self._items.get(email)

    def add(self, user: UserRecord) -> None:
        self._items[user.email] = user


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self) -> None:
        self._users = FakeUserRepository()
        self.committed = False
        self.rolled_back = False

    @property
    def users(self) -> FakeUserRepository:
        return self._users

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc is not None:
            self.rollback()

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class RecordingNotifier(AbstractWelcomeNotifier):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def send(self, email: str, name: str) -> None:
        self.calls.append((email, name))


class RegisterUserUseCase:
    def __init__(
        self,
        uow_factory: Callable[[], AbstractUnitOfWork],
        notifier: AbstractWelcomeNotifier,
    ) -> None:
        self.uow_factory = uow_factory
        self.notifier = notifier

    def execute(self, command: RegisterUserCommand) -> UserRead:
        with self.uow_factory() as uow:
            if uow.users.get_by_email(command.email) is not None:
                raise DuplicateEmail(command.email)

            record = UserRecord(email=command.email, name=command.name)
            uow.users.add(record)
            result = UserRead(email=record.email, name=record.name)
            uow.commit()

        self.notifier.send(result.email, result.name)
        return result


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def notifier() -> RecordingNotifier:
    return RecordingNotifier()


@pytest.fixture
def use_case(
    uow: FakeUnitOfWork,
    notifier: RecordingNotifier,
) -> RegisterUserUseCase:
    return RegisterUserUseCase(
        uow_factory=lambda: uow,
        notifier=notifier,
    )


def test_register_user_commits_and_notifies(
    use_case: RegisterUserUseCase,
    uow: FakeUnitOfWork,
    notifier: RecordingNotifier,
) -> None:
    result = use_case.execute(RegisterUserCommand(email="neo@example.com", name="Neo"))

    assert result == UserRead(email="neo@example.com", name="Neo")
    assert uow.committed is True
    assert uow.rolled_back is False
    assert notifier.calls == [("neo@example.com", "Neo")]


def test_duplicate_email_rolls_back_and_skips_notification(
    use_case: RegisterUserUseCase,
    uow: FakeUnitOfWork,
    notifier: RecordingNotifier,
) -> None:
    uow.users.add(UserRecord(email="neo@example.com", name="Neo"))

    with pytest.raises(DuplicateEmail):
        use_case.execute(RegisterUserCommand(email="neo@example.com", name="Neo"))

    assert uow.committed is False
    assert uow.rolled_back is True
    assert notifier.calls == []
