import a

def f(val: str) -> int:
    if "str" in globals():
        t0 = globals()["str"]
        print("in globals")
    else:
        t0 = __builtins__["str"]
        print("in builtins")
    assert isinstance(val, t0), val
    retr = int(val) + 15
    #if "int" in globals():
    #    rt = globals()["int"]
    #else:
    #    rt = __builtins__["int"]
    #assert isinstance(retr, rt), rt
    return retr
