import ast
import dis
import importlib
from pathlib import Path

rootdir="/home/mikael/workspace/python_typecheck"
ignore_dirs=["/home/mikael/workspace/python_typecheck/venv"]

import storage

def helper_import(name, globals=None, locals=None, fromlist=(), level=0):
    def should_parse(path):
        if rootdir not in path:
            return False
        for d in ignore_dirs:
            if d in path:
                return False
        return True
    def get_ast(path):
        path = Path(path)
        with path.open(mode='r', encoding="utf-8") as reader:
            text = reader.read()
        tree = ast.parse(text)
        return tree
    def store_types(path, tree):
        if path not in storage.STORAGE:
            storage.STORAGE[path] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                print(f"func {node.name}")
                print(f"  return type {node.returns.id}")
                for n in ast.walk(node):
                    if isinstance(n, ast.arg):
                        print(f"  arg {n.arg} has type {n.annotation.id}")

    #print(f"import <{name=}>")
    mod = importlib.__import__(name, globals, locals, fromlist, level)
    try:
        path = mod.__file__
    except:
        return mod

    #print(f"got path <{path=}>")

    if not should_parse(path):
        return mod

    print(f"parsing path <{path=}>")
    tree = get_ast(path)
    #print(ast.dump(tree, indent=2))
    store_types(path, tree)

    return mod


__builtins__.__dict__["__import__"] = helper_import

import parsed_checked as pc
import parsed as p

def mockstorage(arg):
    if arg == 1:
        return "str"
    if arg == "return":
        return "int"

from types import CodeType
import bytecode
from bytecode import Bytecode, Instr, Label, ConcreteBytecode

def get_verify_block(varidx, varname, vartype):
    print(f"generating block for {varidx=} {varname=} {vartype=}")
    label_builtins = Label()
    label_isinstance = Label()
    label_end = Label()
    tmpvarname = f"t{varidx}"
    return [
            Instr("LOAD_CONST", vartype),
            Instr("LOAD_GLOBAL", "globals"),
            Instr("CALL_FUNCTION", 0),
            Instr("CONTAINS_OP", 0),
            Instr("POP_JUMP_IF_FALSE", label_builtins),

            Instr("LOAD_GLOBAL", "globals"),
            Instr("CALL_FUNCTION", 0),
            Instr("LOAD_CONST", vartype),
            Instr("BINARY_SUBSCR"),
            Instr("STORE_FAST", tmpvarname),

            Instr("LOAD_GLOBAL", "print"),
            Instr("LOAD_CONST", 'in globals'),
            Instr("CALL_FUNCTION", 1),
            Instr("POP_TOP"),

            Instr("JUMP_FORWARD", label_isinstance),

            label_builtins,

            Instr("LOAD_GLOBAL", "__builtins__"),
            Instr("LOAD_CONST", vartype),
            Instr("BINARY_SUBSCR"),
            Instr("STORE_FAST", tmpvarname),

            Instr("LOAD_GLOBAL", "print"),
            Instr("LOAD_CONST", 'in builtins'),
            Instr("CALL_FUNCTION", 1),
            Instr("POP_TOP"),

            label_isinstance,

            Instr("LOAD_GLOBAL", "isinstance"),
            Instr("LOAD_FAST", varname),
            Instr("LOAD_FAST", tmpvarname),
            Instr("CALL_FUNCTION", 2),
            Instr("POP_JUMP_IF_TRUE", label_end),
            Instr("LOAD_ASSERTION_ERROR"),
            Instr("LOAD_CONST", f"argument '{varname}' is not of type "),
            Instr("LOAD_FAST", tmpvarname),
            Instr("FORMAT_VALUE", 0),
            Instr("BUILD_STRING", 2),

            Instr("CALL_FUNCTION", 1),
            Instr("RAISE_VARARGS", 1),

            label_end,
        ]

def patch_func(func, new_body):
    current = func.__code__
    print(current.co_argcount)

    #for attr in dir(func.__code__):
    #     if attr.startswith('co_'):
    #         print("\t%s = %s" % (attr, func.__code__.__getattribute__(attr)))

    extra_num = current.co_argcount + 1
    old_code = Bytecode.from_code(current)
    #old_code.argnames.append("val")

    blocks = []
    for idx, arg in enumerate(old_code.argnames):
        blocks.extend(get_verify_block(idx, arg, "str"))

    check_var_block = Bytecode([*blocks, *old_code])
    #check_var_block.argnames.append("foo")
    check_var_block.legalize()
    check_var_block._copy_attr_from(old_code)
    concrete = check_var_block.to_concrete_bytecode()
    #print(bytecode.dump_bytecode(concrete))
    #new_code = check_var_block.to_code().co_code
    #new_constants = (*current.co_consts, "str", "int")
    #new_names = (*current.co_names, "t", "__builtins__", "globals", "isinstance", )
    #new_varnames = (*current.co_varnames, "t", "t0")
    # TODO create code type object according to sys.version_info
    func.__code__ = CodeType(
                             current.co_argcount,
                             current.co_posonlyargcount,
                             current.co_kwonlyargcount,
                             current.co_nlocals + current.co_argcount,
                             concrete.compute_stacksize(),
                             current.co_flags,
                             concrete.to_code().co_code,
                             tuple(concrete.consts),
                             tuple(concrete.names),
                             tuple(concrete.varnames),
                             current.co_filename,
                             current.co_name,
                             current.co_firstlineno,
                             current.co_lnotab,
                             current.co_freevars,
                             current.co_cellvars,
                             )

def caller():
    p.f("s")

def main():
    #with open("parsed.py") as reader:
    #    text = reader.read()
    #tree = ast.parse(text)
    #print(ast.dump(tree, indent=2))
    #pc.f("f")
    #dis.dis(p.f)
    patch_func(p.f, p.f.__code__.co_code)
    dis.dis(pc.f)
    dis.show_code(pc.f)

    p.f("4", False)


if __name__ == '__main__':
    main()
