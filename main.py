import dis

import monkeypatch
import import_helper

import parsed_checked as pc
import parsed as p

def main():
    print("patching")
    monkeypatch.patch_func(p.f)
    print("second patch")
    monkeypatch.patch_func(p.f)
    print("patching f2")
    monkeypatch.patch_func(p.f2)
    #print("output")
    #dis.dis(p.f)
    #dis.show_code(p.f)

    p.f("4")


if __name__ == '__main__':
    main()
