# -*- coding: utf-8 -*-
"""钱箱盈亏台账读模型(PC-3 · 老板端交接班 · 防内盗信任基石)。

老板端「交接班」台账的数据源:按 (tenant,ws) 倒序列历史班次(连号 / 收银员 / 开关班时刻 /
应有·实点·长短款 / 状态)。对标 Loyverse/Square 的 Shifts 报表。跟 audit_report.py(异常按人
汇总)是同一防内盗页的两个视角,不重复。

缺号检测(tamper-evidence):没有物理删班的路径,连号本应连续。取回窗口内相邻两个在场连号之间
若有空缺,即列为 missing_seqs(某张班被绕库删掉的信号)。仅在返回窗口内判断——窗口最低号之下
的缺口无法从截断结果推断,不误报。SQL 每句 WHERE tenant_id + workspace_client_id 全参数化,钱
Decimal → 2 位小数字符串,时间 isoformat(UTC)。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

_DEFAULT_LIMIT = 200


def _money(v) -> Optional[str]:
    return None if v is None else f"{Decimal(str(v)):.2f}"


def _iso(v) -> Optional[str]:
    return v.isoformat() if v else None


def _missing_seqs(seqs: list) -> list:
    """返回窗口内相邻在场连号之间的空缺号(升序)。收银员删掉某张班 → 序号断裂即现于此。"""
    present = sorted(s for s in seqs if s is not None)
    gaps: list = []
    for prev, cur in zip(present, present[1:]):
        if cur > prev + 1:
            gaps.extend(range(prev + 1, cur))
    return gaps


def list_shifts(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    limit: int = _DEFAULT_LIMIT,
) -> dict:
    """本账套历史班次(按连号倒序)+ 缺号警示。四态由前端据 shifts/missing_seqs 渲染。"""
    lim = max(1, min(500, int(limit)))
    cur.execute(
        "SELECT sh.id, sh.shift_seq, sh.cashier_id, c.display_name AS cashier_name, "
        "sh.opened_at, sh.closed_at, sh.opening_float, sh.expected_cash, "
        "sh.counted_cash, sh.cash_diff, sh.status "
        "FROM pos_shifts sh LEFT JOIN pos_cashiers c ON c.id = sh.cashier_id "
        "WHERE sh.tenant_id = %s AND sh.workspace_client_id = %s "
        "ORDER BY sh.shift_seq DESC NULLS LAST LIMIT %s",
        (tenant_id, workspace_client_id, lim),
    )
    rows = cur.fetchall()
    shifts = [
        {
            "id": str(r["id"]),
            "shift_seq": r["shift_seq"],
            "cashier_id": str(r["cashier_id"]) if r["cashier_id"] else None,
            "cashier_name": r["cashier_name"],
            "opened_at": _iso(r["opened_at"]),
            "closed_at": _iso(r["closed_at"]),
            "opening_float": _money(r["opening_float"]),
            "expected_cash": _money(r["expected_cash"]),
            "counted_cash": _money(r["counted_cash"]),
            "cash_diff": _money(r["cash_diff"]),
            "status": r["status"],
        }
        for r in rows
    ]
    return {"shifts": shifts, "missing_seqs": _missing_seqs([r["shift_seq"] for r in rows])}
