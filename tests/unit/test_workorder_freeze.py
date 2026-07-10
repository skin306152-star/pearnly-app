# -*- coding: utf-8 -*-
"""冻结 manifest 汇编守门(services/workorder/freeze.py · C-2 设计 3/5)。

纯函数 build_manifest:六要素齐(逐 item sha256 + 规则版本 + 模型版本 + 裁决回放 + 签批人 +
时间)。fail-closed:有 file_ref 却算不出哈希 → FreezeError 点名。sha256_of 注入,不碰真盘。

R1 回归:事件行 created_at 用真 datetime 类型(对齐 psycopg2 真 store 行,不许字符串替身失真)
——带裁决的 manifest 必须 JSON 可序列化(datetime→ISO / Decimal→十进制串 / 未知类型 fail-loud)。
"""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from decimal import Decimal

from services.workorder import freeze

# 对齐真库行:psycopg2 的 timestamptz 是原生 datetime(R1 打回根因=替身用字符串失真)。
_DECIDED_AT = datetime(2026, 7, 11, 0, 0, 0, tzinfo=timezone.utc)


def _wo():
    return {"id": "wo-1", "workspace_client_id": 7, "period": "2569-05"}


def _classified(item_id, kind, *, money=None, ocr_engine="pipeline_v1"):
    payload = {"item_id": item_id, "kind": kind, "status": "ok"}
    if money:
        payload["money"] = money
    if ocr_engine:
        payload["ocr_engine"] = ocr_engine
    return {"id": 1, "step": "classify", "event_type": "item_classified", "payload": payload}


def _decision(event_id, item_id, decision, **extra):
    payload = {"item_id": item_id, "decision": decision, **extra}
    return {
        "id": event_id,
        "step": "reconcile",
        "event_type": "human_decision",
        "payload": payload,
        "actor": "user:77",
        "created_at": _DECIDED_AT,
    }


_HASHES = {"/o/a.jpg": "aaa", "/o/b.jpg": "bbb"}


def _fake_hash(file_ref):
    return _HASHES.get(file_ref)


class BuildManifestTests(unittest.TestCase):
    def _items(self):
        return [
            {
                "id": "a",
                "kind": "purchase_invoice",
                "status": "ok",
                "file_ref": "/o/a.jpg",
                "original_name": "a.jpg",
            },
            {
                "id": "s",
                "kind": "sales_summary",
                "status": "ok",
                "file_ref": None,
                "original_name": None,
            },
        ]

    def _events(self):
        return [
            _classified("a", "purchase_invoice", ocr_engine="pipeline_v1"),
            _decision(5, "a", "face_value", values={"vat": "70.00"}),
        ]

    def test_six_elements_present(self):
        m = freeze.build_manifest(
            work_order=_wo(),
            items=self._items(),
            events=self._events(),
            deliverable_version=2,
            ocr_models=["gemini-3.1-flash-lite", "gemini-3.1-flash-lite"],
            approver="user:77",
            frozen_at="2026-07-11T00:00:00+00:00",
            sha256_of=_fake_hash,
        )
        # 1 逐 item 源文件 sha256(现算)
        by_id = {it["item_id"]: it for it in m["items"]}
        self.assertEqual(by_id["a"]["sha256"], "aaa")
        self.assertEqual(by_id["a"]["file_name"], "a.jpg")
        self.assertIsNone(by_id["s"]["sha256"])  # 人工填销项无源文件,非失败
        # 2 规则版本
        self.assertEqual(m["rules_version"], freeze.RULES_VERSION)
        # 3 模型版本(引擎自事件流 + 模型名自 ai_usage,去重)
        self.assertEqual(m["model_version"]["ocr_engines"], ["pipeline_v1"])
        self.assertEqual(m["model_version"]["ocr_models"], ["gemini-3.1-flash-lite"])
        # 4 裁决/豁免回放(at 源头规整:datetime 行 → ISO 字符串,R1)
        self.assertEqual(m["decisions"]["a"]["decision"], "face_value")
        self.assertEqual(m["decisions"]["a"]["actor"], "user:77")
        self.assertEqual(m["decisions"]["a"]["at"], "2026-07-11T00:00:00+00:00")
        # 5 签批人 · 6 时间
        self.assertEqual(m["approved_by"], "user:77")
        self.assertEqual(m["frozen_at"], "2026-07-11T00:00:00+00:00")
        # 回执留位 + 版本钉死
        self.assertIsNone(m["receipt"])
        self.assertEqual(m["deliverable_version"], 2)

    def test_missing_source_file_fails_closed_and_names_it(self):
        items = [
            {
                "id": "a",
                "kind": "purchase_invoice",
                "status": "ok",
                "file_ref": "/o/a.jpg",
                "original_name": "a.jpg",
            },
            {
                "id": "g",
                "kind": "purchase_invoice",
                "status": "ok",
                "file_ref": "/o/gone.jpg",
                "original_name": "gone.jpg",
            },
        ]
        with self.assertRaises(freeze.FreezeError) as ctx:
            freeze.build_manifest(
                work_order=_wo(),
                items=items,
                events=[],
                deliverable_version=1,
                ocr_models=[],
                approver="user:77",
                frozen_at="t",
                sha256_of=_fake_hash,  # /o/gone.jpg 不在表 → None → 点名
            )
        self.assertEqual(ctx.exception.code, "workorder.freeze_source_missing")
        self.assertEqual(ctx.exception.missing, ["gone.jpg"])

    def test_original_name_falls_back_to_embedded_name_when_column_empty(self):
        # 存量行 original_name 空 → 回落落盘名反解 {uuid}__原名。
        items = [
            {
                "id": "a",
                "kind": "purchase_invoice",
                "status": "ok",
                "file_ref": "/o/deadbeef__receipt.jpg",
                "original_name": None,
            }
        ]
        m = freeze.build_manifest(
            work_order=_wo(),
            items=items,
            events=[],
            deliverable_version=1,
            ocr_models=[],
            approver="x",
            frozen_at="t",
            sha256_of=lambda fr: "zzz",
        )
        self.assertEqual(m["items"][0]["file_name"], "receipt.jpg")


class ManifestSerializationTests(unittest.TestCase):
    """R1 回归:带裁决(datetime 事件行)的 manifest 必须能走 dumps_manifest 全 JSON 序列化。"""

    def _manifest_with_decisions(self):
        items = [
            {
                "id": "a",
                "kind": "purchase_invoice",
                "status": "ok",
                "file_ref": "/o/a.jpg",
                "original_name": "a.jpg",
            }
        ]
        events = [
            _classified("a", "purchase_invoice"),
            _decision(5, "a", "face_value", values={"vat": "70.00"}),
        ]
        return freeze.build_manifest(
            work_order=_wo(),
            items=items,
            events=events,
            deliverable_version=1,
            ocr_models=[],
            approver="user:77",
            frozen_at="2026-07-11T00:00:00+00:00",
            sha256_of=_fake_hash,
        )

    def test_manifest_with_datetime_decision_rows_serializes_and_round_trips(self):
        # R1 打回的原始崩溃路径:decisions 非空 + at 来自 datetime 行 → dumps 必须成功。
        text = freeze.dumps_manifest(self._manifest_with_decisions())
        back = json.loads(text)
        self.assertEqual(back["decisions"]["a"]["at"], "2026-07-11T00:00:00+00:00")
        self.assertEqual(back["decisions"]["a"]["decision"], "face_value")

    def test_default_handles_stray_datetime_and_decimal(self):
        # 兜底层:汇编没规整到的 datetime/Decimal(如将来新字段)也确定性转换,不炸不失真。
        m = self._manifest_with_decisions()
        m["decisions"]["a"]["values"]["recalc_vat"] = Decimal("35.00")
        m["decisions"]["a"]["seen_at"] = _DECIDED_AT
        back = json.loads(freeze.dumps_manifest(m))
        self.assertEqual(back["decisions"]["a"]["values"]["recalc_vat"], "35.00")  # 无损十进制串
        self.assertEqual(back["decisions"]["a"]["seen_at"], "2026-07-11T00:00:00+00:00")

    def test_unknown_type_fails_loud_not_silently_stringified(self):
        # 冻结包是审计原件:未知类型必须 fail-loud,不许静默 str() 把 bug 埋进不可变文件。
        m = self._manifest_with_decisions()
        m["decisions"]["a"]["values"]["weird"] = object()
        with self.assertRaises(TypeError):
            freeze.dumps_manifest(m)


if __name__ == "__main__":
    unittest.main()
