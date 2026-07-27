# -*- coding: utf-8 -*-
"""跨仓契约闸:云端**真产物** → 桥端消费契约。

P2-B 的假绿是这样来的 —— 云端测试断言"组装产物 ⊆ 云端自己的常量",桥端测试断言"白名单
== 桥端自己的副本",两边全绿,而四类下行路径实测一类都走不通(三类被载荷白名单当场
bad_payload,唯一过白名单的手工凭证死在 INVALID_DOC_DATE)。缺的从来不是断言数量,是
**没有任何一处把云端产物拿给桥端看**。

所以这里分两层,缺一层就回到假绿:
  ① 镜像层(恒跑):产物比 bridge_contract.py 里逐字抄来的桥端契约。CI 没有桥仓,靠它兜。
  ② 真桥层(有桥仓才跑):直接 import 桥端 `writepath/doc_*.validate` 喂产物,并把镜像
     与桥端白名单**逐键对等**比一次 —— 镜像抄漏/抄错在这里当场红。开发机(改契约的地方)
     一定有桥仓,所以这一层落在"谁改谁被抓"的位置上,而不是等上线后由会计发现。

桥仓路径:环境变量 PEARNLY_COMPANION_DIR,缺省取 pearnly-app 的兄弟目录。桥仓只读 import,
不改它一个字节(桥要发版 + 等装机量滚动,窗口期以天计)。
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.express_push.bridge_contract import (  # noqa: E402
    BRIDGE_ACCEPTED_KEYS,
    BRIDGE_CONDITIONAL_KEYS,
    BRIDGE_REQUIRED_KEYS,
    BRIDGE_REQUIRED_NESTED_KEYS,
    BRIDGE_REQUIRED_ROW_KEYS,
    DOC_TYPES,
)
from tests.unit._express_doctype_golden import BOOK, golden_payloads  # noqa: E402

# 四类各自的单据日键。老链路的佛历 `docdate_be` 一个都不该出现 —— 桥端
# `doc_payload.iso_date` 只认 date.fromisoformat,佛历串在那边一律 INVALID_DOC_DATE。
_DATE_KEYS = {
    "ar_receipt": "receipt_date",
    "ap_payment": "payment_date",
    "gl_journal": "voucher_date",
    "stock_adjust": "doc_date",
}


def _companion_dir() -> Path:
    return Path(
        os.environ.get("PEARNLY_COMPANION_DIR") or PROJECT_ROOT.parent / "pearnly-companion"
    )


def _bridge():
    """桥仓的四个 validate + 载荷白名单;桥仓不在(CI)返回 None。"""
    root = _companion_dir()
    if not (root / "bridge" / "writepath" / "doc_receipt.py").exists():
        return None
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from bridge import cloud_jobs
        from bridge.writepath import doc_journal, doc_payment, doc_receipt, doc_stock_adjust
    except ImportError:  # 桥仓在但依赖没装 —— 当没有,别把 CI 判红在别人的环境上
        return None
    return {
        "whitelist": frozenset(cloud_jobs._ALL_WRITE_PAYLOAD_KEYS),
        "validate": {
            "ar_receipt": doc_receipt.validate,
            "ap_payment": doc_payment.validate,
            "gl_journal": doc_journal.validate,
            "stock_adjust": doc_stock_adjust.validate,
        },
    }


_BRIDGE = _bridge()


class BridgeMirrorContractTests(unittest.TestCase):
    """产物 vs 桥端契约镜像。桥仓不在也跑得动,是 CI 里的那道闸。"""

    def setUp(self):
        self.payloads = golden_payloads()

    def test_every_doctype_has_a_golden_payload(self):
        # golden 少一类 = 下面每条断言在那一类上恒真,整组闸静默失效。
        self.assertEqual(set(self.payloads), set(DOC_TYPES))

    def test_top_level_keys_within_bridge_whitelist(self):
        # 桥端 cloud_jobs 对顶层键做白名单:多一个键不是少验一道闸,是整单 bad_payload。
        for doc_type, payload in self.payloads.items():
            with self.subTest(doc_type=doc_type):
                extra = sorted(set(payload) - BRIDGE_ACCEPTED_KEYS)
                self.assertFalse(extra, f"桥端不认得这些键,整单会被拒: {extra}")

    def test_required_top_level_keys_present(self):
        for doc_type, payload in self.payloads.items():
            with self.subTest(doc_type=doc_type):
                missing = sorted(BRIDGE_REQUIRED_KEYS[doc_type] - set(payload))
                self.assertFalse(missing, f"桥端 validate 点名要的键缺了: {missing}")

    def test_required_row_keys_present(self):
        # 子表这层比顶层凶:桥端用 .get() 读,名字不对不抛错而是当"没给"——
        # 渠道前缀丢了是 ACCOUNT_NOT_RESOLVED,批号丢了是几个月后成本对不上。
        for doc_type, tables in BRIDGE_REQUIRED_ROW_KEYS.items():
            payload = self.payloads[doc_type]
            for table, keys in tables.items():
                rows = payload.get(table) or []
                self.assertTrue(rows, f"{doc_type}.{table} golden 是空的,这组闸等于没跑")
                for i, row in enumerate(rows):
                    with self.subTest(doc_type=doc_type, table=table, row=i):
                        self.assertFalse(sorted(keys - set(row)))

    def test_required_nested_keys_present(self):
        for doc_type, blocks in BRIDGE_REQUIRED_NESTED_KEYS.items():
            for block, keys in blocks.items():
                with self.subTest(doc_type=doc_type, block=block):
                    got = self.payloads[doc_type].get(block)
                    self.assertIsInstance(got, dict, f"{doc_type}.{block} golden 没带上")
                    self.assertFalse(sorted(keys - set(got)))

    def test_conditional_keys_present_when_triggered(self):
        # 条件键的坑是"平时不出现所以永远测不到"。golden 特意把触发条件都踩上。
        for doc_type, keys in BRIDGE_CONDITIONAL_KEYS.items():
            for key, when in keys.items():
                with self.subTest(doc_type=doc_type, key=key):
                    self.assertIn(key, self.payloads[doc_type], f"触发条件:{when}")

    def test_dates_are_gregorian_iso_not_buddhist(self):
        for doc_type, key in _DATE_KEYS.items():
            with self.subTest(doc_type=doc_type):
                payload = self.payloads[doc_type]
                self.assertNotIn("docdate_be", payload)
                raw = payload[key]
                self.assertRegex(raw, r"^\d{4}-\d{2}-\d{2}$")
                # 佛历 2569 被当公历读会落进一个"合法但不是那天"的年份。
                self.assertLess(int(raw[:4]), 2400)

    def test_derived_buckets_are_not_shipped(self):
        # 桥端按 channels/settlements 自推分桶,云端再发一份只会两边打架或整单被拒。
        derived = {"net_amount", "cash_amount", "cheque_amount", "advance_amount", "posopr"}
        for doc_type, payload in self.payloads.items():
            with self.subTest(doc_type=doc_type):
                self.assertFalse(derived & set(payload))


@unittest.skipUnless(_BRIDGE, f"桥仓不在 {_companion_dir()} · 跳过真桥层")
class BridgeLiveValidateTests(unittest.TestCase):
    """把云端真产物喂进桥端真 validate。这一层才是"下行路径走不走得通"的唯一凭据。"""

    def test_mirror_matches_bridge_whitelist_exactly(self):
        # 镜像是手抄的,抄漏一个键上面整组闸就在放行桥端不认的载荷。
        diff = sorted(BRIDGE_ACCEPTED_KEYS ^ _BRIDGE["whitelist"])
        self.assertFalse(diff, f"bridge_contract 镜像与桥端白名单不一致: {diff}")

    def test_each_payload_passes_bridge_validate(self):
        for doc_type, payload in golden_payloads().items():
            with self.subTest(doc_type=doc_type):
                result = _BRIDGE["validate"][doc_type](payload, (BOOK,))
                self.assertTrue(result.ok, f"{result.error_code}: {result.detail}")

    def test_bridge_rejects_the_buddhist_date_we_used_to_send(self):
        # 反证:真桥层不是"喂什么都绿"。P2-B 那刀原样重放一次。
        payload = {**golden_payloads()["ar_receipt"], "receipt_date": "690115"}
        result = _BRIDGE["validate"]["ar_receipt"](payload, (BOOK,))
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "INVALID_DOC_DATE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
