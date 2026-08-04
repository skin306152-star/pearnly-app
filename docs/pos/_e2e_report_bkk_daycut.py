# -*- coding: utf-8 -*-
"""销售报表曼谷日切真库 E2E(POS 项目 · 2026-08-05 日切口径从 UTC 改曼谷)。

mock 单测测不到 AT TIME ZONE 的真实语义,此脚本在真 Postgres 上验窗口边界与按天分组:
插 4 笔固定 UTC 时刻的单(禁 now() · CI 在 UTC 17:00–24:00 有日期翻车史),断言曼谷
2026-08-05 单日窗口 [08-04T17:00Z, 08-05T17:00Z) 恰好含曼谷 05 日的两笔、排前后两笔,
且 by_day 把每笔归进它的曼谷日而非 UTC 日;交易明细(sales_log·CSV 同源)同窗口同轴。

一事务跑 + 结尾 ROLLBACK(零残留);租户用随机 uuid,不碰任何真数据。
本地运行:docker start pearnly-db →
  DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
  PYTHONIOENCODING=utf-8 python docs/pos/_e2e_report_bkk_daycut.py
prod 运行:ssh pearnly → cd /opt/mrpilot → set -a;. ./.env;set +a →
  PYTHONIOENCODING=utf-8 PYTHONPATH=/opt/mrpilot venv/bin/python docs/pos/_e2e_report_bkk_daycut.py
"""

import os
import sys
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.pos import report as report_svc  # noqa: E402
from services.pos import sales_log as sales_log_svc  # noqa: E402

results = []

# (备注, UTC 时刻, 金额, 所属曼谷日) —— 曼谷 = UTC+7,05 日窗口 = [04T17:00Z, 05T17:00Z)
_FIXTURE = [
    (
        "曼谷05日 01:30(凌晨单·UTC 还是 04 号)",
        datetime(2026, 8, 4, 18, 30, tzinfo=timezone.utc),
        "100",
        "2026-08-05",
    ),
    (
        "曼谷04日 23:59(差 1 分钟进 05)",
        datetime(2026, 8, 4, 16, 59, tzinfo=timezone.utc),
        "7",
        "2026-08-04",
    ),
    (
        "曼谷05日 23:59:59(收尾一秒)",
        datetime(2026, 8, 5, 16, 59, 59, tzinfo=timezone.utc),
        "30",
        "2026-08-05",
    ),
    (
        "曼谷06日 00:00(半开上界·恰好出窗)",
        datetime(2026, 8, 5, 17, 0, tzinfo=timezone.utc),
        "9",
        "2026-08-06",
    ),
]


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("OK  " if ok else "FAIL") + f" {name}" + (f" · {detail}" if detail else ""))


def main() -> int:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("DATABASE_URL 未设置", file=sys.stderr)
        return 2
    conn = psycopg2.connect(url)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SET LOCAL app.bypass_rls = 'on'")
        tid, ws = str(uuid.uuid4()), 999999901
        for _, sold_at, amount, _ in _FIXTURE:
            cur.execute(
                "INSERT INTO pos_sales (tenant_id, workspace_client_id, sale_type, status, "
                "grand_total, sold_at) VALUES (%s,%s,'sale','completed',%s,%s)",
                (tid, ws, Decimal(amount), sold_at),
            )

        day = report_svc.sales_report(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            date_from=date(2026, 8, 5),
            date_to=date(2026, 8, 5),
        )
        record(
            "曼谷05日窗口 KPI:含凌晨单+收尾秒单=130/2 单(排 04日23:59 与 06日00:00)",
            day["kpi"]["gross"] == "130.00" and day["kpi"]["sales_count"] == 2,
            f"gross={day['kpi']['gross']} count={day['kpi']['sales_count']}",
        )
        record(
            "单日 by_day 只有 2026-08-05 一桶",
            [r["date"] for r in day["by_day"]] == ["2026-08-05"],
            str([r["date"] for r in day["by_day"]]),
        )

        span = report_svc.sales_report(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            date_from=date(2026, 8, 4),
            date_to=date(2026, 8, 6),
        )
        got = {r["date"]: (r["gross"], r["sales_count"]) for r in span["by_day"]}
        want = {"2026-08-04": ("7.00", 1), "2026-08-05": ("130.00", 2), "2026-08-06": ("9.00", 1)}
        record("三日窗口 by_day 每笔归它的曼谷日(凌晨单不落 UTC 日)", got == want, str(got))
        record(
            "窗口总额 = 分日之和(窗口与分组同轴不漏单)",
            span["kpi"]["gross"] == "146.00" and span["kpi"]["sales_count"] == 4,
            f"gross={span['kpi']['gross']} count={span['kpi']['sales_count']}",
        )

        # 交易明细页 + CSV 同源(sales_log 与 report 同口径):窗口捞同样 2 笔,
        # 且行上时刻按曼谷输出(CSV 直接切串,UTC 串会把凌晨单写成前一天)。
        log = sales_log_svc.list_sales(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            date_from=date(2026, 8, 5),
            date_to=date(2026, 8, 5),
        )
        log_days = sorted(r["sold_at"][:10] for r in log["items"])
        record(
            "sales_log 曼谷05日窗口 = 同样 2 笔,行上日期列都是 05 日(+07:00)",
            log["total"] == 2
            and log_days == ["2026-08-05", "2026-08-05"]
            and all(r["sold_at"].endswith("+07:00") for r in log["items"]),
            f"total={log['total']} days={log_days}",
        )

        conn.rollback()
    except Exception as e:
        conn.rollback()
        import traceback

        traceback.print_exc()
        print(f"E2E 异常: {e}", file=sys.stderr)
        return 2
    finally:
        cur.close()
        conn.close()

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{'=' * 50}\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
