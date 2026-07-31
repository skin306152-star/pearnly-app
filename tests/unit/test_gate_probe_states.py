#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_gate_probe_states.py

启动探针失败的分档表(/ai 与 /dms 共一份口径)+ 故障态文案四语齐全。

出身(2026-07-30 走查 · 缺陷4):两个壳的 boot().catch 都只分 401 与「无 status」,
5xx 掉进「闸关」分支,已受邀的用户在服务器抖一下时被告知「为邀请制,请联系 Pearnly
团队开通访问权限」——临时故障被说成永久的权限判定。

本闸钉两件机械可判的:
  1. classifyBootFailure 的分档:401=expired / 403·404·其余4xx=denied /
     5xx·408·429=unavailable / 无 status=offline,两个壳逐条一致(有一处漂就是
     「两个壳两个说法」)。
  2. 故障态那 5 条词条在两个壳的 4 份词典里都在、都非空、且真翻过(zh≠th≠en≠ja)——
     /dms 那套词典没有任何引用闸看着,漏一语就是静默回落中文。

真浏览器那一层(逐个状态码 fulfill、断言落到哪张卡、中泰截图)在
tests/e2e/_gate_probe_honesty_local.spec.js。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import PROJECT_ROOT, _run_node

AI_DIR = PROJECT_ROOT / "static" / "ai"
DMS_DIR = PROJECT_ROOT / "static" / "dms"

# (探针拒绝值, 该落哪一档)。err 形状按两个 api 薄层的真拒绝值:HTTP 错带 status,
# fetch 自身 reject(断网)什么都不带。
_CASES = (
    ({"status": 401}, "expired"),
    ({"status": 403}, "denied"),
    ({"status": 404}, "denied"),
    ({"status": 400}, "denied"),
    ({"status": 422}, "denied"),
    ({"status": 408}, "unavailable"),
    ({"status": 429}, "unavailable"),
    ({"status": 500}, "unavailable"),
    ({"status": 502}, "unavailable"),
    ({"status": 503}, "unavailable"),
    ({"status": 504}, "unavailable"),
    ({}, "offline"),
    (None, "offline"),
)

_DOWN_KEYS = (
    "gate_down_title",
    "gate_down_body",
    "gate_offline_title",
    "gate_offline_body",
    "gate_retry_btn",
)

_LANGS = ("zh", "th", "en", "ja")

_SHELLS = {
    "ai": {
        "gate": AI_DIR / "ai-gate.js",
        "dicts": {lang: AI_DIR / f"ai-i18n-{lang}.js" for lang in _LANGS},
        "global": "__AI_I18N_{}__",
    },
    "dms": {
        "gate": DMS_DIR / "dms-gate.js",
        "dicts": {lang: DMS_DIR / f"dms-i18n-{lang}.js" for lang in _LANGS},
        "global": "__DMS_I18N_{}__",
    },
}


def _classify(shell: str) -> list[str]:
    gate = _SHELLS[shell]["gate"]
    cases = json.dumps([c[0] for c in _CASES])
    return _run_node(f"""
        global.window = global;
        global.self = global;
        const gate = require({str(gate)!r});
        process.stdout.write(JSON.stringify({cases}.map(gate.classifyBootFailure)));
    """)


def _dicts(shell: str) -> dict:
    spec = _SHELLS[shell]
    loads = "".join(f"require({str(spec['dicts'][lang])!r});" for lang in _LANGS)
    reads = ",".join(f"{lang}: window[{spec['global'].format(lang.upper())!r}]" for lang in _LANGS)
    return _run_node(f"""
        global.window = global;
        {loads}
        process.stdout.write(JSON.stringify({{{reads}}}));
    """)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数装载")
class ClassifyBootFailureTests(unittest.TestCase):
    def test_status_lands_in_the_documented_bucket(self):
        for shell in _SHELLS:
            got = _classify(shell)
            for (err, want), actual in zip(_CASES, got):
                self.assertEqual(actual, want, f"/{shell} err={err} 落错档")

    def test_both_shells_agree(self):
        self.assertEqual(_classify("ai"), _classify("dms"), "两个壳的分档表漂了")

    # 反证:判据本身得分得开——若表里 5xx 与 4xx 落同一档,上面两条就退化成恒真。
    def test_table_separates_server_error_from_permission(self):
        buckets = {want for err, want in _CASES}
        self.assertEqual(buckets, {"expired", "denied", "unavailable", "offline"})


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过词典装载")
class DownCopyI18nTests(unittest.TestCase):
    def test_every_shell_has_all_four_languages(self):
        for shell in _SHELLS:
            dicts = _dicts(shell)
            for key in _DOWN_KEYS:
                for lang in _LANGS:
                    text = dicts[lang].get(key)
                    self.assertTrue(
                        isinstance(text, str) and text.strip(),
                        f"/{shell} 的 {lang} 词典缺 {key}(缺了就静默回落中文)",
                    )

    def test_translations_are_real_not_copies(self):
        for shell in _SHELLS:
            dicts = _dicts(shell)
            for key in _DOWN_KEYS:
                texts = [dicts[lang][key] for lang in _LANGS]
                self.assertEqual(len(set(texts)), len(texts), f"/{shell} 的 {key} 有两语同串")

    # 这一屏存在的理由就是这句话:说清不是权限问题。丢了它就退回「你没被邀请」。
    def test_body_says_it_is_not_a_permission_problem(self):
        for shell in _SHELLS:
            dicts = _dicts(shell)
            self.assertIn("不是你的权限", dicts["zh"]["gate_down_body"])
            self.assertIn("ไม่ใช่ปัญหาเรื่องสิทธิ์", dicts["th"]["gate_down_body"])


if __name__ == "__main__":
    unittest.main()
