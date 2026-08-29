# -*- coding: utf-8 -*-
"""Import production modules without leaking a psycopg2 fallback across unit modules."""

from __future__ import annotations

import importlib
import sys
import types
from contextlib import contextmanager

_MODULE_NAMES = (
    "psycopg2",
    "psycopg2.errors",
    "psycopg2.extras",
    "psycopg2.pool",
    "psycopg2.sql",
)
_MISSING = object()


class _StubPool:
    def __init__(self, *args, **kwargs):
        pass

    def getconn(self):
        raise RuntimeError("stub")

    def putconn(self, *args, **kwargs):
        pass

    def closeall(self):
        pass


class _UniqueViolation(Exception):
    pass


def _fallback_modules() -> dict[str, types.ModuleType]:
    pg = types.ModuleType("psycopg2")
    errors = types.ModuleType("psycopg2.errors")
    extras = types.ModuleType("psycopg2.extras")
    pool = types.ModuleType("psycopg2.pool")
    sql = types.ModuleType("psycopg2.sql")

    pg.connect = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("stub"))
    pg.Error = Exception
    pg.OperationalError = Exception
    errors.UniqueViolation = _UniqueViolation
    extras.RealDictCursor = object
    extras.DictCursor = object
    extras.execute_values = lambda *args, **kwargs: None
    extras.Json = lambda value: value
    pool.ThreadedConnectionPool = _StubPool
    pool.SimpleConnectionPool = _StubPool
    sql.SQL = lambda value: value
    sql.Identifier = lambda value: value
    pg.errors = errors
    pg.extras = extras
    pg.pool = pool
    pg.sql = sql
    return {
        "psycopg2": pg,
        "psycopg2.errors": errors,
        "psycopg2.extras": extras,
        "psycopg2.pool": pool,
        "psycopg2.sql": sql,
    }


@contextmanager
def psycopg2_import_guard():
    """Prefer the required driver; isolate the fallback to one import window."""
    try:
        importlib.import_module("psycopg2")
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg2":
            raise
    else:
        yield
        return

    previous = {name: sys.modules.get(name, _MISSING) for name in _MODULE_NAMES}
    sys.modules.update(_fallback_modules())
    try:
        yield
    finally:
        for name, module in previous.items():
            if module is _MISSING:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
