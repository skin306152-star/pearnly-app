# -*- coding: utf-8 -*-
"""工单制真表隔离测试的建表助手(建表逻辑归测试自己 · 不进 services)。

生产建表唯一走 alembic/versions/0059_workorder_core.py(铁律 #5)。真表 RLS 集成测试
仍需在临时库里把 4 表拉起来,这里复用 services/workorder/schema.py 冻结的 DDL 常量
(与 0059 的双跑对齐由 tests/unit/test_workorder_schema.py 静态守),把常量灌进游标 +
挂纯 tenant RLS —— 等价于原 ensure_workorder_schema 的运行期行为,但只服务测试。
"""

from core import db
from core.rls import apply_tenant_rls
from services.workorder import schema


def build_workorder_schema() -> None:
    """在当前库建工单制 4 表 + 索引 + RLS(仅测试用 · 幂等)。"""
    with db.get_cursor(commit=True) as cur:
        for ddl in schema._TABLES:
            cur.execute(ddl)
        for idx in schema._INDEXES:
            # 库已过 C-2 hardening 时,旧 (kind) 唯一索引已被版本化索引撤换;对着存量
            # 多版本数据重建它必撞 UniqueViolation。0059 基线索引只在未 hardening 的
            # 新库需要(建完随即被下面 hardening 换掉)。
            if "uq_wo_deliverables_kind " in idx and _deliverables_versioned(cur):
                continue
            cur.execute(idx)
        schema.ensure_runtime_hardening(cur)  # C-1 租约/幂等键/原始文件名列
        apply_tenant_rls(cur, *schema._RLS_TABLES)


def _deliverables_versioned(cur) -> bool:
    cur.execute("SELECT to_regclass('uq_wo_deliverables_kind_version') AS idx")
    return cur.fetchone()["idx"] is not None
