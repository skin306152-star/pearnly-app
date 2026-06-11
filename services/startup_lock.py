# -*- coding: utf-8 -*-
"""跨 worker 启动 DDL 串行锁。

uvicorn --workers N 时每个 worker 都跑 run_startup() 的 ensure_* 建表,并发 DDL 在
Postgres 里互相死锁(2026-06-11 实测:4-worker 撞 ensure_erp_oauth_tables · cef351bf 回退)。
worker 全在同一台机器,文件锁串行最稳:不依赖 DB 会话——Supabase 事务池下
pg_advisory_lock 的会话语义不可靠,排除该方案。
"""

import os
import tempfile
import threading
from contextlib import contextmanager

try:
    import fcntl
except ImportError:  # Windows 开发机单 worker:进程内锁兜底
    fcntl = None

_LOCK_PATH = os.path.join(tempfile.gettempdir(), "pearnly_startup_ddl.lock")
_fallback_lock = threading.Lock()


@contextmanager
def startup_ddl_lock():
    """同机多 worker 的启动期 DDL 一个一个跑(幂等 ensure 重复执行无害,只消串行)。"""
    if fcntl is None:
        with _fallback_lock:
            yield
        return
    with open(_LOCK_PATH, "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
