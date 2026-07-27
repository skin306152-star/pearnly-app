#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ui_copy_register.py

用户可见文案的语域闸(Zihao 2026-07-27 拍板 · 反面教材是产品里真实存在的句子)。

管的是「谁都能机械判定」的那一半:内部黑话上屏、泰文语气助词混用、装饰性 emoji。
判断题(句子够不够短、动词开不开头)机械闸判不了,靠 review;但黑话这一类以前每批都
往回漂,靠自觉挡不住 —— 前后端有两份副本时尤其(copy_file._NOTE_NEEDS_MODEL 与
stw_att_needs_model 是同一句,改一处另一处照旧说「模型」)。

扫的是【值】不是注释:注释里讲「为什么不能说模型」是对的,写进用户看的串才是缺陷。
"""

from __future__ import annotations

import re
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

# (正则, 为什么不许上屏, 该写成什么)。lookbehind/lookahead 用来放行确实存在的正当搭配。
_BANNED = (
    (r"模型", "会计不关心过没过模型,只关心要不要花钱", "OCR"),
    # 「缺料 / 收料 / 资料」是行业说法,单说「料」是我们的内部行话。
    (r"(?<![缺收材资进原])料(?![口])", "「料」是内部行话", "文件 / 资料"),
    (r"载荷", "工程词", "票面数据"),
    (r"回执卡", "内部构件名", "直接说卡上有什么"),
    (r"派活", "内部调度词", "下单 / 执行"),
    (r"工单态", "内部状态机词", "工单状态"),
    (r"幂等", "工程术语", "不会重复执行"),
    (r"后端", "会计不分前后端", "服务"),
    # 「集成 · ERP 桥」是主站真实菜单名,引用它是对的;单说「桥」会计不知道那是什么。
    (r"(?<!ERP )桥", "「桥」是内部叫法", "Express / 小助手"),
    # Tax Agent 是泰国税务代理的正式名称,不是我们的 Agent。
    (r"(?<!Tax )Agent", "内部架构词", "步骤 / 助手"),
    (r"escalate", "内部流程词", "转人工"),
    (r"闸", "内部机制词", "限制 / 上限"),
    (r"โมเดล", "同「模型」", "OCR"),
    (r"สะพาน(?! ERP)", "同「桥」", "Express / ตัวช่วย"),
    (r"หลังบ้าน", "同「后端」", "ระบบ"),
    # 语气助词:同一组词条一半带一半不带,读起来像两个人写的(FlowAccount / PEAK 的
    # UI 串一律不带)。留不留是判断题,混用是确定缺陷 —— 全站统一不带。
    (r"ค่ะ|คะ(?!แนน)", "泰文语气助词", "去掉"),
    (r"⚠", "装饰性 emoji 撑不起警告", "把「不要重推」写进句子"),
)

_RULES = tuple((re.compile(p), why, better) for p, why, better in _BANNED)

# 只读 zh / th:这两语是本次拍板的范围(/ai 的 en/ja 由 at() 回落 zh 或另行维护)。
_SHARDS = (
    "ai-i18n-zh.js",
    "ai-i18n-zh-2.js",
    "ai-i18n-th.js",
    "ai-i18n-th-2.js",
    "ai-i18n-steward.js",
    "ai-i18n-empty.js",
    "ai-i18n-fail.js",
    "ai-i18n-blocked.js",
    "ai-i18n-board.js",
    "ai-i18n-bank-sales.js",
    "ai-i18n-machine-actions.js",
)

# 超管专用词条:只有我们自己看,内部词在这里是准确而非黑话(同 check_i18n 跳过 adm-*)。
_ADMIN_PREFIXES = ("adm_", "sts_")

# 会计发给【她的客户】的催件正文,不是界面串 —— 泰文商务信函去掉 ค่ะ 会读成命令句。
# 语气助词禁令管的是 UI(按钮/标签/错误),不管对外信函。
_OUTBOUND_KEYS = frozenset({"brx_pool_note_tpl"})


def _violations(where: str, text: str) -> list[str]:
    out = []
    for rule, why, better in _RULES:
        hit = rule.search(text or "")
        if hit:
            out.append(f"{where}: 「{hit.group(0)}」—— {why},改用「{better}」· 原文:{text}")
    return out


def _walk(value, where: str) -> list[str]:
    if isinstance(value, str):
        return _violations(where, value)
    if isinstance(value, dict):
        return [m for k, v in value.items() for m in _walk(v, f"{where}[{k!r}]")]
    if isinstance(value, (list, tuple)):
        return [m for i, v in enumerate(value) for m in _walk(v, f"{where}[{i}]")]
    return []


class StewardCopyRegisterTests(unittest.TestCase):
    """后端文案层(services/steward/copy*.py)· 模块级容器里的每一个串。"""

    def _modules(self):
        from services.steward import (
            copy,
            copy_artifacts,
            copy_brief,
            copy_calc,
            copy_close,
            copy_erp_push,
            copy_file,
            copy_loop,
            copy_period,
        )

        return (
            copy,
            copy_artifacts,
            copy_brief,
            copy_calc,
            copy_close,
            copy_erp_push,
            copy_file,
            copy_loop,
            copy_period,
        )

    def test_no_internal_jargon_reaches_the_accountant(self):
        bad = []
        for module in self._modules():
            for name, value in vars(module).items():
                if name.startswith("__") or not isinstance(value, (dict, list, tuple, str)):
                    continue
                bad += _walk(value, f"{module.__name__}.{name}")
        self.assertEqual(bad, [], "用户可见文案里出现了内部黑话:\n" + "\n".join(bad))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过词典扫描")
class DictionaryRegisterTests(unittest.TestCase):
    """前端词典分片(zh + th)· 跑真 node 装载,扫的是产物不是源文件正则。"""

    def _dicts(self):
        requires = "".join(f"require({str(AI_DIR / name)!r});" for name in _SHARDS)
        return _run_node(f"""
            global.window = global;
            global.__AI_I18N_ZH__ = {{}};
            global.__AI_I18N_TH__ = {{}};
            global.__AI_I18N_EN__ = {{}};
            global.__AI_I18N_JA__ = {{}};
            {requires}
            process.stdout.write(JSON.stringify({{
                zh: global.__AI_I18N_ZH__, th: global.__AI_I18N_TH__,
            }}));
            """)

    def test_no_internal_jargon_in_zh_and_th_dictionaries(self):
        dicts = self._dicts()
        bad = []
        for lang, table in dicts.items():
            for key, text in table.items():
                if key.startswith(_ADMIN_PREFIXES) or key in _OUTBOUND_KEYS:
                    continue
                bad += _walk(text, f"{lang}.{key}")
        self.assertEqual(bad, [], "词典里出现了内部黑话:\n" + "\n".join(bad))

    def test_zh_and_th_cover_the_same_keys(self):
        """两语 key 集合一致 —— 缺一边的那条会在泰文界面上印出原始 key。"""
        dicts = self._dicts()
        zh, th = set(dicts["zh"]), set(dicts["th"])
        self.assertEqual(sorted(zh - th), [], "th 缺这些 key")
        self.assertEqual(sorted(th - zh), [], "zh 缺这些 key")


if __name__ == "__main__":
    unittest.main()
