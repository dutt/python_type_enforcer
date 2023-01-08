import a

def f(val: str) -> int:
    if "str" in globals():
        argumentval0 = globals()["str"]
    else:
        argumentval0 = __builtins__["str"]
    assert isinstance(val, argumentval0), f"argument 'val' is not of type {argumentval0}"
    retr_5_f = int(val) + 15
    if "int" in globals():
        returnretr_5_f0 = globals()["int"]
    else:
        returnretr_5_f0 = __builtins__["int"]
    assert isinstance(retr_5_f, returnretr_5_f0), f"return 'retr_5_f' is not of type {returnretr_5_f0}"
    return retr_5_f
