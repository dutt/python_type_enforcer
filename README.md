# python_type_enforcer
A type enforcer for python. Beware, here there be dragons.

## Okay, so what's this?

A thingy to add runtime verification of types to python.

It's one part import hook that looks for type hints and stores these per file/function/argument/...

Then another part monkey-patcher that modifies a functions bytecode to insert runtime verification of these stored typehints.

For a visual explanation it transforms the file `parsed.py` into the file `parsed_checked.py`, without you having to rewrite the code yourself.

## Oh dear gods below why?

I've had this idea bouncing around for a year and finally got fed up with it. It was easier than expected :)

Possibly some value in a CI pipeline.

## What's left

- Rework the return opcodes. Create a new variable with what's returned, then typecheck that. Otherwise I'm not sure how to typecheck `return foo("blah")`.
- Python version checking. I've tried this on python 3.10.6 on ubuntu 22.04. At least add version verification.
- Recurse, add monkeypatch call on each function call not already wrapped
- Cleaner configuration for import_helper paths
