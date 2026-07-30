#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_verify_script_i18n_injection_gate.py

「验收脚本别拿自带副本盖掉真词典」的机械闸。

反面教材是真事(2026-07-30 三路审查):
  · scripts/_products_barcode_ui_verify.cjs 自带一份中文 COPY,开跑前
    `Object.keys(window.I18N).forEach(l => Object.assign(window.I18N[l], copy))`
    无条件写进全部四种语言,再拿同一份 copy 当期望值 —— 拿自己比自己,漏译天然照不出;
    它出的截图 07-scanned-filled.png 就是泰文界面配中文条码提示,而脚本全绿。
  · scripts/_pos_scan_smoke.cjs 留着一段 PENDING_TH 注入,注释写「这几个键还没进
    pos-i18n.js」—— 键早就四语落地了,注入等于用脚本里的旧副本盖掉真值,断言自我循环。

判据只认「写进页面词典」这一件事,不一刀切禁止读词典(读是对的,期望值就该现场从真词典取):

  A. 部分合并 —— `Object.assign(window.I18N…)`、`window.I18N[lang] = {…}`、
     `window.I18N[lang][key] = …`、以及点号写法 `window.I18N.th = COPY` /
     `window.POS_I18N.th.done = …`:永远红。这是上面两处假绿的形状。
     (2026-07-31 补:上一版只认中括号,而点号是更自然的写法 —— 三种点号写法一律漏网,
     闸半开着还报绿。)
  B. 整份替换 —— `window.I18N = X`:只有脚本自己 require 了真词典源文件
     (static/i18n-data.js / static/pos/pos-i18n.js)时放行。那是把真词典整份搬进
     一张合成页(_rcx_test.cjs 的 harness 就这么干),值仍然是真的;没 require 就是
     自带副本冒充词典,红。

外加一条同源假绿:语言键写错。主 SPA 与 POS 的真键都是 mrpilot_lang,写成 'lang' 的话
语言压根没切,后面每条文案断言都在对着默认语言比,却照样绿。只在脚本真的读了页面词典
时才红 —— 不读词典的脚本(scripts/_stock_guard_ui_verify.cjs 就有这么一行)那行是死代码,
拦它是误伤,而闸一旦开始误报就会被人 skip 掉,还不如不装。

扫 scripts/_*.cjs 全部(含未跟踪的):这批脚本正是「还没提交就已经在自欺」的高发区,
拦在提交前才有意义。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# 本轮三个扫码验收脚本:闸对它们必须有射程,名字写死在这儿,改名了这条自检会红。
BARCODE_SCRIPTS = (
    "_products_barcode_ui_verify.cjs",
    "_pos_scan_smoke.cjs",
    "_inv_scan_smoke.cjs",
)

# 整行注释不算代码:这几个脚本的文件头就在讲「旧版怎么注入的」,按字面扫会把说明当赃物。
# 只剥整行,不碰行内(行内切 // 会把 'http://127.0.0.1' 一起切没)。
_COMMENT_LINE = re.compile(r"^\s*(//|/\*|\*)")

_DICT = r"(?:I18N|POS_I18N)"

# 一层取用:中括号 或 点号。上一版只认中括号 —— 而点号(window.I18N.th = COPY /
# window.POS_I18N.th.done = '…')是更自然的写法,一律漏网,闸等于半开着。
_ACCESS = r"(?:\[[^\]]*\]|\.[A-Za-z_$][\w$]*)"
# 赋值:普通 = 与 ||= &&= ??=。`=(?!=)` 把 == / === / != / >= 全挡在外面(那些是读)。
_ASSIGN = r"(?:\|\||&&|\?\?)?=(?!=)"

# A · 部分合并:Object.assign 打进词典,或直接写某个语言槽 / 某个键。
_MERGE_INTO_DICT = re.compile(rf"Object\.assign\(\s*(?:window\.)?{_DICT}\b")
_SLOT_WRITE = re.compile(
    rf"(?:^|[^\w.$])(?:window\.)?{_DICT}\s*(?:{_ACCESS}\s*){{1,3}}{_ASSIGN}", re.MULTILINE
)

# B · 整份替换。只认带 window. 前缀的写法:`const I18N = {...}` 是脚本自己的局部常量,
# 没进页面就不构成注入(拿硬编码期望值比对是脆,但不会把漏译照绿)。
_WHOLE_DICT_WRITE = re.compile(rf"window\.{_DICT}\s*=(?!=)")
_REAL_DICT_SOURCE = re.compile(r"static[/\\]i18n-data\.js|static[/\\]pos[/\\]pos-i18n\.js")

# C · 语言键。真键是 mrpilot_lang;'lang' 这个键页面根本不读。
_BAD_LANG_KEY = re.compile(r"setItem\(\s*['\"]lang['\"]")
# 「这脚本靠页面词典下断言」的证据:读词典本身,或读页面当前语言。
_READS_DICT = re.compile(r"window\.(?:I18N|POS_I18N)|_currentLang|POS\.state\.lang")


def _code(src: str) -> str:
    return "\n".join(line for line in src.splitlines() if not _COMMENT_LINE.match(line))


def offences(src: str) -> list[str]:
    """这份脚本干了哪些「拿自己比自己」的事(空列表 = 干净)。"""
    src = _code(src)
    hits: list[str] = []
    if _MERGE_INTO_DICT.search(src) or _SLOT_WRITE.search(src):
        hits.append("把自带副本合并进页面词典")
    if _WHOLE_DICT_WRITE.search(src) and not _REAL_DICT_SOURCE.search(src):
        hits.append("整份替换页面词典且没 require 真词典源")
    if _BAD_LANG_KEY.search(src) and _READS_DICT.search(src):
        hits.append("语言键写成 'lang'(真键 mrpilot_lang · 语言压根没切)")
    return hits


def _verify_scripts() -> list[tuple[Path, str]]:
    return [(p, p.read_text(encoding="utf-8")) for p in sorted(SCRIPTS_DIR.glob("_*.cjs"))]


class VerifyScriptI18nInjectionGate(unittest.TestCase):
    def setUp(self):
        self.scripts = _verify_scripts()
        # 判据自检:扫不到文件时下面每条断言都会「通过」,绿得毫无意义。
        self.assertGreater(
            len(self.scripts), 20, "scripts/_*.cjs 扫不到脚本 —— 判据失效比断言失败更危险"
        )

    def test_no_verify_script_fakes_its_own_dictionary(self):
        offenders = {p.name: hits for p, src in self.scripts if (hits := offences(src))}
        self.assertEqual(
            offenders,
            {},
            "以下验收脚本在拿自己比自己 —— 期望值必须现场从页面里的真 window.I18N /"
            " window.POS_I18N 取,脚本一个字都不注入;语言键用 mrpilot_lang。\n"
            + "\n".join(f"  {n}: {'、'.join(h)}" for n, h in sorted(offenders.items())),
        )

    def test_three_barcode_scripts_are_in_range(self):
        """闸得真扫到这三个脚本 —— 文件改名/挪窝时这条先红,而不是闸悄悄空转。"""
        names = {p.name for p, _ in self.scripts}
        self.assertEqual(set(BARCODE_SCRIPTS) - names, set(), "本轮扫码验收脚本不在闸的射程里")

    def test_barcode_scripts_take_expectations_from_the_live_dictionary(self):
        """反面:三个脚本里但凡有一个不读页面词典,它的文案断言就只能是自己写的副本。"""
        for name in BARCODE_SCRIPTS:
            src = _code((SCRIPTS_DIR / name).read_text(encoding="utf-8"))
            self.assertRegex(
                src,
                _READS_DICT,
                f"{name} 没从页面词典取期望值 —— 文案断言等于自说自话",
            )

    def test_criteria_fire_on_the_two_historical_shapes(self):
        """正例用真出过事的两段形状,合成的不是稻草人。"""
        products_old = (
            "const COPY = { 'sx-p-bc-hint': '只填条码' };\n"
            "await page.evaluate((copy) => {\n"
            "    Object.keys(window.I18N).forEach((l) => Object.assign(window.I18N[l], copy));\n"
            "}, COPY);"
        )
        self.assertIn("把自带副本合并进页面词典", offences(products_old))

        pos_old = (
            "const PENDING_TH = { 'posui.bscan.done': 'เสร็จ' };\n"
            "await page.addInitScript((d) => {\n"
            "    window.addEventListener('load', () => Object.assign(window.POS_I18N.th, d));\n"
            "}, PENDING_TH);"
        )
        self.assertIn("把自带副本合并进页面词典", offences(pos_old))

        # 换个写法绕过 Object.assign:直接写语言槽 / 写单个键,一样得认出来
        self.assertIn("把自带副本合并进页面词典", offences("window.I18N['th'] = COPY;"))
        self.assertIn("把自带副本合并进页面词典", offences("window.POS_I18N[l][k] = 'x';"))

    def test_dot_notation_is_caught_too(self):
        """点号是更自然的写法 —— 上一版只认中括号,这三种一律漏网。"""
        dotted = [
            "window.I18N.th = COPY;",
            "window.I18N.th['bscan.notfound'] = '…';",
            "window.POS_I18N.th.done = 'เสร็จ';",
            "window.I18N['th'].done = 'x';",
            # 混进 addInitScript 的形状(真脚本里注入就长这样)
            "await page.addInitScript(() => {\n    window.POS_I18N.th.aim = 'x';\n});",
            # 逐键写:forEach 里一条条塞
            "Object.keys(COPY).forEach((k) => (window.I18N.th[k] = COPY[k]));",
            # 复合赋值一样是写
            "window.I18N.th.done ||= 'x';",
            "window.POS_I18N.th ??= COPY;",
            # 不带 window. 前缀的裸写法
            "I18N.th = COPY;",
        ]
        for src in dotted:
            self.assertIn("把自带副本合并进页面词典", offences(src), f"点号写法漏网:{src}")

    def test_criteria_do_not_catch_reading_the_dictionary(self):
        """反例:读词典、读语言、Object.assign 别的对象,都不该红 —— 误伤一次闸就废了。

        点号判据加进来之后误伤面最大的一片正是「用点号【读】词典」,故这里逐种写法钉住:
        取值、比较、真值判断、回落、解构、当函数实参传。
        """
        clean = [
            "const copy = await page.evaluate((l) => window.I18N[l], lang);",
            "return { lang: window.POS.state.lang, copy: window.POS_I18N[window.POS.state.lang] };",
            "const L = I18N[lang];",
            "window._userInfo = Object.assign(window._userInfo || {}, { plan: 'lifetime' });",
            "api.create = (opts) => orig(Object.assign({}, opts, { onScan: () => {} }));",
            "localStorage.setItem('mrpilot_lang', 'th');",
            # ── 点号读法(本轮新增判据的误伤高发区)──
            "const dict = window.I18N.th;",
            "const want = window.POS_I18N.th['posui.bscan.aim'];",
            "if (window.I18N.th.done === text) return true;",
            "if (!window.POS_I18N.th) throw new Error('no dict');",
            "const s = window.I18N.th.done || key;",
            "const { th } = window.I18N;",
            "expect(window.I18N.th['bscan.notfound']).toContain(code);",
            "await page.evaluate(() => window.POS_I18N.th.aim);",
            "wantMsg = copy.dict['inv-scan-added'].replace('{name}', name);",
            # 同名不同物:别的对象上的 th 槽不是页面词典
            "myCopy.I18N.th = COPY;",
            "state.i18nReady = true;",
        ]
        for src in clean:
            self.assertEqual(offences(src), [], f"误伤了正当写法:{src}")

    def test_whole_dict_transplant_is_only_ok_with_the_real_source(self):
        """整份搬真词典进合成页(_rcx_test.cjs 的 harness)放行,自带一份冒充词典不放行。"""
        transplant = (
            "require(path.join(ROOT, 'static/i18n-data.js'));\n"
            "const I18N = global.window.I18N;\n"
            "const harness = `<script>window.I18N = ${JSON.stringify(I18N)};</script>`;"
        )
        self.assertEqual(offences(transplant), [], "把真词典搬进合成页被误判成注入")
        self.assertIn(
            "整份替换页面词典且没 require 真词典源",
            offences("window.I18N = { th: { 'k': 'v' } };"),
        )

    def test_bad_lang_key_only_fires_when_copy_is_asserted(self):
        """语言键判据的正反例:读词典的脚本写错键 = 假绿;不读词典的那行是死代码。"""
        asserts_copy = (
            "localStorage.setItem('lang', 'zh');\n"
            "const copy = await page.evaluate((l) => window.I18N[l], lang);"
        )
        self.assertIn("语言键写成 'lang'(真键 mrpilot_lang · 语言压根没切)", offences(asserts_copy))
        self.assertEqual(
            offences("localStorage.setItem('lang', 'th');\nawait page.click('#erp-logs');"),
            [],
            "不读词典的脚本被这条判据误伤",
        )

    def test_comment_lines_are_not_evidence(self):
        """文件头讲「旧版怎么注入的」不算注入 —— 三个脚本的头注释里就写着这段历史。"""
        self.assertEqual(
            offences("// 旧版 Object.assign(window.I18N[l], copy) 无条件盖四种语言"),
            [],
            "把说明历史的注释当成了赃物",
        )


if __name__ == "__main__":
    unittest.main()
