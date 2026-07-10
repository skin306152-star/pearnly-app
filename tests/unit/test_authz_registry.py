# -*- coding: utf-8 -*-
"""registry 守门:权限码格式/动词收敛/模块映射合法/自检抓漂移(docs/permissions/02)。"""

import re
import unittest

from services.authz import registry
from services.modules.store import KNOWN_MODULES

# 8 个收敛动词 + 图纸钦定特例(acct.entry.review 逐笔审 · kb.ask 问答 ·
# tax.filing.review/file C3 四权分立复核签批/申报回执)
_VERBS = {"view", "create", "edit", "delete", "approve", "export", "manage", "operate"}
_VERB_EXCEPTIONS = {
    "acct.entry.review",
    "kb.ask",
    "intake.upload",
    "tax.filing.review",
    "tax.filing.file",
}

_CODE_RE = re.compile(r"^[a-z]+(\.[a-z_]+){1,2}$")


class RegistryShapeTests(unittest.TestCase):
    def test_no_duplicate_codes(self):
        groups = (
            registry.CROSS_CODES
            + registry.SALES_CODES
            + registry.PURCHASE_CODES
            + registry.ACCT_CODES
            + registry.TAX_CODES
            + registry.RECON_CODES
            + registry.AR_CODES
            + registry.KB_CODES
            + registry.INV_CODES
            + registry.POS_CODES
            + registry.INTAKE_CODES
            + registry.FIELD_CODES
        )
        self.assertEqual(len(groups), len(registry.ALL_CODES))

    def test_code_format_and_verbs(self):
        cross = set(registry.CROSS_CODES)
        for code in registry.ALL_CODES:
            self.assertRegex(code, _CODE_RE)
            # 动词收敛只约束业务模块(横切域 invite/toggle 等是图纸原文)
            if code in cross or code in _VERB_EXCEPTIONS:
                continue
            verb = code.rsplit(".", 1)[-1]
            self.assertIn(verb, _VERBS, f"{code} 动词越界(02 图纸禁自造)")

    def test_module_mapping_complete_and_valid(self):
        self.assertEqual(set(registry.MODULE_OF), set(registry.ALL_CODES))
        for code, mod in registry.MODULE_OF.items():
            if mod is not None:
                self.assertIn(mod, KNOWN_MODULES, f"{code} 映射到未知模块 {mod}")

    def test_cross_domain_codes_have_no_module_gate(self):
        for code in registry.CROSS_CODES:
            self.assertIsNone(registry.module_of(code), f"横切域 {code} 不该挂模块开关")

    def test_business_codes_gated_by_module(self):
        for code in registry.SALES_CODES:
            self.assertEqual(registry.module_of(code), "sales")
        for code in registry.PURCHASE_CODES + registry.INTAKE_CODES:
            self.assertEqual(registry.module_of(code), "expense")
        for code in registry.POS_CODES:
            self.assertEqual(registry.module_of(code), "pos")


class SelfcheckTests(unittest.TestCase):
    def test_healthy_state_no_problems(self):
        self.assertEqual(registry.selfcheck(), [])

    def test_unknown_jsonb_code_reported(self):
        problems = registry.selfcheck({"accountant": ["sales.doc.view", "made.up.code"]})
        self.assertEqual(len(problems), 1)
        self.assertIn("made.up.code", problems[0])

    def test_known_jsonb_codes_clean(self):
        problems = registry.selfcheck({"viewer": sorted(registry.ROLE_PERMISSIONS["viewer"])})
        self.assertEqual(problems, [])
