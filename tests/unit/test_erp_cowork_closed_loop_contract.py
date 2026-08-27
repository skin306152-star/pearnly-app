# -*- coding: utf-8 -*-
"""PO-0 契约测试 · ERP 与 Cowork 闭环(只验契约,不验实现)。

守住以下合同:
1. 金标夹具形状正确、scenario id 唯一、数量足够;
2. 关系、投递、租户分类与失败码枚举精确;
3. 不变式标识(INV-###)在文档与夹具间完整双向覆盖;
4. 高风险场景与 /ai /pos /dms 零变化哨兵不得缺失;
5. 每个失败码都必须有场景证据;
6. 规格红线短语逐项出现(只判短语,不判整段);
7. 规格与夹具的中文正文不含 emoji。

本文件只读两个契约资产:docs/erp/ERP-COWORK-CLOSED-LOOP.md 与金标
tests/fixtures/erp_cowork_goldens.json。不连网络、不连数据库、不 import 任何业务模块。
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CANONICAL_DOC = PROJECT_ROOT / "docs" / "erp" / "ERP-COWORK-CLOSED-LOOP.md"
GOLDENS = PROJECT_ROOT / "tests" / "fixtures" / "erp_cowork_goldens.json"

EXPECTED_ENGAGEMENT_STATUSES = frozenset(
    {"pending_merchant", "pending_firm", "active", "suspended", "ended"}
)
EXPECTED_SUBMISSION_STATUSES = frozenset({"pending", "delivered", "failed", "superseded"})
EXPECTED_TENANT_TYPES = frozenset({"s_micro", "m_business", "f_firm"})
EXPECTED_FAILURE_CODES = frozenset(
    {
        "ERR_FIRM_REQUIRED",
        "ERR_FIRM_INACTIVE",
        "ERR_PRIMARY_ENGAGEMENT_EXISTS",
        "ERR_ENGAGEMENT_NOT_ACTIVE",
        "ERR_ENGAGEMENT_WORKSPACE_MISMATCH",
        "ERR_ENGAGEMENT_FORBIDDEN",
        "ERR_PRODUCT_SCOPE_REQUIRED",
        "ERR_LOCATION_REQUIRED",
        "ERR_INSUFFICIENT_CREDITS",
        "ERR_SUBMISSION_DELIVERY",
    }
)

ALLOWED_SURFACES = frozenset(
    {
        "/cowork",
        "/erp",
        "/earn",
        "/ai",
        "/pos",
        "/dms",
        "background-bridge",
        "LINE",
        "all-products",
    }
)

REQUIRED_SCENARIO_KEYS = {"id", "surface", "given", "action", "expected", "invariant_ids"}

# 产品边界哨兵:必须存在、面必须正确、必须挂在产品防火墙不变式上。
PRODUCT_BOUNDARY_SENTINELS = {
    "ai-zero-change-sentinel": "/ai",
    "pos-zero-change-sentinel": "/pos",
    "dms-zero-change-sentinel": "/dms",
}

REQUIRED_SCENARIO_IDS = frozenset(
    {
        "cowork-free-registration-success",
        "erp-invite-reuse-existing-merchant",
        "erp-invite-new-merchant-defers-workspace",
        "existing-primary-firm-requires-transfer",
        "earn-metadata-only",
        "firm-merchant-authz-boundary",
        "engagement-active-requires-both-workspaces",
        "cowork-explicit-workspace-selection",
        "suspended-engagement-blocks-future-delivery",
        "ended-engagement-does-not-create-old-firm-submission",
        "confirmed-document-atomic-create",
        "confirmed-document-duplicate",
        "wrong-firm-cannot-read-submission",
        "ocr-discard-zero-business-effect",
        "cowork-edits-review-copy-not-merchant-stock",
        "insufficient-credits-blocks-before-ocr",
        "erp-line-no-reuse-dms-procurement-tables",
        "stockcard-deletion-gated-on-golden-and-exclusivity",
        "failure-states-never-display-success",
    }
)

INVARIANT_RE = re.compile(r"\b(INV-\d{3})\b")

# 规格红线短语。选取的是稳定、不可拆的短短语与术语,不判整段,避免脆弱匹配。
RED_LINE_PHRASES = (
    "product_scope=erp",
    "s_micro",
    "m_business",
    "f_firm",
    "business_location",
    "00000",
    "accounting_engagement",
    "pending_merchant",
    "pending_firm",
    "client_submissions",
    "erp_push_logs",
    "唯一跨租户关系锚",
    "独立授权和计费边界",
    "独立钱包",
    "邀请制",
    "绝不静默",
    "唯一键",
    "ERR_ENGAGEMENT_FORBIDDEN",
    "firm_workspace_client_id NULLABLE",
    "merchant_workspace_client_id NULLABLE",
)

# 覆盖常见 emoji 区段与变体选择符;中文(CJK)不在其中,不会误报。
_EMOJI_RE = re.compile(
    "[\U0001f300-\U0001faff\U00002600-\U000027bf\U0001f000-\U0001f0ff"
    "\U00002b00-\U00002bff\U0000fe00-\U0000fe0f\U0001f1e6-\U0001f1ff]"
)


def load_doc() -> str:
    with open(CANONICAL_DOC, encoding="utf-8") as f:
        return f.read()


def load_goldens() -> dict:
    with open(GOLDENS, encoding="utf-8") as f:
        return json.load(f)


def doc_invariants(doc: str) -> set[str]:
    """文档里出现的所有不变式标识。"""
    return set(INVARIANT_RE.findall(doc))


def scenario_invariant_union(goldens: dict) -> set[str]:
    union: set[str] = set()
    for scene in goldens["scenarios"]:
        union.update(scene["invariant_ids"])
    return union


class GoldensFixtureShape(unittest.TestCase):
    """夹具形状与规模。"""

    @classmethod
    def setUpClass(cls):
        cls.goldens = load_goldens()
        cls.scenarios = cls.goldens["scenarios"]

    def test_fixture_is_json_object(self):
        self.assertIsInstance(self.goldens, dict)
        self.assertEqual(self.goldens["schema_version"], 1)
        self.assertEqual(self.goldens["product_scope"], "erp")

    def test_canonical_doc_points_at_the_doc_under_test(self):
        self.assertEqual(self.goldens["canonical_doc"], "docs/erp/ERP-COWORK-CLOSED-LOOP.md")

    def test_minimum_scenario_count(self):
        self.assertGreaterEqual(len(self.scenarios), 45)

    def test_scenario_ids_are_unique(self):
        ids = [s["id"] for s in self.scenarios]
        self.assertEqual(len(ids), len(set(ids)), "场景 id 必须唯一")

    def test_scenario_ids_are_named(self):
        for scene in self.scenarios:
            self.assertRegex(scene["id"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    def test_required_risk_scenarios_are_present(self):
        actual = {scene["id"] for scene in self.scenarios}
        self.assertEqual(REQUIRED_SCENARIO_IDS - actual, set())

    def test_every_scenario_has_all_required_keys(self):
        for scene in self.scenarios:
            self.assertTrue(
                REQUIRED_SCENARIO_KEYS.issubset(set(scene)),
                f"场景 {scene.get('id')} 缺字段 {REQUIRED_SCENARIO_KEYS - set(scene)}",
            )

    def test_every_scenario_has_a_known_surface(self):
        for scene in self.scenarios:
            self.assertIn(scene["surface"], ALLOWED_SURFACES, scene["id"])

    def test_every_scenario_invariant_ids_is_a_non_empty_list(self):
        for scene in self.scenarios:
            self.assertIsInstance(scene["invariant_ids"], list, scene["id"])
            self.assertGreater(len(scene["invariant_ids"]), 0, scene["id"])
            self.assertEqual(
                len(scene["invariant_ids"]),
                len(set(scene["invariant_ids"])),
                f"{scene['id']} 不变式不得重复",
            )
            for inv in scene["invariant_ids"]:
                self.assertIsInstance(inv, str, scene["id"])
                self.assertRegex(inv, r"^INV-\d{3}$", scene["id"])


class EnumeratedContractSets(unittest.TestCase):
    """状态、分类与失败码枚举必须精确。"""

    @classmethod
    def setUpClass(cls):
        cls.goldens = load_goldens()

    def test_engagement_statuses_exact_set(self):
        self.assertEqual(set(self.goldens["engagement_statuses"]), EXPECTED_ENGAGEMENT_STATUSES)

    def test_submission_statuses_exact_set(self):
        self.assertEqual(set(self.goldens["submission_statuses"]), EXPECTED_SUBMISSION_STATUSES)

    def test_tenant_types_exact_set(self):
        self.assertEqual(set(self.goldens["tenant_type_v2_values"]), EXPECTED_TENANT_TYPES)

    def test_unclassified_tenant_layer_is_nullable_not_a_fourth_type(self):
        self.assertIs(self.goldens["tenant_type_v2_allows_unclassified_null"], True)
        self.assertNotIn(None, self.goldens["tenant_type_v2_values"])

    def test_failure_codes_exact_set(self):
        self.assertEqual(set(self.goldens["failure_codes"]), EXPECTED_FAILURE_CODES)

    def test_every_failure_code_has_scenario_evidence(self):
        scenario_text = "\n".join(scene["expected"] for scene in self.goldens["scenarios"])
        missing = {code for code in EXPECTED_FAILURE_CODES if code not in scenario_text}
        self.assertEqual(missing, set())


class InvariantCoverage(unittest.TestCase):
    """不变式在文档与夹具间双向覆盖。"""

    @classmethod
    def setUpClass(cls):
        cls.doc = load_doc()
        cls.goldens = load_goldens()
        cls.doc_inv = doc_invariants(cls.doc)
        cls.scene_inv = scenario_invariant_union(cls.goldens)

    def test_doc_defines_invariants(self):
        self.assertGreaterEqual(len(self.doc_inv), 19, "文档必须定义不变式标识")

    def test_every_doc_invariant_is_covered_by_a_scenario(self):
        missing = self.doc_inv - self.scene_inv
        self.assertEqual(missing, set(), "文档不变式没有被任何场景覆盖")

    def test_no_scenario_references_unknown_invariant(self):
        unknown = self.scene_inv - self.doc_inv
        self.assertEqual(unknown, set(), "场景引用了文档未定义的不变式")

    def test_coverage_is_complete(self):
        self.assertEqual(self.doc_inv, self.scene_inv)

    def test_key_invariants_present(self):
        required = {
            "INV-011",
            "INV-012",
            "INV-013",
            "INV-014",
            "INV-015",
            "INV-016",
            "INV-017",
            "INV-018",
            "INV-019",
        }
        self.assertTrue(required.issubset(self.doc_inv), required - self.doc_inv)


class ProductBoundarySentinels(unittest.TestCase):
    """/ai /pos /dms 零改动哨兵必须存在且落在产品防火墙不变式上。"""

    @classmethod
    def setUpClass(cls):
        cls.by_id = {s["id"]: s for s in load_goldens()["scenarios"]}

    def test_all_sentinels_present(self):
        for sid in PRODUCT_BOUNDARY_SENTINELS:
            self.assertIn(sid, self.by_id, f"缺哨兵 {sid}")

    def test_sentinel_surfaces_are_the_other_entries(self):
        for sid, surface in PRODUCT_BOUNDARY_SENTINELS.items():
            self.assertEqual(self.by_id[sid]["surface"], surface, sid)
            self.assertNotEqual(surface, "/erp")

    def test_sentinels_carry_product_firewall_invariant(self):
        for sid in PRODUCT_BOUNDARY_SENTINELS:
            self.assertIn("INV-016", self.by_id[sid]["invariant_ids"], sid)

    def test_sentinels_cover_all_protected_state(self):
        for sid in PRODUCT_BOUNDARY_SENTINELS:
            expected = self.by_id[sid]["expected"]
            for marker in ("数据", "余额", "LINE 绑定/会话", "旗标", "路由行为"):
                self.assertIn(marker, expected, f"{sid} 缺零变化维度 {marker}")


class RedLinePhrases(unittest.TestCase):
    """规格红线短语逐项出现(只判短语,不判整段)。"""

    @classmethod
    def setUpClass(cls):
        cls.doc = load_doc()

    def test_each_red_line_phrase_present(self):
        for phrase in RED_LINE_PHRASES:
            self.assertIn(phrase, self.doc, f"规格缺红线短语: {phrase}")

    def test_each_failure_code_is_defined_in_spec(self):
        for code in EXPECTED_FAILURE_CODES:
            self.assertIn(code, self.doc, f"规格缺失败码: {code}")


class NoEmojiQualityGuard(unittest.TestCase):
    """中文规范与夹具不得含 emoji。"""

    def test_doc_has_no_emoji(self):
        doc = load_doc()
        hits = sorted(set(_EMOJI_RE.findall(doc)))
        self.assertEqual(hits, [], f"规格含 emoji: {hits}")

    def test_fixture_has_no_emoji(self):
        goldens = load_goldens()
        hits = sorted(set(_EMOJI_RE.findall(json.dumps(goldens, ensure_ascii=False))))
        self.assertEqual(hits, [], f"夹具含 emoji: {hits}")


if __name__ == "__main__":
    unittest.main()
