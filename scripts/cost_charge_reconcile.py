#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""#4b 对账(只读):指定日 ocr_cost_log(识别侧)vs credit_transactions(扣费侧)按租户比对。

两侧理论上该对得上:每次成功识别(ocr_cost_log.status='ok')都该有一条对应扣费流水
(credit_transactions.type='usage')。差异行意味着扣费漏记/多记,或识别记账漏记 ——
两个都是钱路径,值得人眼复核。豁免账号(users.is_billing_exempt)天然只有识别侧没有
扣费侧,输出里单独标注,不算异常。

只读、不接 cron,先手动跑复核。

用法:
    python scripts/cost_charge_reconcile.py                # 默认曼谷时区昨天
    python scripts/cost_charge_reconcile.py --day 2026-07-08

退出码:0 = 两侧完全一致,1 = 存在差异行(含被豁免账号解释的差异——标注仅供人眼参考)。
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_BANGKOK = timezone(timedelta(hours=7))  # 泰国固定 UTC+7、无夏令时(同 services/sales/dates.py)


def fetch_ocr_counts(cur, start: datetime, end: datetime) -> list:
    """识别侧:成功识别次数/成本,按租户分组。"""
    cur.execute(
        """
        SELECT tenant_id, COUNT(*) AS cnt, COALESCE(SUM(cost_thb), 0) AS cost
        FROM ocr_cost_log
        WHERE status = 'ok' AND created_at >= %s AND created_at < %s
        GROUP BY tenant_id
        """,
        (start, end),
    )
    return cur.fetchall()


def fetch_credit_usage_counts(cur, start: datetime, end: datetime) -> list:
    """扣费侧:usage 类型流水行数/金额,按租户分组。"""
    cur.execute(
        """
        SELECT tenant_id, COUNT(*) AS cnt, COALESCE(SUM(amount_thb), 0) AS amt
        FROM credit_transactions
        WHERE type = 'usage' AND created_at >= %s AND created_at < %s
        GROUP BY tenant_id
        """,
        (start, end),
    )
    return cur.fetchall()


def fetch_exempt_tenant_ids(cur) -> set:
    """豁免账号归属的租户(近似:按 users.tenant_id 主归属,不追多公司 user_company_roles ——
    诊断脚本够用,精确多公司豁免面另评估)。"""
    cur.execute(
        "SELECT DISTINCT tenant_id FROM users "
        "WHERE is_billing_exempt = TRUE AND tenant_id IS NOT NULL"
    )
    return {str(r["tenant_id"]) for r in cur.fetchall()}


def build_reconcile_rows(ocr_rows, credit_rows, exempt_tenant_ids: set) -> list:
    """纯函数:三份已取数据 → 按租户对比行。核心比对逻辑,单测直喂参数不摸 DB。"""
    ocr_map = {(str(r["tenant_id"]) if r["tenant_id"] else None): r for r in ocr_rows}
    credit_map = {(str(r["tenant_id"]) if r["tenant_id"] else None): r for r in credit_rows}
    tenant_keys = sorted(set(ocr_map) | set(credit_map), key=lambda k: (k is not None, k or ""))
    rows = []
    for tid in tenant_keys:
        o = ocr_map.get(tid)
        c = credit_map.get(tid)
        ocr_count = int(o["cnt"]) if o else 0
        ocr_cost = float(o["cost"]) if o else 0.0
        credit_count = int(c["cnt"]) if c else 0
        credit_amount = float(c["amt"]) if c else 0.0
        rows.append(
            {
                "tenant_id": tid,
                "ocr_count": ocr_count,
                "ocr_cost_thb": ocr_cost,
                "credit_count": credit_count,
                "credit_amount_thb": credit_amount,
                "diff_count": ocr_count - credit_count,
                "has_exempt_user": tid in exempt_tenant_ids,
            }
        )
    return rows


def print_report(day: date, rows: list) -> bool:
    """打印对账表,返回是否存在差异行(不管是否由豁免账号解释——退出码见 CLI 用法 docstring,
    豁免只是在每行加注释帮人眼快速识别「这行差异是预期的」,不改变有差异即非零退出的信号)。"""
    print(f"=== 成本对账 · {day.isoformat()}(曼谷时区)===")
    print(
        f"{'tenant_id':<38} {'ocr次数':>8} {'ocr成本':>10} {'扣费次数':>8} {'扣费金额':>10} {'差异':>6}"
    )
    has_diff = False
    for r in rows:
        tag = ""
        if r["diff_count"] != 0:
            has_diff = True
            tag = "  (豁免账号,预期不对称)" if r["has_exempt_user"] else "  !! 差异"
        tid = r["tenant_id"] or "(无租户)"
        print(
            f"{tid:<38} {r['ocr_count']:>8} {r['ocr_cost_thb']:>10.4f} "
            f"{r['credit_count']:>8} {r['credit_amount_thb']:>10.2f} {r['diff_count']:>6}{tag}"
        )
    if not rows:
        print("(当天无数据)")
    return has_diff


def main() -> None:
    parser = argparse.ArgumentParser(description="成本对账(识别侧 vs 扣费侧,只读)")
    parser.add_argument("--day", help="曼谷时区日期 YYYY-MM-DD,默认昨天")
    args = parser.parse_args()

    if args.day:
        day = date.fromisoformat(args.day)
    else:
        day = (datetime.now(_BANGKOK) - timedelta(days=1)).date()

    start = datetime.combine(day, datetime.min.time(), tzinfo=_BANGKOK).astimezone(timezone.utc)
    end = start + timedelta(days=1)

    from core import db

    with db.get_cursor() as cur:
        ocr_rows = fetch_ocr_counts(cur, start, end)
        credit_rows = fetch_credit_usage_counts(cur, start, end)
        exempt_tenant_ids = fetch_exempt_tenant_ids(cur)

    rows = build_reconcile_rows(ocr_rows, credit_rows, exempt_tenant_ids)
    has_diff = print_report(day, rows)
    sys.exit(1 if has_diff else 0)


if __name__ == "__main__":
    main()
