try:
    raise ExceptionGroup("big trouble", [
        ValueError("error1"),
        TypeError("error2"),
        ValueError("error3"),
        KeyError("error4"),
    ])
except* ValueError as ve:
    print("ValueErrors:", ve.exceptions)
except* TypeError as te:
    print("TypeErrors:", te.exceptions)
except* KeyError as ke:
    print("KeyErrors:", ke.exceptions)