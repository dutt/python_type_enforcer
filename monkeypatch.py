from types import CodeType

import bytecode
from bytecode import Bytecode, Instr, Label, ConcreteBytecode

import storage

def get_verify_block(varidx, varname, vartype, block_type):
    print(f"generating block for {varidx=} {varname=} {vartype=}")
    label_builtins = Label()
    label_isinstance = Label()
    label_end = Label()
    tmpvarname = f"{block_type}{varname}{varidx}"
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
            Instr("LOAD_CONST", f"{block_type} '{varname}' is not of type "),
            Instr("LOAD_FAST", tmpvarname),
            Instr("FORMAT_VALUE", 0),
            Instr("BUILD_STRING", 2),

            Instr("CALL_FUNCTION", 1),
            Instr("RAISE_VARARGS", 1),

            label_end,
        ]

def get_stored(current):
    path = current.co_filename
    if path not in storage.STORAGE:
        raise ValueError(f"No storage for {path=}")
    functions = storage.STORAGE[path]
    for f in functions:
        if f["name"] == current.co_name and f["lineno"] == current.co_firstlineno:
            return f

def patch_func(func):
    current = func.__code__
    print(f"Patching {current.co_filename}:{current.co_firstlineno}")
    old_code = Bytecode.from_code(current)
    funcdata = get_stored(current)
    assert funcdata

    argblocks = []
    for idx, arg in enumerate(old_code.argnames):
        vartype = [a for a in funcdata["args"] if a["name"] == arg]
        assert len(vartype) == 1, vartype
        vartype = vartype[0]["type"]
        argblocks.extend(get_verify_block(idx, arg, vartype, block_type="argument"))

    old_code_with_return_asserts = []
    returns = 0
    for idx, instr in enumerate(old_code):
        if instr.name == "RETURN_VALUE":
            # TODO make more flexible, if it's 'return str(retr)'
            varname = old_code[idx-1].arg
            vartype = funcdata["return_type"]
            print(f"got return at {idx}, {varname=}")
            verify_block = get_verify_block(returns, varname, vartype, block_type="return")
            old_code_with_return_asserts.extend(verify_block)
        old_code_with_return_asserts.append(instr)

    check_var_block = Bytecode([*argblocks, *old_code_with_return_asserts])
    check_var_block.legalize()
    check_var_block._copy_attr_from(old_code)
    concrete = check_var_block.to_concrete_bytecode()
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
