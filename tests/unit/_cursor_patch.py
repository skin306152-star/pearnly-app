# -*- coding: utf-8 -*-
"""RLS 迁移期测试共用 · 同时 patch get_cursor + get_cursor_rls 到同一 fake。

B8 RLS 把各 store 的 DAL 从裸 get_cursor 迁到 get_cursor_rls,但同一模块常混着已迁/未迁函数。
测试只要两路同挂同一 fake,就不必管被测函数走哪路。需断言 commit kwarg 的测试用 yield 出的
CursorPatchProxy(暴露实际被调那一路的 call_args/called/call_count)。

target 默认 "core.db" —— 各 store 的 `store.db` 即 core.db 模块对象,patch "core.db.X" 等同。
"""

from contextlib import contextmanager
from unittest import mock


class CursorPatchProxy:
    """暴露实际被调用那一路(get_cursor 或 get_cursor_rls)的 call_args/called/call_count。"""

    def __init__(self, m1, m2):
        self._m1, self._m2 = m1, m2

    def _active(self):
        return self._m2 if self._m2.called else self._m1

    @property
    def called(self):
        return self._m1.called or self._m2.called

    @property
    def call_args(self):
        return self._active().call_args

    @property
    def call_count(self):
        return self._m1.call_count + self._m2.call_count


@contextmanager
def patch_both(*, factory=None, value=None, target="core.db"):
    """patch `{target}.get_cursor` + `.get_cursor_rls` · yield CursorPatchProxy。

    factory: 每次调用产出新游标上下文(side_effect)· 用于按调用收集 kwargs / 返回新 FakeCM。
    value:   两路都返回同一对象(return_value)· 用于一函数内多次开同一 fake 累计。
    二选一。
    """
    if (factory is None) == (value is None):
        raise ValueError("patch_both: 恰好传 factory 或 value 之一")
    if factory is not None:
        m1, m2 = mock.MagicMock(side_effect=factory), mock.MagicMock(side_effect=factory)
        with mock.patch(f"{target}.get_cursor", m1), mock.patch(f"{target}.get_cursor_rls", m2):
            yield CursorPatchProxy(m1, m2)
    else:
        with (
            mock.patch(f"{target}.get_cursor", return_value=value) as m1,
            mock.patch(f"{target}.get_cursor_rls", return_value=value) as m2,
        ):
            yield CursorPatchProxy(m1, m2)
