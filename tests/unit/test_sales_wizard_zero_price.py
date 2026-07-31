#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-1 · 开票向导那一侧:"没设价"不许在任何一环变成 ฿0。

真点真开的那条链在 scripts/_wizard_zero_price_verify.cjs(真 Chromium · 判据是点完之后网络上
有没有 /issue)。这里补的是那条链照不到的两样:
  · 纯判据本身(priced/compliance/lineAmount)在真 node 里跑源码,不是照着实现抄一遍断言;
  · 四语文案齐不齐、dist 有没有跟着提交 —— 这两样浏览器验收里看不出来,而漏了就是线上白屏
    (t() 回 key)或"改了没生效"。

会出事的输入:null 价、空串价、显式 0(赠品·必须与前两者分开)、"abc"(数字框粘进非数)。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from tests.unit._node_harness import PROJECT_ROOT, _run_node

CALC_TS = PROJECT_ROOT / "src" / "home" / "sales-wizard-calc.ts"

# 判据在 TS 里,node 跑不了 TS —— 用 esbuild 现转一份(与产品同一份源码,不是抄写)。
import json  # noqa: E402  (仅为下方 json.dumps 转义路径)

_PRELUDE = """
const esbuild = require('esbuild');
const fs = require('fs');
const src = fs.readFileSync(%s, 'utf8');
const { code } = esbuild.transformSync(src, { loader: 'ts', format: 'cjs' });
const mod = { exports: {} };
new Function('module', 'exports', 'require', code)(mod, mod.exports, () => ({}));
const CALC = mod.exports;
const out = (o) => process.stdout.write(JSON.stringify(o));
""" % json.dumps(str(CALC_TS))


def _run(body: str) -> dict:
    return _run_node(_PRELUDE + body)


def _read(*parts: str) -> str:
    return Path(PROJECT_ROOT, *parts).read_text(encoding="utf-8")


def _dict_value(src: str, key: str):
    """字典里 key 的字面量值。

    不按行锚定:prettier 会把长文案折成 `key:` 换行再接 '…',行锚定的正则那时读不到值,
    而"读不到"在断言里长得跟"这门语言没翻"一模一样 —— 判据会因为排版变化而误报。
    """
    m = re.search(rf"\b{key}:\s*'((?:[^'\\]|\\.)*)'", src)
    return m.group(1) if m else None


class PricedTellsUnsetFromFreeTests(unittest.TestCase):
    """口径与收银台 pos-cashier.priced 同一份:空 = 没定过,0 = 定了(免费)。"""

    @classmethod
    def setUpClass(cls):
        cls.res = _run(
            "out({ cases: [null, undefined, '', '  ', 0, '0', 120, '120', 'abc', NaN]"
            ".map((v) => CALC.priced(v)) });"
        )

    def test_nothing_typed_is_not_a_price(self):
        # null / undefined / '' / '   '
        self.assertEqual(self.res["cases"][:4], [False, False, False, False])

    def test_an_explicit_zero_is_a_price(self):
        """赠品是老板拍板的价,票面上写着 ฿0 谁都看得见 —— 不许跟"忘了填"混成一个值。"""
        self.assertEqual(self.res["cases"][4:6], [True, True])

    def test_a_real_number_is_a_price(self):
        self.assertEqual(self.res["cases"][6:8], [True, True])

    def test_garbage_is_not_a_price(self):
        """数字框粘进非数时浏览器给的就是空串或原文,别当成 0 发出去。"""
        self.assertEqual(self.res["cases"][8:], [False, False])


class ComplianceBlocksUnpricedLinesTests(unittest.TestCase):
    """第 5 步的合规清单是"开出"那一下的守门(doIssue 直接读它)。"""

    @classmethod
    def setUpClass(cls):
        cls.res = _run("""
        const base = {
            docType: 'tax_invoice_receipt', sellerIdx: 0,
            buyer: { type: 'individual', name: 'ก', addr: 'ข', tin: '1234567890123',
                     branchType: 'hq', branchNo: '' },
            hdisc: 0, vatRate: 7, whtRate: 0,
            pay: { status: 'paid', method: 'cash', date: '2026-07-30', paidAmt: null },
            issueDate: '2026-07-30', dueDate: '', be: false,
            paper: 'a4', docLang: 'th_en', layout: 'single',
        };
        const ck = (lines) => {
            const c = CALC.compliance(Object.assign({}, base, { lines }));
            const p = c.find((x) => x.key === 'ckPrice');
            return { pass: p.pass, req: p.req, na: p.na };
        };
        const L = (desc, price) => ({ desc, qty: 1, price, disc: 0, vat: true });
        out({
            blank: ck([L('นม', '')]),
            nul: ck([L('นม', null)]),
            gift: ck([L('ของแถม', 0)]),
            mixed: ck([L('โค้ก', 120), L('นม', '')]),
            giftPlusPaid: ck([L('โค้ก', 120), L('ของแถม', 0)]),
            priced: ck([L('โค้ก', 120)]),
            // 没写品名的行不上票(buildPayload 过滤它),不该因为它拦住整张单
            draftRow: ck([L('โค้ก', 120), L('', '')]),
            // 一整行 0 元的整单:合计 0,前端放行、后端零额闸兜(两道闸各管一头)
            allFree: ck([L('ของแถม', 0)]),
        });
        """)

    def test_a_blank_price_blocks_issuing(self):
        self.assertFalse(self.res["blank"]["pass"])
        self.assertTrue(self.res["blank"]["req"], "这条不是必过项 = 挡不住任何人")
        self.assertFalse(self.res["blank"]["na"])

    def test_a_null_price_blocks_issuing(self):
        self.assertFalse(self.res["nul"]["pass"])

    def test_one_unpriced_line_among_priced_ones_still_blocks(self):
        """整单合计 >0(120 那行撑着),后端零额闸看不出问题 —— 只有这一条拦得住。"""
        self.assertFalse(self.res["mixed"]["pass"])

    def test_an_explicit_gift_line_does_not_block(self):
        self.assertTrue(self.res["gift"]["pass"])
        self.assertTrue(self.res["giftPlusPaid"]["pass"])

    def test_priced_lines_pass(self):
        self.assertTrue(self.res["priced"]["pass"])

    def test_a_half_typed_row_does_not_block(self):
        """还没写品名的那行不会印上票,拿它拦住整张单 = 用户找不到该改哪。"""
        self.assertTrue(self.res["draftRow"]["pass"])


class LineAmountIsOneImplementationTests(unittest.TestCase):
    """合计 / 购物车 / 票面预览三处的行金额必须是同一份算法。"""

    def test_null_and_blank_contribute_nothing_instead_of_crashing(self):
        res = _run("""
        const L = (qty, price, disc) => ({ desc: 'x', qty, price, disc, vat: true });
        out({
            nul: CALC.lineAmount(L(2, null, 0)),
            blank: CALC.lineAmount(L(2, '', 0)),
            gift: CALC.lineAmount(L(2, 0, 0)),
            normal: CALC.lineAmount(L(2, '120', 20)),
            neverNegative: CALC.lineAmount(L(1, '50', '80')),
        });
        """)
        self.assertEqual(res["nul"], 0)
        self.assertEqual(res["blank"], 0)
        self.assertEqual(res["gift"], 0)
        self.assertEqual(res["normal"], 220)
        self.assertEqual(res["neverNegative"], 0)

    def test_the_three_render_sites_all_call_it(self):
        """手抄一份就会漂:购物车画 ฿0.00 而合计按 null 算,两个数字对不上没人看得出。"""
        for mod in ("sales-wizard-steps", "sales-wizard-preview"):
            with self.subTest(module=mod):
                self.assertIn("lineAmount(", _read("src", "home", f"{mod}.ts"))


class FourLanguagesTests(unittest.TestCase):
    """漏一门语言 = 那门语言下 t() 回键名,屏上直接显示 "noPrice"。"""

    KEYS = ("noPrice", "noPriceHint", "ckPrice", "ckPriceD")

    def test_every_new_key_exists_in_all_four_dicts(self):
        # zh/en 在 sales-wizard-i18n.ts,th/ja 在 sales-wizard-i18n-langs.ts(拆文件守行数闸)
        src = _read("src", "home", "sales-wizard-i18n.ts") + _read(
            "src", "home", "sales-wizard-i18n-langs.ts"
        )
        for key in self.KEYS:
            with self.subTest(key=key):
                hits = len(re.findall(rf"^\s+{key}:", src, re.M))
                self.assertEqual(hits, 4, f"{key} 只有 {hits} 门语言(要 4 门)")

    def test_thai_and_japanese_are_really_translated_not_copies(self):
        """占位式"补齐"(四份都填中文)键数是齐的,店里是坏的。

        两次踩同一个坑,记在这:
        1. "值里有没有汉字" —— 日文本来就用汉字(単価/明細/無償),按码位查把真译文判成没译。
        2. 改成"日文必须含假名" —— 短标签本来就可以全汉字(価格未設定,同 dict 里既有的
           非課税 也是),照样冤枉真译文。
        机械分得清的只有两样:泰文有自己独占的字符段(U+0E00–U+0E7F),以及"不许跟中文逐字
        相同"。日文与中文用码位分不开,就别假装分得开 —— 只查后一条,并把这个限度写在这里,
        免得下一个人再发明第三种查法。
        """
        langs = _read("src", "home", "sales-wizard-i18n-langs.ts")
        zh = _read("src", "home", "sales-wizard-i18n.ts")
        cut = langs.index("export const JA")
        dicts = {"th": langs[:cut], "ja": langs[cut:]}
        thai = re.compile(r"[฀-๿]")
        for key in self.KEYS:
            zh_val = _dict_value(zh, key)
            for lang, src in dicts.items():
                val = _dict_value(src, key)
                with self.subTest(key=key, lang=lang):
                    self.assertIsNotNone(val, f"{lang} 里没有 {key}")
                    self.assertNotEqual(val, zh_val, f"{key} 的 {lang} 是中文原样复制")
                    if lang == "th":
                        self.assertRegex(val, thai, f"{key} 的泰文译文里没有泰文")


class BuiltBundleTests(unittest.TestCase):
    """改 src/** 必须把 dist 一起提交(prod 不重建 dist)。"""

    def test_main_bundle_carries_the_zero_price_gate(self):
        dist = _read("static", "dist", "main.js")
        for marker in ("sw-noprice", "ckPriceD", "noPriceHint"):
            with self.subTest(marker=marker):
                self.assertIn(marker, dist, f"{marker} 没进 dist/main.js")

    def test_stylesheet_carries_the_noprice_styling(self):
        """类名进了 JS、样式没进 CSS = 屏上跟正常价一个色,等于没提示。"""
        self.assertIn(".sw-noprice", _read("static", "dist", "home.css"))


if __name__ == "__main__":
    unittest.main()
