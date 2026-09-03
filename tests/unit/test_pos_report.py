# -*- coding: utf-8 -*-
"""POS 销售报表聚合纯逻辑守门测试(POS 项目 · PO-B6)。

不连库:金额/数量字符串化、日期窗口片段(半开区间)、报表装配形状 + 客单价计算。真聚合
SQL(笛卡尔积防护)由 _e2e_po_b6 真库覆盖。"""

import unittest
from datetime import date, datetime, timezone
from decimal import Decimal

from services.pos import report


class _Cur:
    """按 execute 顺序回放预置结果:每次 execute pop 一组 (one, all)。"""

    def __init__(self, scripted):
        self._scripted = list(scripted)
        self._cur = None
        self.queries = []

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        self._cur = self._scripted.pop(0)

    def fetchone(self):
        return self._cur[0]

    def fetchall(self):
        return self._cur[1]


# sales_report 尾部固定跑 heat(1 句)+ live(2 句),与窗口无关;各装配测试统一拼这段回放。
_DASH_TAIL = [
    (None, []),  # heat
    ({"last_sale_at": None}, None),  # live · 最新一单
    (None, None),  # live · 无在班班次
]


class FormatTests(unittest.TestCase):
    def test_money_and_qty(self):
        self.assertEqual(report._money(Decimal("12480")), "12480.00")
        self.assertEqual(report._money(None), "0.00")
        self.assertEqual(report._qty("412"), "412.000")

    def test_range_is_shared_bangkok_window(self):
        """窗口构造收口单一事实源(report_window·三个报表面同轴):此处只守接线,
        形状/参数测试在 test_report_window.py,真库语义在 docs/pos/_e2e_report_bkk_daycut.py。"""
        from services.pos.report_window import bangkok_day_range

        self.assertIs(report._range, bangkok_day_range)

    def test_by_day_groups_on_bangkok_date(self):
        """按天分组必须与窗口同轴(曼谷日),禁回退 UTC 日切——否则跨曼谷 0–7 点的单
        在窗口内却被归进前一天,报表列与 KPI 对不上。"""
        cur = _Cur([(None, []), (None, [])])  # by_day + cost_by_day
        report._by_day(cur, ("t", 9), date(2026, 8, 5), date(2026, 8, 5))
        for sql, _ in cur.queries:
            self.assertIn("AT TIME ZONE 'Asia/Bangkok')::date", sql)
            self.assertNotIn("'UTC'", sql)


class AssemblyTests(unittest.TestCase):
    def test_report_shape_and_avg_ticket(self):
        scripted = [
            ({"gross": Decimal("300"), "sales_count": 2, "refund": Decimal("20")}, None),  # kpi
            ({"cost": Decimal("120"), "complete": True}, None),  # kpi cost_agg
            (None, [{"d": date(2026, 6, 1), "gross": Decimal("300"), "sales_count": 2}]),  # by_day
            (
                None,
                [{"d": date(2026, 6, 1), "cost": Decimal("120"), "complete": True}],
            ),  # by_day cost
            # by_method:两句——方法汇总 tendered + 找零汇总(此桶无找零 chg=0 → 净=200)
            (None, [{"method": "cash", "amount": Decimal("200")}]),  # by_method tendered
            ({"chg": Decimal("0")}, None),  # by_method change
            (
                None,
                [
                    {
                        "product_id": "p1",
                        "name_th": "โค้ก",
                        "name_en": "Coke",
                        "name_zh": "可乐",
                        "qty": Decimal("12"),
                        "gross": Decimal("180"),
                        "cost": Decimal("70"),
                        "complete": True,
                    }
                ],
            ),  # top_products
            (
                None,
                [{"cashier_id": "c1", "name": "Nok", "sales_count": 2, "gross": Decimal("300")}],
            ),
        ] + _DASH_TAIL
        out = report.sales_report(_Cur(scripted), tenant_id="t", workspace_client_id=9)
        self.assertEqual(out["kpi"]["gross"], "300.00")
        self.assertEqual(out["kpi"]["avg_ticket"], "150.00")  # 300/2
        self.assertEqual(out["kpi"]["refund"], "20.00")
        self.assertEqual(out["kpi"]["cost"], "120.00")  # 净 COGS(此桶无退货行 → 与售出成本相等)
        self.assertEqual(out["kpi"]["gross_profit"], "160.00")  # 净口径:300 - 20(退货) - 120
        self.assertTrue(out["kpi"]["cost_complete"])
        self.assertEqual(
            out["by_day"][0],
            {
                "date": "2026-06-01",
                "gross": "300.00",
                "sales_count": 2,
                "cost": "120.00",
                "gross_profit": "180.00",
                "cost_complete": True,
            },
        )
        self.assertEqual(out["by_method"], {"cash": "200.00"})  # 净额口径(此桶无找零)
        self.assertEqual(
            out["top_products"][0]["name"],
            {"th": "โค้ก", "en": "Coke", "zh": "可乐", "display": "โค้ก / Coke / 可乐"},
        )
        self.assertEqual(out["top_products"][0]["qty"], "12.000")
        self.assertEqual(out["top_products"][0]["cost"], "70.00")
        self.assertEqual(out["top_products"][0]["gross_profit"], "110.00")  # 180 - 70
        self.assertEqual(out["by_cashier"][0]["cashier_id"], "c1")

    def test_avg_ticket_zero_when_no_sales(self):
        scripted = [
            ({"gross": Decimal("0"), "sales_count": 0, "refund": Decimal("0")}, None),
            ({"cost": Decimal("0"), "complete": True}, None),
            (None, []),  # by_day
            (None, []),  # by_day cost
            (None, []),  # by_method tendered
            ({"chg": Decimal("0")}, None),  # by_method change
            (None, []),  # top_products
            (None, []),  # by_cashier
        ] + _DASH_TAIL
        out = report.sales_report(_Cur(scripted), tenant_id="t", workspace_client_id=9)
        self.assertEqual(out["kpi"]["avg_ticket"], "0.00")  # 不除零
        self.assertEqual(out["kpi"]["gross_profit"], "0.00")


class CostHonestyTests(unittest.TestCase):
    """成本不完整(有老单据/无成本记录)时毛利必须诚实置空,不许拿部分数据瞎猜。"""

    def test_kpi_gross_profit_null_when_cost_incomplete(self):
        scripted = [
            ({"gross": Decimal("300"), "sales_count": 2, "refund": Decimal("0")}, None),
            ({"cost": Decimal("50"), "complete": False}, None),  # 有行成本未知
            (None, []),  # by_day
            (None, []),  # by_day cost
            (None, []),  # by_method tendered
            ({"chg": Decimal("0")}, None),  # by_method change
            (None, []),  # top_products
            (None, []),  # by_cashier
        ] + _DASH_TAIL
        out = report.sales_report(_Cur(scripted), tenant_id="t", workspace_client_id=9)
        self.assertIsNone(out["kpi"]["gross_profit"])
        self.assertFalse(out["kpi"]["cost_complete"])
        self.assertEqual(out["kpi"]["cost"], "50.00")  # 已知部分仍展示,但不当最终毛利

    def test_by_day_and_top_products_null_when_incomplete(self):
        scripted = [
            ({"gross": Decimal("100"), "sales_count": 1, "refund": Decimal("0")}, None),
            ({"cost": Decimal("0"), "complete": True}, None),
            (None, [{"d": date(2026, 6, 2), "gross": Decimal("100"), "sales_count": 1}]),
            (None, [{"d": date(2026, 6, 2), "cost": Decimal("40"), "complete": False}]),
            (None, []),  # by_method tendered
            ({"chg": Decimal("0")}, None),  # by_method change
            (
                None,
                [
                    {
                        "product_id": "p2",
                        "name_th": "น้ำ",
                        "name_en": "Water",
                        "name_zh": "水",
                        "qty": Decimal("5"),
                        "gross": Decimal("100"),
                        "cost": Decimal("40"),
                        "complete": False,
                    }
                ],
            ),
            (None, []),
        ] + _DASH_TAIL
        out = report.sales_report(_Cur(scripted), tenant_id="t", workspace_client_id=9)
        self.assertIsNone(out["by_day"][0]["gross_profit"])
        self.assertFalse(out["by_day"][0]["cost_complete"])
        self.assertIsNone(out["top_products"][0]["gross_profit"])
        self.assertFalse(out["top_products"][0]["cost_complete"])

    def test_by_day_missing_cost_bucket_treated_as_unknown(self):
        """理论上不该发生(每笔已完成销售必有行),但防御:某天没匹配到 cost 分组 → 置空不猜 0。"""
        scripted = [
            ({"gross": Decimal("50"), "sales_count": 1, "refund": Decimal("0")}, None),
            ({"cost": Decimal("0"), "complete": True}, None),
            (None, [{"d": date(2026, 6, 3), "gross": Decimal("50"), "sales_count": 1}]),
            (None, []),  # cost_by_day 空 · 无该日分组
            (None, []),  # by_method tendered
            ({"chg": Decimal("0")}, None),  # by_method change
            (None, []),  # top_products
            (None, []),  # by_cashier
        ] + _DASH_TAIL
        out = report.sales_report(_Cur(scripted), tenant_id="t", workspace_client_id=9)
        self.assertIsNone(out["by_day"][0]["cost"])
        self.assertIsNone(out["by_day"][0]["gross_profit"])
        self.assertFalse(out["by_day"][0]["cost_complete"])


class RefundNetProfitTests(unittest.TestCase):
    """毛利净口径:退货从毛利底线回冲(营收扣退货、COGS 扣退货回冲成本),不再虚高。

    _cost_agg 已把退货行(负成本)算进净 COGS,故 cost 参数在含退货桶里就是净额。"""

    def _run(self, *, gross, refund, net_cost, complete=True):
        scripted = [
            ({"gross": Decimal(gross), "sales_count": 1, "refund": Decimal(refund)}, None),
            ({"cost": Decimal(net_cost), "complete": complete}, None),
            (None, []),  # by_day
            (None, []),  # by_day cost
            (None, []),  # by_method tendered
            ({"chg": Decimal("0")}, None),  # by_method change
            (None, []),  # top_products
            (None, []),  # by_cashier
        ] + _DASH_TAIL
        return report.sales_report(_Cur(scripted), tenant_id="t", workspace_client_id=9)

    def test_full_refund_zeroes_profit(self):
        """卖฿100(成本60)全退:gross=100/refund=100/净COGS=0 → 毛利=0(非虚高的 40)。"""
        out = self._run(gross="100", refund="100", net_cost="0")["kpi"]
        self.assertEqual(out["gross"], "100.00")  # gross 口径不变(仍是 sale 营收)
        self.assertEqual(out["refund"], "100.00")
        self.assertEqual(out["cost"], "0.00")  # 净 COGS = 60 售出 − 60 退货回冲
        self.assertEqual(out["gross_profit"], "0.00")  # 100 - 100 - 0

    def test_partial_refund_net_profit(self):
        """半退:营收净 50、净 COGS 30 → 毛利 20。"""
        out = self._run(gross="100", refund="50", net_cost="30")["kpi"]
        self.assertEqual(out["gross_profit"], "20.00")  # 100 - 50 - 30

    def test_incomplete_cost_null_even_with_refund(self):
        """退货行/售出行有 None 成本 → 净 COGS 不齐 → 毛利诚实置空(不拿假 0 冲)。"""
        out = self._run(gross="100", refund="100", net_cost="0", complete=False)["kpi"]
        self.assertIsNone(out["gross_profit"])
        self.assertFalse(out["cost_complete"])


class ByMethodChangeNettingTests(unittest.TestCase):
    """现金桶取净收入:tendered − change(Bug#4)。

    pos_payments.amount 存顾客给的钱(tendered),找零单独存在 pos_sales.change_amount。旧
    _by_method 直接 SUM(amount) 把找零当现金收入虚增。修法:两句 SQL——按方式汇总 tendered +
    从 pos_sales 单独汇总 change(每单一行·天然只算一次·避开 min(uuid) 聚合不存在),Python 侧
    从现金桶减去找零。此处 mock 回放 tendered + change,真正跑 Python 净额逻辑。"""

    def _run(self, method_rows, change=0):
        cur = _Cur([(None, method_rows), ({"chg": Decimal(str(change))}, None)])
        out = report._by_method(cur, ("t", 9), None, None)
        return out, cur.queries

    def test_sql_shape_no_min_uuid(self):
        _, q = self._run([])
        methods_sql, change_sql = q[0][0], q[1][0]
        self.assertIn("SUM(p.amount)", methods_sql)  # 方法汇总取原始 tendered
        self.assertIn("SUM(change_amount)", change_sql)  # 找零从 pos_sales 单独汇总
        self.assertIn("FROM pos_sales", change_sql)
        self.assertNotIn("MIN(", methods_sql)  # 禁 min(uuid)——Postgres 无此聚合(根因)
        self.assertNotIn("MIN(", change_sql)

    def test_cash_amount_is_net_of_change(self):
        # 应付฿55、现金 tendered฿100、change฿45 → 净额 55(Python 侧 100 − 45)
        out, _ = self._run([{"method": "cash", "amount": Decimal("100")}], change=45)
        self.assertEqual(out, {"cash": "55.00"})

    def test_mixed_payment_non_cash_bucket_untouched(self):
        # 混合单:现金 tendered60 − change4 = 净56 + 刷卡44 → 刷卡桶不受找零影响
        out, _ = self._run(
            [
                {"method": "cash", "amount": Decimal("60")},
                {"method": "card", "amount": Decimal("44")},
            ],
            change=4,
        )
        self.assertEqual(out, {"cash": "56.00", "card": "44.00"})

    def test_non_cash_only_unchanged(self):
        # 纯非现金单:无找零(change=0),口径与旧实现一致(回归)
        out, _ = self._run([{"method": "transfer", "amount": Decimal("100")}], change=0)
        self.assertEqual(out, {"transfer": "100.00"})


class ComparePrevAndHourlyTests(unittest.TestCase):
    """仪表盘环比与分时(2026-08-04):有界窗口才有「上一等长周期」,单日窗口才有分时。"""

    _MAIN = [
        ({"gross": Decimal("300"), "sales_count": 2, "refund": Decimal("0")}, None),  # kpi
        ({"cost": Decimal("120"), "complete": True}, None),  # kpi cost_agg
        (None, []),  # by_day
        (None, []),  # by_day cost
        (None, []),  # by_method tendered
        ({"chg": Decimal("0")}, None),  # by_method change
        (None, []),  # top_products
        (None, []),  # by_cashier
    ]

    def test_unbounded_window_has_no_prev_or_hourly(self):
        out = report.sales_report(
            _Cur(list(self._MAIN) + _DASH_TAIL), tenant_id="t", workspace_client_id=9
        )
        self.assertIsNone(out["prev_kpi"])
        self.assertIsNone(out["prev_range"])
        self.assertIsNone(out["by_hour"])

    def test_prev_window_is_equal_length_and_adjacent(self):
        scripted = (
            list(self._MAIN)
            + [
                (
                    {"gross": Decimal("100"), "sales_count": 1, "refund": Decimal("0")},
                    None,
                ),  # prev kpi
                ({"cost": Decimal("40"), "complete": True}, None),  # prev cost_agg
            ]
            + _DASH_TAIL
        )
        cur = _Cur(scripted)
        out = report.sales_report(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 7),
        )
        self.assertEqual(out["prev_range"], {"from": "2026-05-25", "to": "2026-05-31"})
        self.assertEqual(out["prev_kpi"]["gross"], "100.00")
        self.assertIsNone(out["by_hour"])  # 多日窗口无分时
        # 环比查询真的落在上一窗口:prev kpi 那句(尾部 heat+live 三句之前的第二句)的参数
        # 含 05-25 与 06-01(半开上界)
        prev_params = cur.queries[-5][1]
        self.assertIn(date(2026, 5, 25), prev_params)
        self.assertIn(date(2026, 6, 1), prev_params)

    def test_single_day_window_gets_hourly_buckets(self):
        scripted = (
            list(self._MAIN)
            + [
                (
                    {"gross": Decimal("0"), "sales_count": 0, "refund": Decimal("0")},
                    None,
                ),  # prev kpi
                ({"cost": Decimal("0"), "complete": True}, None),  # prev cost_agg
                (
                    None,
                    [
                        {"h": 9, "gross": Decimal("120"), "sales_count": 3},
                        {"h": 14, "gross": Decimal("180"), "sales_count": 4},
                    ],
                ),  # by_hour
            ]
            + _DASH_TAIL
        )
        out = report.sales_report(
            _Cur(scripted),
            tenant_id="t",
            workspace_client_id=9,
            date_from=date(2026, 8, 4),
            date_to=date(2026, 8, 4),
        )
        self.assertEqual(out["prev_range"], {"from": "2026-08-03", "to": "2026-08-03"})
        self.assertEqual(
            out["by_hour"],
            [
                {"hour": 9, "gross": "120.00", "sales_count": 3},
                {"hour": 14, "gross": "180.00", "sales_count": 4},
            ],
        )


class DashboardSectionsTests(unittest.TestCase):
    """仪表盘重建新增(2026-08-04):环比窗口可由前端指定语义 + heat/live 分区形状。"""

    _MAIN = ComparePrevAndHourlyTests._MAIN

    def test_prev_override_takes_precedence(self):
        """前端给了 prev_from/prev_to(上周同日)就用它,不再回落相邻等长窗口。"""
        scripted = (
            list(self._MAIN)
            + [
                (
                    {"gross": Decimal("90"), "sales_count": 1, "refund": Decimal("0")},
                    None,
                ),  # prev kpi
                ({"cost": Decimal("30"), "complete": True}, None),  # prev cost_agg
                (None, []),  # by_hour(单日窗口)
            ]
            + _DASH_TAIL
        )
        cur = _Cur(scripted)
        out = report.sales_report(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            date_from=date(2026, 8, 4),
            date_to=date(2026, 8, 4),
            prev_from=date(2026, 7, 28),
            prev_to=date(2026, 7, 28),
        )
        self.assertEqual(out["prev_range"], {"from": "2026-07-28", "to": "2026-07-28"})
        self.assertEqual(out["prev_kpi"]["gross"], "90.00")
        # prev kpi 查询(by_hour+heat+live 四句之前的第二句)参数真的落在 07-28 半开窗口
        prev_params = cur.queries[-6][1]
        self.assertIn(date(2026, 7, 28), prev_params)
        self.assertIn(date(2026, 7, 29), prev_params)

    def test_heat_window_anchored_to_date_to(self):
        """heat = 以 date_to 为锚的近 14 天,行形如 {date, hour, gross}(曼谷日 × 曼谷钟点)。"""
        heat_rows = [
            {"d": date(2026, 8, 3), "h": 9, "gross": Decimal("120")},
            {"d": date(2026, 8, 4), "h": 18, "gross": Decimal("260")},
        ]
        scripted = list(self._MAIN) + [
            ({"gross": Decimal("0"), "sales_count": 0, "refund": Decimal("0")}, None),
            ({"cost": Decimal("0"), "complete": True}, None),
            (None, []),  # by_hour(单日窗口)
            (None, heat_rows),  # heat
            ({"last_sale_at": None}, None),  # live · 最新一单
            (None, None),  # live · 无在班班次
        ]
        cur = _Cur(scripted)
        out = report.sales_report(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            date_from=date(2026, 8, 4),
            date_to=date(2026, 8, 4),
        )
        self.assertEqual(
            out["heat"],
            [
                {"date": "2026-08-03", "hour": 9, "gross": "120.00"},
                {"date": "2026-08-04", "hour": 18, "gross": "260.00"},
            ],
        )
        heat_sql, heat_params = cur.queries[-3]
        self.assertIn("Asia/Bangkok", heat_sql)
        self.assertIn(date(2026, 7, 22), heat_params)  # 锚往回 13 天
        self.assertIn(date(2026, 8, 5), heat_params)  # 半开上界 = 锚 + 1 天

    def test_live_shape_with_open_shift(self):
        last_sale = datetime(2026, 8, 4, 6, 7, tzinfo=timezone.utc)
        scripted = list(self._MAIN) + [
            (None, []),  # heat
            ({"last_sale_at": last_sale}, None),  # live · 最新一单
            ({"shift_seq": 4, "cashier_name": "earn"}, None),  # live · 在班班次
        ]
        out = report.sales_report(_Cur(scripted), tenant_id="t", workspace_client_id=9)
        self.assertEqual(
            out["live"],
            {
                "last_sale_at": "2026-08-04T06:07:00+00:00",
                "open_shift": {"cashier_name": "earn", "shift_seq": 4},
            },
        )


class SectionFilterTests(unittest.TestCase):
    """sections 轻参数(2026-08-06):只算命中的分区,未请求键省略——翻页只取 by_day 时
    SQL 句数从 8+ 掉到 2,热力标题又借 heat_range 标注窗口。"""

    def test_by_day_only_runs_two_queries(self):
        cur = _Cur([(None, []), (None, [])])  # by_day + cost_by_day
        out = report.sales_report(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            date_from=date(2026, 8, 1),
            date_to=date(2026, 8, 31),
            sections={"by_day"},
        )
        self.assertEqual(list(out), ["by_day"])
        self.assertEqual(len(cur.queries), 2)

    def test_kpi_only_runs_two_queries(self):
        cur = _Cur(
            [
                ({"gross": Decimal("1"), "sales_count": 1, "refund": Decimal("0")}, None),
                ({"cost": Decimal("0"), "complete": True}, None),
            ]
        )
        out = report.sales_report(cur, tenant_id="t", workspace_client_id=9, sections={"kpi"})
        self.assertEqual(list(out), ["kpi"])
        self.assertEqual(len(cur.queries), 2)

    def test_heat_section_carries_range(self):
        cur = _Cur([(None, [])])  # heat 单句
        out = report.sales_report(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            date_from=date(2026, 8, 4),
            date_to=date(2026, 8, 4),
            sections={"heat"},
        )
        self.assertEqual(list(out), ["heat", "heat_range"])
        self.assertEqual(len(cur.queries), 1)
        self.assertEqual(out["heat_range"], {"from": "2026-07-22", "to": "2026-08-04"})

    def test_unknown_section_name_ignored(self):
        cur = _Cur([])
        out = report.sales_report(cur, tenant_id="t", workspace_client_id=9, sections={"bogus"})
        self.assertEqual(out, {})

    def test_heat_range_defaults_to_bangkok_today(self):
        """无 date_to 时锚 = 曼谷今天,范围仍是 14 个曼谷日(from = to − 13 天)。"""
        from datetime import timedelta

        cur = _Cur([(None, [])])
        out = report.sales_report(cur, tenant_id="t", workspace_client_id=9, sections={"heat"})
        to = date.fromisoformat(out["heat_range"]["to"])
        frm = date.fromisoformat(out["heat_range"]["from"])
        self.assertEqual(frm, to - timedelta(days=13))

    def test_heat_range_matches_heat_window_query(self):
        """回显范围与 _heat 实际查询窗口同源:半开上界 = to + 1 天。"""
        cur = _Cur([(None, [])])
        out = report.sales_report(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            date_to=date(2026, 8, 4),
            sections={"heat"},
        )
        self.assertEqual(out["heat_range"], {"from": "2026-07-22", "to": "2026-08-04"})
        sql, params = cur.queries[0]
        self.assertIn("Asia/Bangkok", sql)
        self.assertIn(date(2026, 7, 22), params)
        self.assertIn(date(2026, 8, 5), params)


if __name__ == "__main__":
    unittest.main()
