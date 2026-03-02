# Modern dataclass patterns: frozen value objects, default_factory, kw_only, and pattern matching.
# 현대 dataclass 패턴: frozen 값 객체, default_factory, kw_only, 패턴 매칭.
# Why: dataclass is one of the cleanest ways to model internal value objects without dragging in a full validation framework.
# 왜: dataclass는 풀 validation 프레임워크 없이 내부 값 객체를 깔끔하게 모델링하는 가장 좋은 도구 중 하나다.
# Use when: modeling settings, commands, value objects, or pattern-matching friendly payloads.
# 언제 쓰나: 설정 객체, command, 값 객체, 패턴 매칭용 payload를 만들 때 좋다.

from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(slots=True, frozen=True, kw_only=True)
class RetryPolicy:
    max_attempts: int
    base_delay_ms: int = 100
    retry_on: tuple[str, ...] = ("timeout", "busy")


@dataclass(slots=True)
class Command:
    kind: str
    payload: str
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.kind = self.kind.strip().lower()
        self.payload = self.payload.strip()


def dispatch(command: Command) -> str:
    match command:
        case Command("email", payload, tags) if "urgent" in tags:
            return f"urgent email -> {payload}"
        case Command("email", payload, _):
            return f"email -> {payload}"
        case Command("sms", payload, _):
            return f"sms -> {payload}"
        case _:
            return "unknown"


def main() -> None:
    policy = RetryPolicy(max_attempts=3)
    stronger_policy = replace(policy, max_attempts=5)
    print("policy:", policy)
    print("updated policy:", stronger_policy)

    command = Command(kind=" EMAIL ", payload=" welcome ", tags=["urgent"])
    print("normalized command:", command)
    print("dispatch:", dispatch(command))


if __name__ == "__main__":
    main()
