# -*- coding: utf-8 -*-
"""真库冒烟(test_*_pg_smoke.py)共用的连库口。

CI 的 pg-smoke job 按这个文件名 glob 收人(见 .github/workflows/ci.yml),新写一份 smoke
不用登记就自动进闸 —— 正因为进得这么容易,"连哪个库"必须只有一处答案:

  · 只认 PEARNLY_PG_SMOKE_URL,取不到回落 docker-compose.yml 里 pearnly-db 的本地 DSN;
  · **绝不回落 DATABASE_URL** —— 开发机上那个变量指的是生产库,而 smoke 会真建表真删行。

连不上就整类 skip(CI 侧另有「skip 也算红」的判据兜着,本机没起 docker 时才是真 skip)。
建表 / 清表 / 游标替身各家不同(并发用例要每路一条独立连接,别家共用一条),留在各自文件里。
"""

from __future__ import annotations

import os
import unittest

LOCAL_DSN = os.environ.get(
    "PEARNLY_PG_SMOKE_URL", "postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly"
)


def connect():
    # psycopg2 延到调用时才 import:没装驱动的机器上,收集用例这一步不该直接崩。
    import psycopg2

    return psycopg2.connect(LOCAL_DSN, connect_timeout=3)


def connect_or_skip():
    """连得上返回连接;连不上抛 SkipTest(setUpClass 里直接调)。"""
    try:
        return connect()
    except Exception as exc:
        raise unittest.SkipTest(f"本地 pearnly-db 不可达({exc!r})· 起 docker compose 后再跑")
