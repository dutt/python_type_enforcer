import dis

import monkeypatch
import import_helper

import parsed_checked as pc
import parsed as p

def main():
    monkeypatch.patch_func(p.f)
    dis.dis(p.f)
    dis.show_code(p.f)

    p.f("4")


if __name__ == '__main__':
    main()
