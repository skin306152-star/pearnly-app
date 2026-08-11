# -*- coding: utf-8 -*-
"""风控 A 类日期规则的曼谷日切边界(services/knowledge/rules/validity.py)。

服务器跑 UTC,曼谷 00:00–07:00 期间 UTC 还停在昨天:R-DATE-01 会把当天开的票判成未来日,
R-DATE-02 的 current_month/prev_month 窗口在月初那几小时整体退一个月。ctx.today 显式传值的
调用方不受影响,这里只锁没传值时的兜底(= 真实链路上 OCR 复核走的那条)。

新建而非并进 tests/unit/knowledge/test_rules_engine.py:那份是从 sandbox 逐字迁来的
pytest 函数式用例(靠 _pytest_adapter 包成 TestCase),这里按仓库 unittest 口径写。
"""

import unittest
from datetime import date, datetime, timedelta, timezone
from unittest import mock

from services.knowledge.rules.context import ClientRuleSet, Invoice, RuleContext
from services.knowledge.rules.validity import r_date_01_legal, r_date_02_accounting_period
from services.knowledge.schema import RULE_ACCOUNTING_PERIOD, SUBJECT_GLOBAL, ClientRule


class _FrozenDatetime:
    """UTC 6-30 17:30 = 曼谷 7-01 00:30:两边不同日、且不同月。"""

    @staticmethod
    def now(tz=None):
        return datetime(2026, 6, 30, 17, 30, tzinfo=timezone.utc).astimezone(tz)


def _invoice(invoice_date: str) -> Invoice:
    return Invoice(invoice_no="INV-001", invoice_date=invoice_date)


def _ctx(rules: ClientRuleSet = None) -> RuleContext:
    return RuleContext(tenant_id="t", rules=rules or ClientRuleSet())


def _current_month_rule() -> ClientRuleSet:
    return ClientRuleSet.from_rules(
        [
            ClientRule(
                id=1,
                tenant_id="t",
                workspace_client_id=None,
                rule_type=RULE_ACCOUNTING_PERIOD,
                subject_type=SUBJECT_GLOBAL,
                subject_key=None,
                rule_body={"mode": "current_month"},
                severity=None,
                is_active=True,
                effective_from=None,
                effective_to=None,
                origin="manual",
                created_at=datetime(2026, 6, 30),
            )
        ]
    )


def _fired(findings) -> set:
    return {f.rule_id for f in findings}


class ValidityClockTests(unittest.TestCase):
    def test_the_frozen_instant_really_straddles_the_month(self):
        instant = _FrozenDatetime.now(timezone.utc)
        self.assertEqual(instant.date(), date(2026, 6, 30))
        self.assertEqual((instant + timedelta(hours=7)).date(), date(2026, 7, 1))

    def test_today_in_bangkok_is_not_a_future_invoice_date(self):
        with mock.patch("services.sales.dates.datetime", _FrozenDatetime):
            findings = r_date_01_legal(_invoice("2026-07-01"), _ctx())
        self.assertEqual(_fired(findings), set())

    def test_tomorrow_in_bangkok_still_fires(self):
        with mock.patch("services.sales.dates.datetime", _FrozenDatetime):
            findings = r_date_01_legal(_invoice("2026-07-02"), _ctx())
        self.assertEqual(_fired(findings), {"R-DATE-01"})

    def test_accounting_window_follows_the_bangkok_month(self):
        with mock.patch("services.sales.dates.datetime", _FrozenDatetime):
            findings = r_date_02_accounting_period(
                _invoice("2026-07-01"), _ctx(_current_month_rule())
            )
        self.assertEqual(_fired(findings), set())

    def test_previous_bangkok_month_is_out_of_window(self):
        # 反向自证:窗口真是 7 月,6-30 的票才会被判出期(窗口若还停在 6 月,这条不会响)。
        with mock.patch("services.sales.dates.datetime", _FrozenDatetime):
            findings = r_date_02_accounting_period(
                _invoice("2026-06-30"), _ctx(_current_month_rule())
            )
        self.assertEqual(_fired(findings), {"R-DATE-02"})
        self.assertEqual(findings[0].evidence["period_start"], "2026-07-01")

    def test_explicit_ctx_today_still_wins(self):
        with mock.patch("services.sales.dates.datetime", _FrozenDatetime):
            ctx = RuleContext(tenant_id="t", today=date(2026, 6, 30))
            findings = r_date_01_legal(_invoice("2026-07-01"), ctx)
        self.assertEqual(_fired(findings), {"R-DATE-01"})


if __name__ == "__main__":
    unittest.main()
