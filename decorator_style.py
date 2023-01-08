def typechecked_decorator(func):
    annotations = inspect.get_annotations(func)

    @functools.wraps(func)
    def inner(*args, **kwargs):
        sig = inspect.signature(func)
        arglist = [*args]
        for arg_idx, p in enumerate(sig.parameters):
            if p == "self":
                continue
            if arg_idx >= len(arglist):
                break

            vartype = annotations[p]
            assert isinstance(arglist[arg_idx], vartype), f"{func.__name__}: argument {p} should be a {annotations[p]} but got a {type(arglist[arg_idx])}"

        data = {**kwargs}
        for arg, value in data.items():
            assert isinstance(value, annotations[arg]), f"{func.__name__}: argument {arg} should be a {annotations[arg]} but got a {type(value)}"
        retr = func(*args, **kwargs)
        assert isinstance(retr, annotations["return"]), f"{func.__name__}: should return a {annotations['return']} but returned a {type(retr)}"
        return retr
    return inner

class TypeChecked(type):
    def __init__(cls, name, bases, attrs):
        funcs = [m for m in inspect.getmembers(cls) if not m[0].startswith("__") and not m[0].endswith("__")]
        for name, method in funcs:
            setattr(cls, name, typechecked_decorator(method))
        return

class Thingy(metaclass=TypeChecked):
    def dothing(self, val : int) -> int:
        return str(val + 15)
