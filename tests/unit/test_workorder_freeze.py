# -*- coding: utf-8 -*-
"""冻结 manifest 汇编守门(services/workorder/freeze.py · C-2 设计 3/5)。

纯函数 build_manifest:六要素齐(逐 item sha256 + 规则版本 + 模型版本 + 裁决回放 + 签批人 +
时间)。fail-closed:有 file_ref 却算不出哈希 → FreezeError 点名。sha256_of 注入,不碰真盘。
"""

from __future__ import annotations

import unittest

from services.workorder import freeze


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
        "created_at": "2026-07-11T00:00:00Z",
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
        # 4 裁决/豁免回放
        self.assertEqual(m["decisions"]["a"]["decision"], "face_value")
        self.assertEqual(m["decisions"]["a"]["actor"], "user:77")
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


if __name__ == "__main__":
    unittest.main()
