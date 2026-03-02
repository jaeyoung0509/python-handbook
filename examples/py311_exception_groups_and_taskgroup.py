# Added in Python 3.11: ExceptionGroup, except*, and asyncio.TaskGroup.
# Python 3.11에서 추가: ExceptionGroup, except*, asyncio.TaskGroup.
# Why: concurrent work can fail in multiple places at once, and old except lost that structure.
# 왜: 동시 작업은 여러 곳에서 동시에 실패할 수 있는데, 예전 except 모델은 그 구조를 잘 보존하지 못했다.
# Use when: running fan-out async jobs where failures should stay grouped and visible.
# 언제 쓰나: fan-out async 작업에서 실패를 그룹 단위로 유지하고 싶을 때 좋다.

import asyncio


async def fail(name: str, error_type: type[Exception]) -> None:
    await asyncio.sleep(0)
    raise error_type(f"{name} failed")


async def main() -> None:
    try:
        # TaskGroup gives structured concurrency: child tasks live and fail as one unit.
        # TaskGroup은 구조적 동시성을 제공해서 자식 task를 하나의 생명주기로 묶는다.
        async with asyncio.TaskGroup() as task_group:
            task_group.create_task(fail("load-user", ValueError))
            task_group.create_task(fail("load-orders", TypeError))
    # except* peels matching errors out of the group instead of flattening everything to one error.
    # except*는 그룹 전체를 평평하게 만들지 않고, 해당 타입 예외만 부분적으로 꺼내 처리한다.
    except* ValueError as group:
        print("ValueError group:")
        for error in group.exceptions:
            print(" ", repr(error))
    except* TypeError as group:
        print("TypeError group:")
        for error in group.exceptions:
            print(" ", repr(error))


if __name__ == "__main__":
    asyncio.run(main())
