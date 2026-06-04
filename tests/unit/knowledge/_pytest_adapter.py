"""Expose pytest-style module test functions to unittest discover.

These knowledge tests were migrated verbatim from the pearnly-knowledge sandbox,
where they ran under pytest as top-level ``test_*`` functions. The main project's
CI runs ``unittest discover``, which only collects ``TestCase`` subclasses.
``build_case`` wraps a module's top-level test functions as methods on a
generated ``TestCase`` so they run unchanged here — keeping the migrated tests
verbatim rather than hand-rewriting 47 functions into a different style.
"""

import unittest


def build_case(module_globals: dict, name: str) -> type:
    methods = {
        fn_name: (lambda self, _fn=fn: _fn())
        for fn_name, fn in module_globals.items()
        if fn_name.startswith("test_") and callable(fn)
    }
    return type(name, (unittest.TestCase,), methods)
