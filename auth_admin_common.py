"""超管路由 · 共享 helper(lazy 委托 auth_signup 破循环 import)。"""

from fastapi import Request


def _require_super_admin(request: Request):
    """lazy 委托 auth_signup._require_super_admin(破循环 import)。"""
    from auth_signup import _require_super_admin as _f

    return _f(request)


def _row_count(row, default=0):
    """lazy 委托 auth_signup._row_count(破循环 import)。"""
    from auth_signup import _row_count as _f

    return _f(row, default)
