import dis
import inspect
import functools

import monkeypatch
#import import_helper

from functools import lru_cache

import parsed_checked as pc
import parsed as p

def main():
    t = Thingy()
    assert t.dothing(4) == 19
    return

    print("patching")
    monkeypatch.patch_func(p.f)
    dis.dis(p.f)
    dis.show_code(p.f)

    assert p.f(val="4") == 22


if __name__ == '__main__':
    main()
