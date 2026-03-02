import asyncio


async def fail(name: str, error_type: type[Exception]) -> None:
    await asyncio.sleep(0)
    raise error_type(f"{name} failed")


async def main() -> None:
    try:
        async with asyncio.TaskGroup() as task_group:
            task_group.create_task(fail("load-user", ValueError))
            task_group.create_task(fail("load-orders", TypeError))
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
