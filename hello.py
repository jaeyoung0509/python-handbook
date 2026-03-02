import asyncio
from typing import Type

async def fetchz_data(id:int)   -> str:
    if id ==2:
        raise ValueError("Data 2 불량")

    if id==3:
        raise TypeError("asdasd")
    return f"data{id}"
                        

def raise_group():

    errors = [
        ValueError("invalid value"),
        TypeError("wrong type"),
        KeyError("missing key")
    ]
    raise ExceptionGroup("multiple errors", errors)

async def main():
    try:
        async with asyncio.TaskGroup() as tg:
            task1 = tg.create_task(fetchz_data(1))
            taks2= tg.create_task(fetchz_data(2))
            taks3 = tg.create_task(fetchz_data(3))
    
    except *ValueError as e:
        print(f"ValueError 발생: {e.exceptions}")

    except *TypeError as e:
        print(f"TypeError 발생: {e.exceptions}")

    try:
         raise_group():
    except ExceptionGroup as eg:
        print(eg.exceptions)



asyncio.run(main())


def get_firt[T](items: list[T]) -> T:
    return items[0]

type Vector[T] = list[tuple[T,T ]]