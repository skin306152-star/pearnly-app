# -*- coding: utf-8 -*-
"""销项单据连号分配(PO-4 · docs/sales-module/docs/13)。

泰国税票连号不跳:正式开出时在事务内 FOR UPDATE 锁号计数器,取号 +1。草稿不占号、
作废不回收号。重置策略可配——默认每年(yearly),底层同样支持按月(monthly)/永不
(never),切换只改 reset,不返工。号码格式 前缀+期间+流水(如 INV2026-00001)。

allocate 必须在已开启事务的 cursor 上调用(db.get_cursor_rls(commit=True)),否则
FOR UPDATE 不构成并发互斥。
"""

from __future__ import annotations

from datetime import date

RESET_YEARLY = "yearly"
RESET_MONTHLY = "monthly"
RESET_NEVER = "never"


def period_key(reset: str, on: date) -> str:
    """号码桶键(进 document_number_sequences 主键 · 决定何时重置归 1)。"""
    if reset == RESET_MONTHLY:
        return on.strftime("%Y-%m")
    if reset == RESET_NEVER:
        return "ALL"
    return on.strftime("%Y")


def format_number(prefix: str, reset: str, on: date, n: int, width: int = 5) -> str:
    seq = f"{n:0{width}d}"
    if reset == RESET_MONTHLY:
        return f"{prefix}{on.strftime('%Y%m')}-{seq}"
    if reset == RESET_NEVER:
        return f"{prefix}-{seq}"
    return f"{prefix}{on.strftime('%Y')}-{seq}"


def allocate(
    cur, *, tenant_id: str, doc_type: str, prefix: str, reset: str, on: date, start: int = 1
) -> tuple[str, int]:
    """事务内取下一个连号 → (展示号, 流水号)。调用方负责开事务并提交。

    start = 新序列(该 period 首次出号)的起始流水号(接旧账本设 = 旧末号+1);序列已存在则
    忽略 start(不回拨已发出的号)。
    """
    period = period_key(reset, on)
    cur.execute(
        "INSERT INTO document_number_sequences (tenant_id, doc_type, prefix, period, next_number) "
        "VALUES (%s, %s, %s, %s, %s) "
        "ON CONFLICT (tenant_id, doc_type, prefix, period) DO NOTHING",
        (tenant_id, doc_type, prefix, period, max(int(start), 1)),
    )
    cur.execute(
        "SELECT next_number FROM document_number_sequences "
        "WHERE tenant_id=%s AND doc_type=%s AND prefix=%s AND period=%s FOR UPDATE",
        (tenant_id, doc_type, prefix, period),
    )
    n = cur.fetchone()["next_number"]
    cur.execute(
        "UPDATE document_number_sequences SET next_number = next_number + 1 "
        "WHERE tenant_id=%s AND doc_type=%s AND prefix=%s AND period=%s",
        (tenant_id, doc_type, prefix, period),
    )
    return format_number(prefix, reset, on, n), n
