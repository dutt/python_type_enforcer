from types import CodeType

import bytecode
from bytecode import Bytecode, Instr, Label, ConcreteBytecode

import storage

def get_print_block(text):
    return [
        Instr("LOAD_GLOBAL", "print"),
        Instr("LOAD_CONST", text),
        Instr("CALL_FUNCTION", 1),
        Instr("POP_TOP"),
    ]

def get_verify_block(varidx, varname, vartype, block_type):
    label_builtins = Label()
    label_isinstance = Label()
    label_end = Label()
    tmpvarname = f"{block_type}{varname}{varidx}"
    print(f"generating {block_type} block for {varidx=} {varname=} {vartype=} {tmpvarname=}")
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

            #*get_print_block(f"{varidx=} {varname=} {vartype=} {tmpvarname=} in globals"),

            Instr("JUMP_FORWARD", label_isinstance),

            label_builtins,

            Instr("LOAD_GLOBAL", "__builtins__"),
            Instr("LOAD_CONST", vartype),
            Instr("BINARY_SUBSCR"),
            Instr("STORE_FAST", tmpvarname),

            #*get_print_block(f"{varidx=} {varname=} {vartype=} {tmpvarname=} in builtins"),

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

def get_start_tmp_var_block(varname):
    print(f"start tmp_var_block {varname=}")
    return [
        Instr("STORE_FAST", varname),
    ]

def get_end_tmp_var_block(varname):
    print(f"end tmp_var_block {varname=}")
    return [
        Instr("LOAD_FAST", varname)
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
    # TODO check if already patched

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

    newlocals = len(argblocks)

    old_code_with_return_asserts = []
    returns = 0
    for idx, instr in enumerate(old_code):
        if isinstance(instr, Label):
            continue
        if instr.name == "RETURN_VALUE":
            vartype = funcdata["return_type"]

            # if it's already a variable just assert type
            #varname = old_code[idx-1].arg
            #print(f"got return at {idx}, {varname=}, {return_size=}")
            #verify_block = get_verify_block(returns, varname, vartype, block_type="return")

            # otherwise, make a temp variable
            newlocals += 1
            #return_size = 1
            #while (isinstance(old_code[idx-return_size], Label) or
            #       old_code[idx-return_size].lineno == instr.lineno) and return_size <= idx:
            #    return_size += 1
            varname = f"retr_{idx}_{current.co_name}"
            #print(f"got return at {idx}, {varname=}, {return_size=}")
            print(f"got return at {idx}, {varname=}")
            start_tmp_var_block = get_start_tmp_var_block(varname)
            old_code_with_return_asserts.extend(start_tmp_var_block)
            verify_block = get_verify_block(returns, varname, vartype, block_type="return")
            old_code_with_return_asserts.extend(verify_block)
            end_tmp_var_block = get_end_tmp_var_block(varname)
            old_code_with_return_asserts.extend(end_tmp_var_block)

            returns += 1
        old_code_with_return_asserts.append(instr)

    blocks = [*argblocks, *old_code_with_return_asserts]
    #print("\n".join([str(b) for b in blocks]))
    check_var_block = Bytecode(blocks)
    check_var_block.legalize()
    check_var_block._copy_attr_from(old_code)
    concrete = check_var_block.to_concrete_bytecode()
    # TODO create code type object according to sys.version_info
    func.__code__ = CodeType(
                             current.co_argcount,
                             current.co_posonlyargcount,
                             current.co_kwonlyargcount,
                             current.co_nlocals + newlocals,
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
