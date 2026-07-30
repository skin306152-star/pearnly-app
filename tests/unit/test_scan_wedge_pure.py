#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_scan_wedge_pure.py

条码枪键盘楔子(static/scan/scan-wedge.js)判定守门。真 node 子进程跑源文件 + 桩 document,
用真 setTimeout(不 mock 计时器)——「间隔超过 150ms 算一串结束」这条判据本身就是时间语义,
把计时器换成假的等于不验它。

钉死六条(错任何一条,店里当场出事):
  1. 字符间隔超 MAX_GAP_MS 才收尾;没超就还在攒同一串。
  2. 短于 MIN_LENGTH 位的丢掉(店员随手碰一下键盘不该当成扫了一件货)。
  3. Enter / Tab 立即收尾并 preventDefault(否则枪的回车把表单顺手提交了)。
  4. 焦点在 input/textarea/contenteditable 上不抢(店员在改数量,截走按键=输入框吞字);
     该元素带 data-enable-barcode 才例外。
  5. data-enable-barcode="gun" 的框只收「枪打的那种串」,人手打的照旧归那个框 ——
     批号/效期这类框走这一档(见 WedgeGunOnlyFieldTests)。
  6. exclusive 订阅者在场时独占(modal 开着,底下页面不该偷偷把货加进购物车)。
"""

from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

from tests.unit._node_harness import PROJECT_ROOT, _run_node

WEDGE = PROJECT_ROOT / "static" / "scan" / "scan-wedge.js"


# 桩 document:只提供楔子真正用到的四样(挂/摘 keydown、建隐藏 input、body)。
# touch = True 时给 globalThis 加一个 ontouchstart 属性 —— 楔子用 `in` 判触屏,
# 值是 undefined 也算存在,这正好模拟安卓而不需要整套 jsdom。
def _prelude(touch: bool = False) -> str:
    return f"""
        const handlers = [];
        const created = [];
        {"global.ontouchstart = undefined;" if touch else ""}
        global.document = {{
            addEventListener: (t, f) => handlers.push(f),
            removeEventListener: (t, f) => {{
                const i = handlers.indexOf(f);
                if (i >= 0) handlers.splice(i, 1);
            }},
            createElement: () => {{
                const el = {{
                    attrs: {{}},
                    style: {{}},
                    value: '',
                    className: '',
                    focused: 0,
                    setAttribute(k, v) {{ this.attrs[k] = v; }},
                    focus() {{ this.focused += 1; }},
                }};
                created.push(el);
                return el;
            }},
            body: {{ appendChild: () => {{}} }},
        }};
        const wedge = require({json.dumps(str(WEDGE))});
        const BODY = {{ tagName: 'BODY' }};
        let prevented = 0;
        function press(key, target) {{
            const el = target || BODY;
            handlers.forEach((h) =>
                h({{
                    key: key,
                    target: el,
                    preventDefault: () => {{ prevented += 1; }},
                }})
            );
            // 浏览器的默认动作在 keydown 处理器【之后】才把字符落进框里。顺序照真的来,
            // 「楔子读到的是扫之前的内容」这条才验得出;颠倒过来快照里就已经带上这一串了。
            if (key.length === 1 && typeof el.accept === 'function') el.accept(key);
        }}
        function type(keys, target) {{ keys.forEach((k) => press(k, target)); }}
        const out = (o) => process.stdout.write(JSON.stringify(o));
        const GAP = wedge.MAX_GAP_MS;
    """


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class WedgeSourceTests(unittest.TestCase):
    def test_source_exists_and_under_line_ceiling(self):
        lines = WEDGE.read_text(encoding="utf-8").count("\n") + 1
        self.assertLess(lines, 500, f"scan-wedge.js {lines} 行 · 铁律单文件 <500")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class WedgeTimingTests(unittest.TestCase):
    def test_gap_finalizes_the_string(self):
        got = _run_node(_prelude() + """
            const seen = [];
            wedge.register((code) => seen.push(code));
            type(['4', '9', '0', '1']);
            setTimeout(() => out({ seen, prevented }), GAP + 80);
            """)
        self.assertEqual(got["seen"], ["4901"])
        # 靠间隔收尾时没有按键要吃掉
        self.assertEqual(got["prevented"], 0)

    def test_keys_within_gap_stay_one_string(self):
        got = _run_node(_prelude() + """
            const seen = [];
            wedge.register((code) => seen.push(code));
            type(['4', '9']);
            setTimeout(() => {
                type(['0', '1']);                      // 仍在 GAP 之内 → 同一串
                setTimeout(() => out({ seen }), GAP + 80);
            }, Math.max(1, GAP - 100));
            """)
        self.assertEqual(got["seen"], ["4901"])

    def test_gap_splits_two_scans(self):
        got = _run_node(_prelude() + """
            const seen = [];
            wedge.register((code) => seen.push(code));
            type(['4', '9', '0', '1']);
            setTimeout(() => {
                type(['5', '6', '7', '8']);
                setTimeout(() => out({ seen }), GAP + 80);
            }, GAP + 80);
            """)
        self.assertEqual(got["seen"], ["4901", "5678"])

    def test_shorter_than_min_length_dropped(self):
        got = _run_node(_prelude() + """
            const seen = [];
            wedge.register((code) => seen.push(code));
            type(['1', '2']);
            setTimeout(() => out({ seen, min: wedge.MIN_LENGTH }), GAP + 80);
            """)
        self.assertEqual(got["seen"], [])
        self.assertEqual(got["min"], 3)

    def test_exactly_min_length_delivered(self):
        got = _run_node(_prelude() + """
            const seen = [];
            wedge.register((code) => seen.push(code));
            type(['1', '2', '3']);
            setTimeout(() => out({ seen }), GAP + 80);
            """)
        self.assertEqual(got["seen"], ["123"])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class WedgeEndKeyTests(unittest.TestCase):
    def test_enter_finalizes_immediately_and_prevents_default(self):
        # 不等 GAP 就读结果:Enter 必须当场收尾,不是「顺便也能收尾」。
        got = _run_node(_prelude() + """
            const seen = [];
            wedge.register((code) => seen.push(code));
            type(['4', '9', '0', '1', 'Enter']);
            out({ seen, prevented });
            """)
        self.assertEqual(got["seen"], ["4901"])
        self.assertEqual(got["prevented"], 1, "枪的回车没被吃掉 · 表单会被顺手提交")

    def test_tab_finalizes_immediately(self):
        got = _run_node(_prelude() + """
            const seen = [];
            wedge.register((code) => seen.push(code));
            type(['8', '8', '5', '1', 'Tab']);
            out({ seen, prevented });
            """)
        self.assertEqual(got["seen"], ["8851"])
        self.assertEqual(got["prevented"], 1)

    def test_enter_on_short_buffer_not_prevented(self):
        # 人在页面上按回车(缓冲区里没东西)不能被楔子吃掉,否则所有回车提交都失灵。
        got = _run_node(_prelude() + """
            const seen = [];
            wedge.register((code) => seen.push(code));
            press('Enter');
            out({ seen, prevented });
            """)
        self.assertEqual(got["seen"], [])
        self.assertEqual(got["prevented"], 0)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class WedgeEndKeyOwnershipTests(unittest.TestCase):
    """Enter/Tab 吃不吃,取决于这一串是枪打的还是人打的。

    只看「长度够不够」就 preventDefault 会把人打的导航键一起吞掉 —— 而落点是可编辑元素时,
    正在打字的十有八九是人。判据只能是速度:枪实测 ≤50ms/字符,人手进不到那个区间。
    """

    # 人手速度:两键之间 90ms —— 高于枪速上限(50),又没到 MAX_GAP_MS(150)把一串拆开。
    _HUMAN_GAP = 90

    def _typed_slowly(self, keys: list[str], target: str) -> dict:
        return _run_node(_prelude() + """
            const seen = [];
            wedge.register((code) => seen.push(code));
            const keys = %s;
            const target = %s;
            (function next(i) {
                if (i >= keys.length) { out({ seen, prevented }); return; }
                press(keys[i], target);
                setTimeout(() => next(i + 1), %d);
            })(0);
            """ % (json.dumps(keys), target, self._HUMAN_GAP))

    def test_human_typed_tab_in_optin_field_keeps_moving_focus(self):
        # 入库数量框带 data-enable-barcode(扫完一件光标就停在那儿,下一枪照旧要收得到)。
        # 店员在里面打「1000」再按 Tab:那是导航键。只看长度就吃掉的话,焦点纹丝不动,
        # 店员只能看出「弹窗卡住了」。
        got = self._typed_slowly(
            ["1", "0", "0", "0", "Tab"],
            "{ tagName: 'INPUT', dataset: { enableBarcode: '' } }",
        )
        self.assertEqual(got["seen"], ["1000"], "串被拆开了 · 这轮的 prevented 不作数")
        self.assertEqual(got["prevented"], 0, "人手打的 Tab 被吃掉 · 焦点走不了")

    def test_gun_speed_tab_in_optin_field_is_swallowed(self):
        # 同一个框里换成枪:字符间隔 ≈0,收尾的 Tab 是枪发的,吃掉它 ——
        # 不吃焦点就被顺手挪走,下一枪落到别的控件上。
        got = _run_node(_prelude() + """
            const seen = [];
            const qty = { tagName: 'INPUT', dataset: { enableBarcode: '' } };
            wedge.register((code) => seen.push(code));
            type(['8','8','5','0','9','9','9','3','2','0','0','1','4','Tab'], qty);
            out({ seen, prevented, gunGap: wedge.GUN_MAX_GAP_MS });
            """)
        self.assertEqual(got["seen"], ["8850999320014"])
        self.assertEqual(got["prevented"], 1, "枪的 Tab 没吃掉 · 焦点被顺手挪走")
        self.assertLess(got["gunGap"], 150, "枪速上限没低于 MAX_GAP_MS · 判据没有区分力")

    def test_slow_burst_outside_editable_still_swallows_enter(self):
        # 落点不是可编辑元素 = 那儿本来就没人在打字。有的枪带 intercharacter delay,
        # 不该因为慢就把回车漏给表单 —— 这条守住「别矫枉过正」。
        got = self._typed_slowly(["4", "9", "0", "1", "Enter"], "null")
        self.assertEqual(got["seen"], ["4901"])
        self.assertEqual(got["prevented"], 1, "页面上的一串慢枪输入,回车漏给了表单")


# 会被字符打进去的框。楔子不吃字符键(吃了人手打字就没了),所以扫进来的那一串一定会先
# 落进框里 —— 桩必须照这个样子来,否则「认成枪扫之后把框还原」这条根本无从验起。
_FIELDS = """
    function fieldBase(mode, initial) {
        return {
            tagName: 'INPUT',
            dataset: mode === null ? {} : { enableBarcode: mode },
            value: initial || '',
        };
    }
    function textField(mode, initial) {
        const el = fieldBase(mode, initial);
        el.accept = function (k) { this.value += k; };
        return el;
    }
    // type=date 不把原串存进 value:Chrome 把 4901234567894 吃成一个荒唐的日期,使用方拿不到
    // 那串原文,想「把扫进来的那段从 value 里摘回去」无从下手 —— 只有楔子手上有扫前快照。
    function dateField(mode, initial) {
        const el = fieldBase(mode, initial);
        el.type = 'date';
        el.typed = '';
        el.accept = function (k) {
            this.typed += k;
            if (this.typed.length >= 6) this.value = '49012-03-31';
        };
        return el;
    }
    // 按指定字符间隔敲一串。间隔是这一组用例的全部区分力,不能拿同步 forEach 糊过去。
    function typeAt(keys, target, gapMs, done) {
        (function next(i) {
            if (i >= keys.length) { done(); return; }
            press(keys[i], target);
            setTimeout(() => next(i + 1), gapMs);
        })(0);
    }
"""

COKE_KEYS = json.dumps(list("4901234567894"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class WedgeGunOnlyFieldTests(unittest.TestCase):
    """data-enable-barcode="gun":这个框里只有【枪打的那种串】算条码。

    为什么要有这一档 —— 入库「填完这箱再扫下一箱」是标准动作,而批号/效期就是两个普通的
    可编辑框:不声明,楔子按「有人在打字」让开,条码 4901234567894 被打进 type=date,
    效期变成 49012-03-31(date 控件收 6 位年份、提交不拦),扫码零回调、第二箱行压根没
    出现、屏上无任何消息,店员以为枪没响再扫一次又被吞;FEFO 与近效期告警从此按四万九千年
    后算。反过来,把它声明成不分青红皂白的那一档也不行:人手在同一个框里填日期会被抢走。
    所以这一组的输入全是「两种可能性都沾一点」的串 —— 长得像条码的人手输入、快得像枪的
    人手输入、以及真的枪扫。
    """

    def test_gun_burst_into_date_field_is_delivered_and_field_restored(self):
        got = _run_node(
            _prelude()
            + _FIELDS
            + """
            const seen = [];
            const box = dateField('gun');
            wedge.register((code, target) => seen.push([code, target === box]));
            typeAt(%s, box, 0, () => {
                press('Enter', box);
                out({ seen, prevented, value: box.value, typed: box.typed });
            });
            """
            % COKE_KEYS
        )
        self.assertEqual(got["seen"], [["4901234567894", True]], "枪扫进效期框被整发吞掉了")
        self.assertEqual(got["typed"], "4901234567894", "这一串没真打进框里 · 这轮证明不了还原")
        self.assertEqual(got["value"], "", f"垃圾日期留在格子里了: {got['value']}")
        self.assertEqual(got["prevented"], 1, "枪的回车没吃掉 · 半张入库单会被顺手提交")

    def test_restore_puts_back_what_was_already_typed(self):
        # 店员先手写了批号,再扫下一箱 —— 还原是「回到扫之前」,不是把整格清空。
        got = _run_node(
            _prelude()
            + _FIELDS
            + """
            const seen = [];
            const box = textField('gun', 'LOT-B240301');
            wedge.register((code) => seen.push(code));
            typeAt(%s, box, 0, () => {
                press('Enter', box);
                out({ seen, value: box.value });
            });
            """
            % COKE_KEYS
        )
        self.assertEqual(got["seen"], ["4901234567894"])
        self.assertEqual(got["value"], "LOT-B240301", "还原把店员先前填好的批号一起抹了")

    def test_human_typed_date_digits_are_left_in_the_field(self):
        # 最要命的那种输入:人手打的「31032027」有 8 位,长度这条判据一个人都拦不住,
        # 全靠速度分开。被抢走 = 店员填的效期当场消失,还平白多出一条「扫到 31032027」。
        got = _run_node(
            _prelude()
            + _FIELDS
            + """
            const seen = [];
            const box = dateField('gun');
            wedge.register((code) => seen.push(code));
            typeAt(['3','1','0','3','2','0','2','7'], box, 90, () => {
                press('Tab', box);
                out({ seen, prevented, typed: box.typed, value: box.value });
            });
            """
        )
        self.assertEqual(got["seen"], [], "人手填的日期被当成扫码抢走了")
        self.assertEqual(got["typed"], "31032027", "串没打进框 · 这轮不作数")
        self.assertEqual(got["value"], "49012-03-31", "楔子动了人手填的内容")
        self.assertEqual(got["prevented"], 0, "人手打的 Tab 被吃掉 · 焦点走不了")

    def test_held_key_autorepeat_is_not_a_scan(self):
        # 按住一个键不放:系统自动重复约 30ms 一发,速度和长度两条判据都过得去。
        # 只有「至少两种不同字符」拦得住它 —— 拦不住就是店员按住 0 不放,框被清空。
        got = _run_node(
            _prelude()
            + _FIELDS
            + """
            const seen = [];
            const box = textField('gun');
            wedge.register((code) => seen.push(code));
            typeAt(['0','0','0','0','0','0','0','0','0','0'], box, 30, () => {
                setTimeout(() => out({ seen, value: box.value }), wedge.MAX_GAP_MS + 80);
            });
            """
        )
        self.assertEqual(got["seen"], [], "按住一个键不放被当成扫了一件货")
        self.assertEqual(got["value"], "0000000000", "自动重复被当成扫码 · 框被清了")

    def test_short_fast_burst_is_not_a_scan(self):
        # 「2027」四位打得飞快(手指熟练的店员填年份就是这样)。零售码最短 8 位,
        # 长度这条判据在这里是唯一的拦网。
        got = _run_node(
            _prelude()
            + _FIELDS
            + """
            const seen = [];
            const box = textField('gun');
            wedge.register((code) => seen.push(code));
            typeAt(['2','0','2','7'], box, 0, () => {
                setTimeout(() => out({ seen, value: box.value, min: wedge.GUN_MIN_LENGTH }),
                    wedge.MAX_GAP_MS + 80);
            });
            """
        )
        self.assertEqual(got["seen"], [], "四位快打被当成扫了一件货")
        self.assertEqual(got["value"], "2027")
        self.assertGreaterEqual(got["min"], 8, "枪扫长度下限低于 EAN-8 的 8 位 · 判据没有区分力")

    def test_gun_burst_without_end_key_still_delivered(self):
        # 有的枪不发后缀,靠 MAX_GAP_MS 收尾。这一档同样要还原 + 送出。
        got = _run_node(
            _prelude()
            + _FIELDS
            + """
            const seen = [];
            const box = dateField('gun');
            wedge.register((code) => seen.push(code));
            typeAt(%s, box, 0, () => {
                setTimeout(() => out({ seen, value: box.value }), wedge.MAX_GAP_MS + 80);
            });
            """
            % COKE_KEYS
        )
        self.assertEqual(got["seen"], ["4901234567894"], "不带后缀的枪在这个框里被吞了")
        self.assertEqual(got["value"], "", "垃圾日期留在格子里了")

    def test_always_mode_field_keeps_what_was_typed_into_it(self):
        # 另一档(裸 data-enable-barcode,入库数量框)不还原:那串字符归使用方摘
        # (inventory-scan.ts::stripScanned,它拿得到原串)。两档的差别写在这条上,
        # 免得下一个人顺手把还原做成全局的,把数量框的摘取逻辑架空。
        got = _run_node(
            _prelude()
            + _FIELDS
            + """
            const seen = [];
            const qty = textField('', '1');
            wedge.register((code) => seen.push(code));
            typeAt(%s, qty, 0, () => {
                press('Enter', qty);
                out({ seen, value: qty.value });
            });
            """
            % COKE_KEYS
        )
        self.assertEqual(got["seen"], ["4901234567894"])
        self.assertEqual(got["value"], "14901234567894", "裸声明那档被引擎顺手还原了")

    def test_undeclared_editable_field_is_still_left_alone(self):
        # 这一档是「别把人手填日期也抢走」的底线:没声明就一律让开,跟改动前一样。
        # 声明由使用方按框逐个给(入库那两个框归 D 组),引擎不替它们做主。
        got = _run_node(
            _prelude()
            + _FIELDS
            + """
            const seen = [];
            const box = dateField(null);
            wedge.register((code) => seen.push(code));
            typeAt(%s, box, 0, () => {
                press('Enter', box);
                out({
                    seen,
                    prevented,
                    capture: {
                        none: wedge.shouldCapture(dateField(null)),
                        gun: wedge.shouldCapture(dateField('gun')),
                    },
                    mode: {
                        none: wedge.barcodeMode(dateField(null)),
                        gun: wedge.barcodeMode(dateField('gun')),
                        bare: wedge.barcodeMode(dateField('')),
                    },
                });
            });
            """
            % COKE_KEYS
        )
        self.assertEqual(got["seen"], [], "没声明的框被抢了")
        self.assertEqual(got["prevented"], 0)
        self.assertEqual(got["capture"], {"none": False, "gun": True})
        self.assertEqual(got["mode"], {"none": "", "gun": "gun", "bare": "always"})


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class WedgeFocusTests(unittest.TestCase):
    def test_focused_input_is_not_hijacked(self):
        got = _run_node(_prelude() + """
            const seen = [];
            wedge.register((code) => seen.push(code));
            type(['4', '9', '0', '1'], { tagName: 'INPUT' });
            setTimeout(() => out({ seen }), GAP + 80);
            """)
        self.assertEqual(got["seen"], [])

    def test_focused_textarea_is_not_hijacked(self):
        got = _run_node(_prelude() + """
            const seen = [];
            wedge.register((code) => seen.push(code));
            type(['4', '9', '0', '1'], { tagName: 'TEXTAREA' });
            setTimeout(() => out({ seen }), GAP + 80);
            """)
        self.assertEqual(got["seen"], [])

    def test_contenteditable_is_not_hijacked(self):
        got = _run_node(_prelude() + """
            const seen = [];
            wedge.register((code) => seen.push(code));
            type(['4', '9', '0', '1'], { tagName: 'DIV', isContentEditable: true });
            setTimeout(() => out({ seen }), GAP + 80);
            """)
        self.assertEqual(got["seen"], [])

    def test_input_with_data_enable_barcode_opts_in(self):
        got = _run_node(_prelude() + """
            const seen = [];
            const box = { tagName: 'INPUT', dataset: { enableBarcode: '' } };
            wedge.register((code) => seen.push(code));
            type(['4', '9', '0', '1'], box);
            setTimeout(() => out({ seen }), GAP + 80);
            """)
        self.assertEqual(got["seen"], ["4901"])

    def test_non_editable_target_captured_and_passed_back(self):
        got = _run_node(_prelude() + """
            const seen = [];
            const btn = { tagName: 'BUTTON', id: 'pay' };
            wedge.register((code, target) => seen.push([code, target && target.id]));
            type(['4', '9', '0', '1'], btn);
            setTimeout(() => out({ seen }), GAP + 80);
            """)
        self.assertEqual(got["seen"], [["4901", "pay"]])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class WedgeKeyFilterTests(unittest.TestCase):
    def test_non_printable_keys_never_enter_the_buffer(self):
        got = _run_node(_prelude() + """
            const seen = [];
            wedge.register((code) => seen.push(code));
            type(['4', 'ArrowLeft', '9', 'F5', '0', 'Escape', '1']);
            setTimeout(() => out({ seen }), GAP + 80);
            """)
        self.assertEqual(got["seen"], ["4901"], "功能键被当字符拼进条码了")

    def test_meta_combo_ignored(self):
        got = _run_node(_prelude() + """
            const seen = [];
            wedge.register((code) => seen.push(code));
            handlers.forEach((h) =>
                h({ key: 'r', metaKey: true, target: BODY, preventDefault: () => {} })
            );
            type(['4', '9', '0']);
            setTimeout(() => out({ seen }), GAP + 80);
            """)
        self.assertEqual(got["seen"], ["490"])

    def test_clean_strips_modifier_names(self):
        # 枪发 GS1 分隔符时会带 Alt/Control 组合键;键名本身不是条码内容。
        got = _run_node(_prelude() + """
            out({
                mixed: wedge.clean('49Alt01Shift'),
                ctrl: wedge.clean('Control8851234567895'),
                empty: wedge.clean(null),
            });
            """)
        self.assertEqual(got["mixed"], "4901")
        self.assertEqual(got["ctrl"], "8851234567895")
        self.assertEqual(got["empty"], "")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class WedgeSubscriptionTests(unittest.TestCase):
    def test_no_global_listener_until_first_register(self):
        got = _run_node(_prelude() + """
            const before = handlers.length;
            const off = wedge.register(() => {});
            const during = handlers.length;
            off();
            out({ before, during, after: handlers.length, subs: wedge.subscriberCount() });
            """)
        self.assertEqual(got, {"before": 0, "during": 1, "after": 0, "subs": 0})

    def test_unregister_stops_delivery(self):
        got = _run_node(_prelude() + """
            const seen = [];
            const off = wedge.register((code) => seen.push(code));
            off();
            type(['4', '9', '0', '1']);
            setTimeout(() => out({ seen }), GAP + 80);
            """)
        self.assertEqual(got["seen"], [])

    def test_two_subscribers_both_receive(self):
        got = _run_node(_prelude() + """
            const a = [], b = [];
            wedge.register((c) => a.push(c));
            wedge.register((c) => b.push(c));
            type(['4', '9', '0', '1', 'Enter']);
            out({ a, b });
            """)
        self.assertEqual(got, {"a": ["4901"], "b": ["4901"]})

    def test_exclusive_subscriber_takes_over(self):
        got = _run_node(_prelude() + """
            const page = [], modal = [];
            wedge.register((c) => page.push(c));
            const closeModal = wedge.register((c) => modal.push(c), { exclusive: true });
            type(['4', '9', '0', '1', 'Enter']);
            closeModal();
            type(['5', '6', '7', '8', 'Enter']);
            out({ page, modal });
            """)
        self.assertEqual(got["modal"], ["4901"], "modal 开着时没独占")
        self.assertEqual(got["page"], ["5678"], "modal 关掉后页面订阅没恢复")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class WedgeAndroidSinkTests(unittest.TestCase):
    def test_touch_device_gets_inputmode_none_sink(self):
        # 安卓上蓝牙枪一被当键盘就弹软键盘挡屏;inputmode="none" 的隐藏 input 是压掉它的办法。
        got = _run_node(_prelude(touch=True) + """
            wedge.register(() => {});
            const sink = created[0];
            out({
                made: created.length,
                inputmode: sink && sink.attrs.inputmode,
                autocomplete: sink && sink.attrs.autocomplete,
                cls: sink && sink.className,
            });
            """)
        self.assertEqual(got["made"], 1)
        self.assertEqual(got["inputmode"], "none")
        self.assertEqual(got["autocomplete"], "off")
        self.assertEqual(got["cls"], "bscan-sink")

    def test_desktop_does_not_create_sink(self):
        got = _run_node(_prelude() + """
            wedge.register(() => {});
            out({ made: created.length });
            """)
        self.assertEqual(got["made"], 0, "非触屏设备不该白塞一个隐藏 input")

    def test_sink_gets_focus_so_soft_keyboard_stays_down(self):
        got = _run_node(_prelude(touch=True) + """
            const seen = [];
            wedge.register((c) => seen.push(c));
            type(['4', '9', '0', '1', 'Enter']);
            out({ seen, focused: created[0].focused > 0 });
            """)
        self.assertEqual(got["seen"], ["4901"])
        self.assertTrue(got["focused"], "没把焦点塞进水槽 · 安卓软键盘会弹出来挡屏")


if __name__ == "__main__":
    unittest.main()
