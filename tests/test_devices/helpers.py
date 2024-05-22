def get_unwrapped(func):
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__
    return func
