import ast
import importlib
from pathlib import Path

import storage

currdir = Path(__file__).resolve().parent
rootdir=str(currdir)
ignore_dirs=[str(currdir / "venv")]

def import_helper(name, globals=None, locals=None, fromlist=(), level=0):
    def should_parse(path):
        if rootdir not in path:
            return False
        for d in ignore_dirs:
            if d in path:
                return False
        return True
    def get_ast(path):
        with open(path, mode='r', encoding="utf-8") as reader:
            text = reader.read()
        tree = ast.parse(text)
        return tree
    def store_types(path, tree):
        if path not in storage.STORAGE:
            storage.STORAGE[path] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            print(f"{path}:{node.lineno} - func {node.name}")
            print(f"  return type {node.returns.id}")
            funcdata = {
                "name" : node.name,
                "return_type" : node.returns.id,
                "path" : path,
                "lineno" : node.lineno,
                "args" : []
            }
            for n in ast.walk(node):
                if not isinstance(n, ast.arg):
                    continue
                print(f"  arg {n.arg} has type {n.annotation.id}")
                funcdata["args"].append({
                    "name" : n.arg,
                    "type" : n.annotation.id
                })
            storage.STORAGE[path].append(funcdata)

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

__builtins__["__import__"] = import_helper
