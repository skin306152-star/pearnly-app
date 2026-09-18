"""同一批 OCR 里"同名公司"不得建成两个账套(2026-09-18 线上重复账套事故回归)。

事故:一份 13 页 PDF,12 页读到卖方税号、1 页没读到。旧行为按 ("tax")/("name") 两个身份键
各建一个账套 → 同一家公司两个账套 → 下次上传时名字匹配到两个 → 整批 409 workspace_ambiguous。
"""

import unittest
from unittest import mock

from services.ocr.recognize import workspace_assignment

SAME_TAX = "0105546015062"
OTHER_TAX = "0735527000289"


def _fields(name, tax, direction="sales"):
    return {
        "seller_name": name,
        "seller_tax": tax,
        "buyer_name": "Buyer Co",
        "buyer_tax": "0105550001111",
        "direction": direction,
    }


def _plan(fields, direction):
    return {
        "action": "create",
        "workspace_client_id": None,
        "workspace_name": str(fields.get("seller_name") or ""),
        "subject": {
            "tax_id": str(fields.get("seller_tax") or ""),
            "name": str(fields.get("seller_name") or ""),
        },
        "direction": direction,
    }


class _Batch:
    """跑一次 resolve_batch,返回(决策列表, 建账套次数)。"""

    def __init__(self, assignments, plans=None):
        self.assignments = assignments
        self.created = []
        self.plans = plans

    def run(self):
        def materialize(plan, _user_id, _tenant_id, **_kwargs):
            # 与真 materialize_assignment 同口径:已经命中账套的计划原样返回,只对 create 建新账套
            if plan.get("workspace_client_id"):
                return dict(plan)
            workspace_id = 900 + len(self.created)
            self.created.append(plan)
            return {
                "workspace_client_id": workspace_id,
                "action": "created",
                "workspace_name": plan["workspace_name"],
                "subject": dict(plan["subject"]),
            }

        user = {"id": "user-1", "tenant_id": "tenant-1", "is_super_admin": True}
        with (
            mock.patch.object(
                workspace_assignment.document_assignment,
                "prepare_assignment",
                side_effect=(
                    self.plans
                    if self.plans is not None
                    else (lambda fields, direction, *_a, **_k: _plan(fields, direction))
                ),
            ),
            mock.patch.object(
                workspace_assignment.document_assignment,
                "materialize_assignment",
                side_effect=materialize,
            ),
            mock.patch.object(workspace_assignment, "_log_created"),
        ):
            decisions = workspace_assignment.resolve_batch(
                self.assignments,
                user,
                "manual",
                fallback_workspace_id=None,
            )
        return decisions, len(self.created)


class OcrWorkspaceBatchAssignmentTests(unittest.TestCase):
    def test_missing_tax_on_one_page_reuses_the_same_company_account_set(self):
        """税号读不出来的那页跟同批同名的其他页共用一个账套,不再建第二个。"""
        decisions, created = _Batch(
            [
                (_fields("Sincere Ice", SAME_TAX), "sales"),
                (_fields("Sincere Ice", ""), "sales"),
            ]
        ).run()

        self.assertEqual(created, 1)
        self.assertEqual([d["workspace_client_id"] for d in decisions], [900, 900])

    def test_canonical_account_set_is_the_page_with_tax_whatever_the_order(self):
        """规范账套取"带税号"的那一页,与它在批次里出现的先后无关。"""
        for order in ("tax_first", "tax_last"):
            with self.subTest(order=order):
                taxes = (SAME_TAX, "") if order == "tax_first" else ("", SAME_TAX)
                decisions, created = _Batch(
                    [
                        (_fields("Sincere Ice", taxes[0]), "sales"),
                        (_fields("Sincere Ice", taxes[1]), "sales"),
                    ]
                ).run()

                self.assertEqual(created, 1)
                self.assertEqual([d["workspace_client_id"] for d in decisions], [900, 900])
                self.assertEqual(decisions[0]["subject"]["tax_id"], SAME_TAX)

    def test_same_name_with_two_different_tax_ids_stays_two_account_sets(self):
        """同名但各自有不同税号 = 两家公司,不能收拢。"""
        decisions, created = _Batch(
            [
                (_fields("Sincere Ice", SAME_TAX), "sales"),
                (_fields("Sincere Ice", OTHER_TAX), "sales"),
            ]
        ).run()

        self.assertEqual(created, 2)
        self.assertEqual([d["workspace_client_id"] for d in decisions], [900, 901])

    def test_different_companies_are_untouched(self):
        decisions, created = _Batch(
            [
                (_fields("Alpha Co", SAME_TAX), "sales"),
                (_fields("Beta Co", ""), "sales"),
            ]
        ).run()

        self.assertEqual(created, 2)
        self.assertEqual([d["workspace_client_id"] for d in decisions], [900, 901])

    def test_taxless_page_follows_a_sibling_that_hit_an_existing_account_set(self):
        """线上真实形态:12 页带税号命中已有账套,第 13 页税号读空且名字与已有账套拼写不同
        → 不能因此再建一个账套,要落到兄弟页命中的那个。"""
        existing = {
            "workspace_client_id": 107,
            "action": "unbound",
            "workspace_name": "Sincere Ice",
            "subject": {"tax_id": SAME_TAX, "name": "Sincere Ice"},
        }
        decisions, created = _Batch(
            [
                (_fields("Sincere Ice", SAME_TAX), "sales"),
                (_fields("Sincere Ice", ""), "sales"),
            ],
            plans=[existing, _plan(_fields("Sincere Ice", ""), "sales")],
        ).run()

        self.assertEqual(created, 0)
        self.assertEqual([d["workspace_client_id"] for d in decisions], [107, 107])

    def test_taxless_page_with_a_different_tax_than_the_sibling_still_creates(self):
        """兄弟页命中的账套税号与这页读到的税号冲突 → 是两家公司,照旧新建。"""
        existing = {
            "workspace_client_id": 107,
            "action": "unbound",
            "workspace_name": "Sincere Ice",
            "subject": {"tax_id": SAME_TAX, "name": "Sincere Ice"},
        }
        decisions, created = _Batch(
            [
                (_fields("Sincere Ice", SAME_TAX), "sales"),
                (_fields("Sincere Ice", OTHER_TAX), "sales"),
            ],
            plans=[existing, _plan(_fields("Sincere Ice", OTHER_TAX), "sales")],
        ).run()

        self.assertEqual(created, 1)
        self.assertEqual([d["workspace_client_id"] for d in decisions], [107, 900])


if __name__ == "__main__":
    unittest.main()
