#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_home_list_error_states.py

机械闸:src/home/** 里,catch 块把列表状态清成 `[]` 却不留任何失败痕迹 → 红。

为什么值得一道闸:后端 500 被渲染成空态,是本仓三个月里犯了三次的同一个错
(识别记录 → 对账中心「最近对账」→ 客户管理「买方客户」)。根因每次都一样 ——
失败路径把列表清成 `[]`,渲染层只剩「长度 0」这一个信号,于是照空态渲染成
「还没有…」。用户读到的是「我的数据没了」,于是去查数据而不是重试。

判据(刻意窄,宁可漏不可误报):
  命中 = catch 块里有 `<已有标识符> = []`,且整个 catch 块里找不到任何失败痕迹。
  失败痕迹 = showToast/showAlert/throw/listErrorHtml/posErrMsg/pu-error/
             或给带 Err/Error/Failed/offline 字样的变量赋一个非空值。
  不命中 = catch 里新声明的局部空数组(const ids: string[] = [])—— 那不是把
           已有列表清空。

刻意没做的那半边:「不看 resp.ok 就把响应体当正常载荷解」同样是这个病,但
本仓有两套合法的成功契约(HTTP 状态码 vs `{ok, data, error}` 信封),诚实的
检查可能落在任一边。实测:裸判「函数里没提过 resp.ok」= 27 处命中,其中 24
处是信封校验(env.ok !== true),纯误报;加信封豁免后剩 7 处,里面仍有 4 处
需要逐个读渲染层才判得出真假。做不到既准又不误报,故不在本闸里断,把测量结
果写在这段注释里交下一轮,不给一道会被 `# noqa` 掉的假闸。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src" / "home"

# 已登记的例外:key = "<仓库相对路径>::<被清空的标识符>",value = 为什么这处不算不诚实。
# 登记表自己也要保鲜:登记了却已经不再命中的条目照样判红(防它烂成免死金牌)。
ALLOW: dict[str, str] = {
    "src/home/expense-data.ts::rules": (
        "识别关键词规则是灰度功能,拉不到时同一段把 kwEnabled 一起置 false → 整块关键词 UI "
        "不渲染,用户看不到一张骗人的空清单;主页面(费用小类树)是另一次请求,不受影响。"
    ),
    "src/home/pos-audit.ts::cashiers": (
        "收银员下拉是筛选器的选项源,不是数据清单:拉不到时筛选器少几个选项,页面主体"
        "(异常汇总)自己有 errCode 错误态兜着,不会把 500 说成「这个店没有异常」。"
    ),
    "src/home/pos-sales-log.ts::cashiers": (
        "同 pos-audit:筛选器选项源。销售流水主体在 fetchPage 里走 posErrMsg 错误态。"
    ),
}

_CATCH = re.compile(r"\bcatch\b\s*(?:\([^)]*\)\s*)?\{")
# 赋值给一个已存在的标识符(含 S.clients / obj.list 这类成员)
_EMPTY_ASSIGN = re.compile(r"(?<![\w.$])([\w.$]+)\s*=\s*\[\]\s*;")
_DECLARE = re.compile(r"\b(?:const|let|var)\s+[\w{[]")
# 失败位那条:否定前瞻必须自己吃掉空白,否则 `\s*=\s*` 会回退成 0 个空格,
# 前瞻看到的是空格而不是 false —— 赋 false 也当成留痕(踩过,见 test_gate_catches_falsy_flag)。
_TRACE = re.compile(
    r"showToast\(|showAlert\(|listErrorHtml\(|posErrMsg\(|pu-error|\bthrow\b|"
    r"\w*(?:Err|Error|Failed|failed|offline)\s*=(?!\s*(?:''|\"\"|null|false|\[\]|0\b))"
)


def _catch_bodies(src: str) -> list[tuple[int, str]]:
    """(catch 起始行号, catch 块正文)。花括号配平取块,不用固定行窗口。"""
    out: list[tuple[int, str]] = []
    for m in _CATCH.finditer(src):
        open_at = src.index("{", m.start())
        depth = 0
        for j in range(open_at, len(src)):
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    out.append((src.count("\n", 0, m.start()) + 1, src[open_at + 1 : j]))
                    break
    return out


def scan_source(rel_path: str, src: str) -> list[tuple[str, int, str]]:
    """返回 [(key, 行号, 被清空的标识符)]。key 用于查登记表。"""
    found: list[tuple[str, int, str]] = []
    for line, body in _catch_bodies(src):
        if _TRACE.search(body):
            continue
        for m in _EMPTY_ASSIGN.finditer(body):
            head = body[: m.start()].rsplit("\n", 1)[-1]
            if _DECLARE.search(head):
                continue
            name = m.group(1)
            found.append((f"{rel_path}::{name}", line, name))
    return found


def scan_tree() -> list[tuple[str, int, str]]:
    out: list[tuple[str, int, str]] = []
    for path in sorted(SRC_DIR.rglob("*.ts")) + sorted(SRC_DIR.rglob("*.js")):
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        out += scan_source(rel, path.read_text(encoding="utf-8"))
    return out


# ── 毒/干净样本:闸自己得能被证明有牙,否则「全绿」不算数 ──────────────────
POISON = """
async function loadThings() {
    try {
        const d = await apiClient('/api/things');
        S.things = d.things || [];
    } catch (e) {
        console.error('fail', e);
        S.things = [];
    }
}
"""

CLEAN_FLAG = """
async function loadThings() {
    try {
        S.things = (await apiClient('/api/things')).things || [];
        S.thingsFailed = false;
    } catch (e) {
        S.thingsFailed = true;
        S.things = [];
    }
}
"""

CLEAN_TOAST = """
async function loadThings() {
    try {
        S.things = [];
    } catch (e) {
        showToast(t('load-fail'), 'error');
        S.things = [];
    }
}
"""

CLEAN_LOCAL_DECL = """
async function pick() {
    try {
        return await apiClient('/api/things');
    } catch (e) {
        const ids: string[] = [];
        return ids;
    }
}
"""

CLEAN_RENDER_ERROR = """
async function loadThings() {
    try {
        S.things = (await apiClient('/api/things')).things || [];
    } catch (e) {
        el.innerHTML = listErrorHtml('things-error-title', 'data-things-retry');
        S.things = [];
    }
}
"""

# 失败位被赋成空串/false 不算留痕(那是「清掉上一次的错误」,不是「这次错了」)
POISON_FALSY_FLAG = """
async function loadThings() {
    try {
        S.things = (await apiClient('/api/things')).things || [];
    } catch (e) {
        S.thingsFailed = false;
        S.things = [];
    }
}
"""


class ListErrorStateGate(unittest.TestCase):
    def test_gate_catches_poison(self):
        """毒样本:清空 + 只有 console.error → 必须逮住。"""
        self.assertEqual([h[2] for h in scan_source("x.ts", POISON)], ["S.things"])

    def test_gate_catches_falsy_flag(self):
        """把失败位赋成 false 也是没留痕 —— 不许当护身符。"""
        self.assertEqual([h[2] for h in scan_source("x.ts", POISON_FALSY_FLAG)], ["S.things"])

    def test_gate_passes_clean_samples(self):
        for name, sample in (
            ("失败位", CLEAN_FLAG),
            ("toast", CLEAN_TOAST),
            ("局部声明", CLEAN_LOCAL_DECL),
            ("渲染错误态", CLEAN_RENDER_ERROR),
        ):
            with self.subTest(name):
                self.assertEqual(scan_source("x.ts", sample), [], f"{name} 被误报")

    def test_no_unregistered_offenders(self):
        offenders = [h for h in scan_tree() if h[0] not in ALLOW]
        self.assertEqual(
            offenders,
            [],
            "列表加载失败被渲染成空态(后端 500 会被用户读成「数据没了」)。"
            "修法:置一个失败位 → 渲染层走 src/home/list-error-state.ts 的错误态 + 重试;"
            "确实不算缺陷的写进本文件 ALLOW 并给出理由。命中:%s" % offenders,
        )

    def test_allowlist_is_not_stale(self):
        """登记表保鲜:登记了却已经不命中的条目照样红,防它烂成免死金牌。"""
        live = {h[0] for h in scan_tree()}
        stale = sorted(k for k in ALLOW if k not in live)
        self.assertEqual(stale, [], f"ALLOW 里这些条目已经不再命中,该删:{stale}")

    def test_allowlist_reasons_are_real(self):
        for key, reason in ALLOW.items():
            with self.subTest(key):
                self.assertGreaterEqual(len(reason.strip()), 30, f"{key} 的理由太短")


if __name__ == "__main__":
    unittest.main()
