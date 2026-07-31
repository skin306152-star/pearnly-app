#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_scan_wedge_ruler.py · 「枪 vs 人」这把尺子本身的反证

前三轮的病根一次比一次深:功能没闸 → 闸用不会出事的输入验会出事的判据 → 判据本身量错了
东西。所以这一组测的不是「楔子能不能收到码」(那在 test_scan_wedge_pure.py),是尺子:

  1. 量的是【事件产生的时刻】还是【它在主线程被处理的时刻】。8ms/字符的真枪 + 一次 120ms
     长任务,后者量出来是 120ms 的坎 —— 自变量(主线程忙不忙)和因变量(判枪还是判人)
     成了同一个东西。断言直接钉 info.gap:换回墙钟这条就红。
  2. 慢枪 50~150ms 六档:落在框里的一律当人打的(判不准时偏向人手,那一半的错是可见的)。
  3. 按住一个键不放:实测 40~48ms 一发,速度和长度两条判据全过,只有 repeat 答得了。
  4. 人手中速填日期 100~260ms + 带分隔符的写法:框里的东西一个字都不许动。
  5. 防修过头:真枪打进已填好的框,原内容必须原样还回、码照旧落成一行。
  6. 尺子挂在哪儿(第五轮):按住一个键不放这条原先只在「落进声明接枪的框」时被问到,而
     收银主屏的焦点常态在 body 上 —— 框外那条路一条用例都没有。框内框外结论必须一样。
  7. 跨界(第五轮):一串枪从框外开头、结尾落进声明接枪的框(产品自己制造:命中后
     qty.focus())。快照只取第一个键那一次时两道保护同时落空,码照旧发出去查而数量框被
     写脏。凡是发出去查了的那一串,它碰过的每个框都必须回到扫之前。

元素不是这里现造的:声明档位与 input type 都从产品源码(inventory-modals.ts /
sales-products-scan.ts)里抠出来,合法档位从引擎常量里抠。产品哪天把声明改回裸的、或者
把效期框换成 type=text,这一组的靶子跟着变 —— 验的永远是产品真在用的那一档。
"""

from __future__ import annotations

import json
import re
import shutil
import unittest
from pathlib import Path

from tests.unit._node_harness import PROJECT_ROOT, _run_node

WEDGE = PROJECT_ROOT / "static" / "scan" / "scan-wedge.js"

COKE = "4901234567894"  # 13 位 EAN · 枪扫的那一串
OLD_CODE = "8850999320014"  # 框里已经有的码
LOT = "LOT-B240301"  # 店员手写的批号
# 柜台上压住一个键:12 发自动重复的 '0',松手时蹭到 '5''7'。真 Chromium 实测(_r5 的 c2)
# 就是这个形状 —— 长度和速度两条判据全过,只有 repeat / 整串一个字符答得了。
HELD_KEYS = "0" * 12 + "57"


def _mode_gun() -> str:
    m = re.search(r"var MODE_GUN\s*=\s*'([a-z]+)'", WEDGE.read_text(encoding="utf-8"))
    if not m:
        raise AssertionError("scan-wedge.js 里找不到 MODE_GUN —— 判据的合法值没了,断言无从谈起")
    return m.group(1)


MODE_GUN = _mode_gun()


def _product_field(rel: str, anchor: str) -> dict:
    """从产品源码里抠出某个框的真实声明(档位 + input type)。

    抠不到就直接失败:靶子从产品里来,产品改了这里必须当场知道,而不是继续验一个
    产品不使用的元素(本仓吃过这个亏:验收脚本用桩造出产品里不存在的对象来验自己)。
    """
    text = (PROJECT_ROOT / rel).read_text(encoding="utf-8")
    tags = [t for t in re.findall(r"<input\b[^>]*>", text) if anchor in t]
    if len(tags) != 1:
        raise AssertionError(f"{rel} 里带 {anchor} 的 <input> 有 {len(tags)} 个 · 靶子对不上")
    tag = tags[0]
    tier = re.search(r'data-enable-barcode="([^"]*)"', tag)
    if not tier:
        raise AssertionError(f"{rel} 的 {anchor} 没写 data-enable-barcode 档位值")
    kind = re.search(r'\btype="([^"]*)"', tag)
    return {"tier": tier.group(1), "type": kind.group(1) if kind else "text"}


QTY = _product_field("src/home/inventory-modals.ts", 'data-k="qty"')
BATCH = _product_field("src/home/inventory-modals.ts", 'data-k="batch_no"')
EXPIRY = _product_field("src/home/inventory-modals.ts", 'data-k="expiry_date"')
BARCODE = _product_field("src/home/sales-products-scan.ts", "${INPUT_ID}")


# ── node 桩 ────────────────────────────────────────────────────────────────
# 按键带两个时刻:stamp(事件产生的时刻 · 物理节拍算出来的)与真正调用处理器的那一刻。
# 主线程被堵住时两者分开 —— 这正是要验的东西,所以桩必须把它们分开造。
_PRELUDE = """
    const handlers = [];
    const focusins = [];
    // 按事件类型分开派发:混在一个数组里,keydown 也会喂给 focusin 处理器,于是「焦点挪走
    // 那一刻取快照」这条永远看起来是对的(每发按键都替它补了一遍),等于没验。
    global.document = {
        addEventListener: (t, f) => (t === 'focusin' ? focusins : handlers).push(f),
        removeEventListener: (t, f) => {
            const list = t === 'focusin' ? focusins : handlers;
            const i = list.indexOf(f);
            if (i >= 0) list.splice(i, 1);
        },
        createElement: () => ({ style: {}, value: '', setAttribute() {}, focus() {} }),
        body: { appendChild: () => {} },
    };
    const wedge = require(%s);
    const seen = [];
    const typed = []; // 判成「人在打字」时楔子给的那一声(onTyped)· 不是第二个判据出口
    let prevented = 0;
    wedge.register((code, target, info) => seen.push({ code, info }), {
        onTyped: (code, target, info) =>
            typed.push({ code, before: info.before, field: info.field }),
    });

    // 产品里那个框长什么样,就照什么样造(type / 档位都来自产品源码)。
    function field(spec, initial) {
        const el = {
            tagName: 'INPUT',
            type: spec.type,
            dataset: { enableBarcode: spec.tier },
            value: initial || '',
        };
        el.accept = (k) => { el.value += k; };
        return el;
    }
    // <input type=date>:真 Chromium 把打进来的数字按自己的格式重排,原串拿不回来,只留下
    // 一个「残渣」。残渣长什么样由调用方按实测值给(scripts/_gun_ruler_verify.cjs 量的),
    // 判据绝不该看它 —— 人打的和机器打的残渣互相穿帮,方向是反的。
    function dateField(spec, initial, residue) {
        const el = field(spec, initial);
        el.typed = '';
        el.accept = (k) => {
            el.typed += k;
            if (residue !== undefined && el.typed.length >= 6) el.value = residue;
        };
        return el;
    }

    // 收银主屏的常态:焦点在 body 上,楔子直接收(不是任何一个声明接枪的框)。
    const BODY = { tagName: 'BODY' };
    // 浏览器在 focus() 里【同步】发 focusin,那一刻新框还没接到这一串的任何字符。
    function focusTo(el) { focusins.forEach((h) => h({ target: el })); }

    /**
     * 发一发按键。
     * target        这一发 keydown 的 target —— 浏览器在派发【开始】时定死,派发中途改焦点也不变。
     * onDispatched  处理器都跑完之后、字符落进框之前做的事(产品在 keydown 里挪光标就落在这个
     *               位置)。它返回哪个元素,这一发的字符就落进哪个,而不是 target。
     */
    function press(key, target, stamp, repeat, onDispatched) {
        handlers.forEach((h) =>
            h({
                key,
                target,
                repeat: !!repeat,
                timeStamp: stamp,
                preventDefault: () => { prevented += 1; },
            })
        );
        const land = (onDispatched && onDispatched()) || target;
        if (key.length === 1 && land && typeof land.accept === 'function') land.accept(key);
    }

    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const block = (ms) => { const end = Date.now() + ms; while (Date.now() < end) {} };

    /**
     * 按物理节拍发一串键。stamp 从节拍算,与处理器什么时候真被调用无关。
     * blockAt: 发到第几个字符时主线程被一个长任务堵住(堵住期间的按键攒着,解封后一起到)。
     *
     * 真正 sleep 的时长封顶 30ms,故意的:让「按键送达处理器的间隔」与「按键产生的间隔」
     * 对不上。引擎量对了地方(stamp)时这一层差异不影响结论;量错了地方(墙钟)时,一串
     * 120ms 的人手输入会以 30ms 的节奏送达 —— 当场被判成枪。这就是这组反证的红线所在。
     */
    async function burst(keys, target, gapMs, opts) {
        const o = opts || {};
        const jump = o.jump; // { at, to, inDispatch } 打到一半光标被挪进另一个框
        let where = target;
        let stamp = 1000;
        for (let i = 0; i < keys.length; i++) {
            if (i) stamp += gapMs;
            if (o.blockAt === i) block(o.blockMs || 120);
            let after = null;
            if (jump && jump.at === i && jump.inDispatch) {
                // 产品在 keydown 处理器里挪光标:这一发的 target 还是旧框,字符却落进新框。
                after = () => { focusTo(jump.to); where = jump.to; return jump.to; };
            } else if (jump && jump.at === i) {
                // 常态:光标是查码应答回来时挪的(inventory-scan.ts 命中后 qty.focus()),
                // 落在两发按键【之间】—— 新框这时还是干净的。
                focusTo(jump.to);
                where = jump.to;
            }
            press(keys[i], where, stamp, o.repeat && i > 0, after);
            if (!o.bunchedAfter || i < o.bunchedAfter) await sleep(Math.min(gapMs, 30));
        }
        if (o.end) press(o.end, where, stamp + gapMs);
    }

    const out = (o) => process.stdout.write(JSON.stringify(o));
    const settle = (o) => setTimeout(() => out(o()), wedge.MAX_GAP_MS + 90);
""" % json.dumps(str(WEDGE))


def _js(body: str) -> str:
    return _PRELUDE + body


def _run(body: str) -> dict:
    return _run_node(_js(body))


def _keys(text: str) -> str:
    return json.dumps(list(text))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class TargetsComeFromProductSourceTests(unittest.TestCase):
    """靶子不是这里编的 —— 先把这件事本身钉住。"""

    def test_all_four_declared_fields_use_the_engine_tier(self):
        for name, spec in (
            ("qty", QTY),
            ("batch", BATCH),
            ("expiry", EXPIRY),
            ("barcode", BARCODE),
        ):
            with self.subTest(field=name):
                self.assertEqual(spec["tier"], MODE_GUN, f"{name} 框声明的不是引擎那一档")

    def test_expiry_is_a_native_date_control_and_the_others_are_not(self):
        # 效期框是 type=date 才有「原串拿不回来、只能靠扫前快照还原」这个问题。
        self.assertEqual(EXPIRY["type"], "date")
        self.assertEqual(QTY["type"], "number")
        self.assertEqual(BARCODE["type"], "text")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class RulerMeasuresEventTimeTests(unittest.TestCase):
    """反证 2 · 真枪 + 一次 120ms 长任务。这条不依赖「蓝牙枪真的慢」那个前提。"""

    def test_long_task_does_not_turn_a_real_gun_into_a_human(self):
        got = _run("""
            const box = field(%s, '');
            burst(%s, box, 8, { blockAt: 4, blockMs: 120, bunchedAfter: 4, end: 'Enter' })
                .then(() => out({ seen, prevented, value: box.value }));
            """ % (json.dumps(BATCH), _keys(COKE)))
        self.assertEqual([s["code"] for s in got["seen"]], [COKE], "长任务一卡,真枪就被判成人手")
        self.assertEqual(got["prevented"], 1, "枪的回车没吃掉")
        # 尺子直接受审:量的是事件产生时刻就该是 8ms 上下;换回墙钟这里会跳到 120 上下。
        self.assertLessEqual(
            got["seen"][0]["info"]["gap"],
            20,
            "引擎量到的间隔跟着主线程卡顿走了 · 尺子量的是处理时刻不是产生时刻",
        )

    def test_the_field_is_restored_even_though_the_burst_arrived_bunched(self):
        got = _run("""
            const box = field(%s, %s);
            burst(%s, box, 8, { blockAt: 4, blockMs: 120, bunchedAfter: 4, end: 'Enter' })
                .then(() => out({ seen, value: box.value }));
            """ % (json.dumps(BATCH), json.dumps(LOT), _keys(COKE)))
        self.assertEqual([s["code"] for s in got["seen"]], [COKE])
        self.assertEqual(got["value"], LOT, "长任务那一路没走还原 · 码跟批号接成了一串")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SlowBurstInDeclaredFieldTests(unittest.TestCase):
    """反证 1 · 慢枪 50~150ms 六档。

    没有哪个阈值能把「慢枪」和「打字快的人」分开(人手实测 100~260ms,两段叠着)。所以这一
    档的结论是明确选的:落在框里就当人打的 —— 错了店员看得见(码没落地,再扫一次),反过来
    错是静默改效期。这条钉的是「不许有人再拿代理判据把它抢过去」。
    """

    SPEEDS = [55, 70, 90, 110, 140, 149]

    def test_the_threshold_is_exactly_where_it_says_it_is(self):
        # 阈值本身要钉住:恰好 GUN_MAX_GAP_MS 算枪,多 1ms 就归人。含糊的边界会被下一个人
        # 「顺手放宽一点」,而放宽的方向正是把人手打的抢过来。
        got = _run("""
            const at = field(%s, ''), over = field(%s, '');
            const run = async () => {
                await burst(%s, at, wedge.GUN_MAX_GAP_MS, { end: 'Enter' });
                const first = seen.length;
                await burst(%s, over, wedge.GUN_MAX_GAP_MS + 1, { end: 'Enter' });
                out({ atThreshold: first, overThreshold: seen.length - first,
                      limit: wedge.GUN_MAX_GAP_MS });
            };
            run();
            """ % (json.dumps(BATCH), json.dumps(BATCH), _keys(COKE), _keys(COKE)))
        self.assertEqual(got["limit"], 50)
        self.assertEqual(got["atThreshold"], 1, "恰好卡在上限的一串没被当成枪")
        self.assertEqual(got["overThreshold"], 0, "超过上限 1ms 还当枪 · 判据的边界是软的")

    def test_slow_burst_in_a_declared_field_is_left_to_the_human(self):
        for gap in self.SPEEDS:
            with self.subTest(gapMs=gap):
                got = _run("""
                    const box = field(%s, '');
                    burst(%s, box, %d, { end: 'Tab' })
                        .then(() => out({ seen, prevented, value: box.value }));
                    """ % (json.dumps(BATCH), _keys(COKE), gap))
                self.assertEqual(got["seen"], [], f"{gap}ms/字符被当成枪扫抢走了")
                self.assertEqual(got["prevented"], 0, f"{gap}ms/字符的 Tab 被吃掉 · 焦点走不了")
                self.assertEqual(got["value"], COKE, "楔子动了框里的内容")

    def test_a_slow_burst_outside_any_field_is_still_a_scan(self):
        # 防修过头的另一半:框外没人在打字,慢也照收(有些枪带 intercharacter delay)。
        got = _run("""
            burst(%s, { tagName: 'BUTTON', id: 'pay' }, 70, { end: 'Enter' })
                .then(() => out({ seen, prevented }));
            """ % _keys(COKE))
        self.assertEqual([s["code"] for s in got["seen"]], [COKE], "页面上的慢枪被丢了")
        self.assertEqual(got["prevented"], 1)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class HeldKeyTests(unittest.TestCase):
    """反证 3 · 按住一个键不放(真 Chromium 实测 40.1~47.9ms 一发,全落在 50ms 判据以内)。"""

    def test_autorepeat_of_one_key_is_not_a_scan(self):
        got = _run("""
            const box = field(%s, '');
            burst(%s, box, 45, { repeat: true })
                .then(() => settle(() => ({ seen, value: box.value })));
            """ % (json.dumps(BATCH), _keys("0" * 12)))
        self.assertEqual(got["seen"], [], "按住一个键不放被当成扫了一件货")
        self.assertEqual(got["value"], "0" * 12, "自动重复被当成扫码 · 框被清了")

    def test_autorepeat_of_a_digit_inside_an_existing_code_is_not_a_scan(self):
        # 三轮实测的那一发:按住 0 不放,把 8850999320014 整框换成 0000000000 还回绿字。
        got = _run("""
            const box = field(%s, %s);
            burst(%s, box, 45, { repeat: true })
                .then(() => settle(() => ({ seen, value: box.value })));
            """ % (json.dumps(BARCODE), json.dumps(OLD_CODE), _keys("0" * 10)))
        self.assertEqual(got["seen"], [], "按住 0 不放把商品的条码换掉了")
        self.assertTrue(got["value"].startswith(OLD_CODE), "楔子把框里原来的码抹了")

    def test_repeat_flag_beats_speed_even_at_gun_cadence(self):
        # repeat 拿得到时,快到 5ms 也不算枪:那是一个键的自动重复,不是十三次击键。
        got = _run("""
            const box = field(%s, '');
            burst(%s, box, 5, { repeat: true, end: 'Enter' })
                .then(() => out({ seen, prevented }));
            """ % (json.dumps(BATCH), _keys("1212121212121")))
        self.assertEqual(got["seen"], [], "repeat 标志没挡住 · 只剩速度一条判据")
        self.assertEqual(got["prevented"], 0)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class HeldKeyOutsideAnyFieldTests(unittest.TestCase):
    """反证 3b · 按住一个键不放,而焦点【不在任何框里】—— 收银主屏的常态。

    上面三条全拿 field(...) 当靶子,于是验的一直是「落进声明接枪的框」那半条路;框外
    finalize 直接把码发出去,repeat / hasTwoDistinct 一次都不被问到。台式收银上东西压住一个
    键、枪的触发键卡住都走这里(真 Chromium 实测:12 发 autoRepeat '0' @25ms 再蹭到 '5''7',
    事件戳最大间隔 34.6ms —— 速度这条判据是站在错的一边的)。

    这一组同时钉反向:框外的真枪(收银主屏扫码是主路径)不许被这条误伤。
    """

    def test_autorepeat_outside_any_field_is_not_a_scan(self):
        got = _run("""
            burst(%s, BODY, 25, { repeat: true })
                .then(() => settle(() => ({ seen, typed, prevented })));
            """ % _keys(HELD_KEYS))
        self.assertEqual(got["seen"], [], "收银主屏压住一个键不放被当成扫了一件货")
        self.assertEqual(got["typed"], [], "框外没人在打字 · 不该拿 onTyped 顶一句")

    def test_one_repeated_character_outside_any_field_is_not_a_scan(self):
        # repeat 拿不到的环境(合成事件 / 老浏览器):整串就一个字符这条物理事实要顶上。
        got = _run("""
            burst(%s, BODY, 25, { end: 'Enter' })
                .then(() => out({ seen, prevented }));
            """ % _keys("0" * 13))
        self.assertEqual(got["seen"], [], "整串一个字符在框外被当成条码")
        self.assertEqual(got["prevented"], 0, "不是扫码却把回车吃了 · 表单会被顺手提交")

    def test_the_same_string_is_refused_in_a_field_and_outside_it(self):
        # 「按住一个键不放」是物理事实,跟落在哪儿无关。同一串两处结论必须一样 —— 不一样就
        # 说明这条判据又只挂在一半路上了(本轮之前正是:框里挡,框外放行)。
        got = _run("""
            const run = async () => {
                // 两串都拿 Enter 收尾:不给结束键就要等 150ms 计时器,而 out() 不等它 ——
                // 那样两边都读到 0,这条断言在坏引擎上照样绿(它自己就成了假绿)。
                const box = field(%s, '');
                await burst(%s, box, 25, { repeat: true, end: 'Enter' });
                const inBox = seen.length;
                await burst(%s, BODY, 25, { repeat: true, end: 'Enter' });
                out({ inBox, outside: seen.length - inBox });
            };
            run();
            """ % (json.dumps(BATCH), _keys(HELD_KEYS), _keys(HELD_KEYS)))
        self.assertEqual([got["inBox"], got["outside"]], [0, 0], "框内框外两个结论 · 判据挂了一半")

    def test_a_real_gun_outside_any_field_still_scans(self):
        # 反向:收银主屏(焦点在 body)扫码是整个功能的主路径。把它弄坏了,前面几条全白搭。
        for gap in (5, 8, 20, 49, 70, 140):
            with self.subTest(gapMs=gap):
                got = _run("""
                    burst(%s, BODY, %d, { end: 'Enter' })
                        .then(() => out({ seen, prevented }));
                    """ % (_keys(COKE), gap))
                self.assertEqual(
                    [s["code"] for s in got["seen"]], [COKE], f"{gap}ms/字符的真枪在框外被丢了"
                )
                self.assertEqual(got["prevented"], 1, "枪的回车没吃掉")

    def test_a_gun_code_with_one_repeated_run_outside_still_scans(self):
        # 真码里有连着的重复位(8850999320014 有三个 9、两个 0)—— 挡的是「整串一个字符」,
        # 不是「有重复字符」。把这条写宽一点,库里一半的码就扫不出来了。
        got = _run("""
            burst(%s, BODY, 8, { end: 'Enter' })
                .then(() => out({ seen }));
            """ % _keys(OLD_CODE))
        self.assertEqual([s["code"] for s in got["seen"]], [OLD_CODE], "带重复位的真码被挡了")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class CrossBoundaryBurstTests(unittest.TestCase):
    """② 一串枪从框外开头、结尾落进声明接枪的框。

    产品自己制造这个场景:命中后 qty.focus()(inventory-scan.ts)。枪比网络快,第一箱的查码
    应答在第二串打到一半时回来,后半串就落进数量框。快照只在本串第一个键上取时 info.field
    停在 false —— looksLikeGun 不判、restoreField 不还原,两道保护同时失效而码照旧发出去查:
    数量框从 1 变成 1234567894 跟着整张收货单提交,手机端那列只有 72px,屏上只看得见头几位。

    规矩定成:碰过任何一个框就按框里那套判,认成枪扫再把碰过的框逐个还原。
    """

    def test_gun_that_lands_in_the_qty_box_midway_restores_it_and_still_scans(self):
        got = _run("""
            const qty = field(%s, '1');
            burst(%s, BODY, 8, { jump: { at: 4, to: qty }, end: 'Enter' })
                .then(() => out({ seen, prevented, qty: qty.value }));
            """ % (json.dumps(QTY), _keys(COKE)))
        self.assertEqual(got["qty"], "1", f"数量框成了 {got['qty']} · 这一单要按它入库")
        self.assertEqual([s["code"] for s in got["seen"]], [COKE], "跨界那一串没发出去查")
        self.assertTrue(got["seen"][0]["info"]["field"], "碰过框却报 field=false · 使用方无从判起")
        self.assertEqual(got["prevented"], 1, "枪的回车没吃掉 · 半张入库单会被顺手提交")

    def test_focus_moved_inside_one_keys_dispatch_still_snapshots_before_the_character(self):
        # 光标在某一发的派发中途被挪走(产品在 keydown 处理器里挪就是这样):那一发的 target
        # 还是旧框,字符却落进新框。只认 keydown 会把新框的头一个字符漏在快照外面 —— 还原成
        # 「1 加一位」照样是错的数量。焦点那一刻的 focusin 才是干净的取样点。
        got = _run("""
            const qty = field(%s, '1');
            burst(%s, BODY, 8, { jump: { at: 4, to: qty, inDispatch: true }, end: 'Enter' })
                .then(() => out({ seen, qty: qty.value }));
            """ % (json.dumps(QTY), _keys(COKE)))
        self.assertEqual(got["qty"], "1", f"数量框剩下 {got['qty']} · 快照晚了一个字符")
        self.assertEqual([s["code"] for s in got["seen"]], [COKE])

    def test_a_burst_crossing_two_boxes_restores_both(self):
        # 一串横跨两个框(上一件的数量框 → 下一行的批号框)。只还原最后那个 = 前一个框留着
        # 半截码,而它同样跟着整张收货单提交。
        got = _run("""
            const qty = field(%s, '24');
            const lot = field(%s, %s);
            burst(%s, qty, 8, { jump: { at: 6, to: lot }, end: 'Enter' })
                .then(() => out({ seen, qty: qty.value, lot: lot.value }));
            """ % (json.dumps(QTY), json.dumps(BATCH), json.dumps(LOT), _keys(COKE)))
        self.assertEqual(got["qty"], "24", f"数量框成了 {got['qty']}")
        self.assertEqual(got["lot"], LOT, f"批号框成了 {got['lot']}")
        self.assertEqual([s["code"] for s in got["seen"]], [COKE])

    def test_a_slow_crossing_burst_is_handed_back_to_the_human_with_the_right_snapshot(self):
        # 跨界不改判据的方向:慢串照旧当人在打字(不回调、不动框),但那一声必须带【落点那个
        # 框】的扫前内容 —— 店员点「这是扫的」时 useTyped 拿它还原,给错框就是把别处的内容
        # 写进数量框。
        got = _run("""
            const qty = field(%s, '1');
            burst(%s, BODY, 120, { jump: { at: 4, to: qty }, end: 'Tab' })
                .then(() => out({ seen, typed, prevented, qty: qty.value }));
            """ % (json.dumps(QTY), _keys(COKE)))
        self.assertEqual(got["seen"], [], "120ms/字符的跨界串被当成枪扫抢走了")
        self.assertEqual(got["prevented"], 0, "人手打的 Tab 被吃掉 · 焦点走不了")
        self.assertEqual(
            [t["before"] for t in got["typed"]], ["1"], "onTyped 给的不是落点框的扫前值"
        )
        self.assertEqual([t["field"] for t in got["typed"]], [True], "跨界那一串报了 field=false")

    def test_a_held_key_that_crosses_into_a_box_is_not_a_scan(self):
        # 两条毛病叠一块:框外按住键不放,中途光标被塞进数量框。任一条判据挂了都会发出去查。
        got = _run("""
            const qty = field(%s, '1');
            burst(%s, BODY, 25, { repeat: true, jump: { at: 4, to: qty } })
                .then(() => settle(() => ({ seen, qty: qty.value })));
            """ % (json.dumps(QTY), _keys(HELD_KEYS)))
        self.assertEqual(got["seen"], [], "按住一个键不放跨进数量框后被当成扫码")

    def test_no_delivered_burst_ever_leaves_a_box_it_touched_dirty(self):
        """钉的是状态本身,不是某一个场景:凡是发出去查了的那一串,它碰过的每个框都必须回到
        扫之前。四轮的病根正是「只量了一侧」—— 这条把两侧绑在同一个断言里。"""
        got = _run("""
            const run = async () => {
                const rows = [];
                const cases = [
                    ['inBoxOnly', null, false],
                    ['startsOutside', 4, false],
                    ['jumpInDispatch', 4, true],
                    ['jumpAtLastKey', 12, false],
                ];
                for (const [name, at, inDispatch] of cases) {
                    const qty = field(%s, '7');
                    const before = seen.length;
                    const opts = { end: 'Enter' };
                    if (at === null) {
                        await burst(%s, qty, 8, opts);
                    } else {
                        opts.jump = { at, to: qty, inDispatch };
                        await burst(%s, BODY, 8, opts);
                    }
                    rows.push({ name, delivered: seen.length - before, qty: qty.value });
                }
                out({ rows });
            };
            run();
            """ % (json.dumps(QTY), _keys(COKE), _keys(COKE)))
        for row in got["rows"]:
            with self.subTest(case=row["name"]):
                self.assertEqual(row["delivered"], 1, "这一串没发出去查 · 反向被弄坏了")
                self.assertEqual(row["qty"], "7", f"发出去查了,数量框却留着 {row['qty']}")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class HumanTypingDateTests(unittest.TestCase):
    """反证 4 · 人手中速填日期(三轮实测 100ms / 120ms 当场破:框被清空 + 真发出一次查码)。"""

    SPEEDS = [100, 120, 140, 180, 260]
    WRITINGS = ["20271231", "2027/12/31", "31122027"]

    def test_hand_typed_dates_stay_in_the_expiry_field(self):
        for text in self.WRITINGS:
            for gap in self.SPEEDS:
                with self.subTest(text=text, gapMs=gap):
                    got = _run("""
                        const box = dateField(%s, '');
                        burst(%s, box, %d, { end: 'Tab' })
                            .then(() => out({ seen, prevented, typed: box.typed }));
                        """ % (json.dumps(EXPIRY), _keys(text), gap))
                    self.assertEqual(got["seen"], [], f"人手打的 {text}@{gap}ms 被当成扫码抢走")
                    self.assertEqual(got["prevented"], 0, "人手打的 Tab 被吃掉 · 焦点走不了")
                    self.assertEqual(got["typed"], text, "串没打进框 · 这轮不作数")

    def test_hand_typed_date_into_an_already_filled_expiry_is_left_alone(self):
        # 改效期是店员的日常动作:框里本来就有值,新值也得原样留下。
        got = _run("""
            const box = dateField(%s, '2027-12-31', '2028-11-30');
            burst(%s, box, 120, { end: 'Tab' })
                .then(() => out({ seen, value: box.value, typed: box.typed }));
            """ % (json.dumps(EXPIRY), _keys("20281130")))
        self.assertEqual(got["seen"], [], "人手改效期被当成扫码")
        self.assertEqual(got["value"], "2028-11-30", "楔子把人手刚改好的效期还原回旧值了")

    def test_a_residue_only_a_machine_could_leave_does_not_make_it_a_machine(self):
        """真 Chromium 实测:人手 120ms/字符打 20271231,日期控件留下 202712-03-01。

        「残渣不像 yyyy-mm-dd 就是机器打的」这条代理判据在这里方向是反的 —— 它把店员
        填的效期判成扫码,整框抹掉再发一次查码。这条钉住:判据不许看残渣。
        """
        got = _run("""
            const box = dateField(%s, '', '202712-03-01');
            burst(%s, box, 120, { end: 'Tab' })
                .then(() => out({ seen, prevented, value: box.value }));
            """ % (json.dumps(EXPIRY), _keys("20271231")))
        self.assertEqual(got["seen"], [], "残渣不像日期就判成机器 · 店员填的效期被抹掉了")
        self.assertEqual(got["value"], "202712-03-01", "楔子动了人手填进去的内容")
        self.assertEqual(got["prevented"], 0)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class DoNotOverCorrectTests(unittest.TestCase):
    """反证 5 · 防修过头:真枪 5ms/字符打进已填好的框,原内容原样还回、码落成一行。"""

    def test_gun_into_a_filled_expiry_restores_the_date_and_delivers_one_code(self):
        # 残渣用实测值 2027-12-14:枪把 13 位码打进已填 2027-12-31 的框,控件留下的是一个
        # 合法日期。看残渣的判据在这里会判成人手 → 效期被悄悄改成 12-14 且扫码凭空消失。
        got = _run("""
            const box = dateField(%s, '2027-12-31', '2027-12-14');
            burst(%s, box, 5, { end: 'Enter' })
                .then(() => out({ seen, prevented, value: box.value, typed: box.typed }));
            """ % (json.dumps(EXPIRY), _keys(COKE)))
        self.assertEqual([s["code"] for s in got["seen"]], [COKE], "枪扫进效期框被吞了")
        self.assertEqual(got["typed"], COKE, "串没真打进框 · 这轮证明不了还原")
        self.assertEqual(got["value"], "2027-12-31", "店员填好的效期被扫码抹掉了")
        self.assertEqual(got["prevented"], 1, "枪的回车没吃掉 · 半张入库单会被顺手提交")

    def test_gun_into_a_filled_barcode_field_does_not_concatenate(self):
        # 三轮真打穿的那一条:新码接在旧码后面凑成 26 位,还回绿字「没人用这个码」。
        got = _run("""
            const box = field(%s, %s);
            burst(%s, box, 5, { end: 'Enter' })
                .then(() => out({ seen, value: box.value }));
            """ % (json.dumps(BARCODE), json.dumps(OLD_CODE), _keys(COKE)))
        self.assertEqual([s["code"] for s in got["seen"]], [COKE])
        self.assertEqual(got["value"], OLD_CODE, f"框里成了新旧相接的一串: {got['value']}")
        self.assertNotIn(OLD_CODE + COKE, got["value"])

    def test_gun_into_a_filled_qty_field_restores_the_typed_quantity(self):
        # 入库改数量:店员打了 24 再扫下一箱,24 不能被扫码顺手改掉。
        got = _run("""
            const box = field(%s, '24');
            burst(%s, box, 5, { end: 'Tab' })
                .then(() => out({ seen, value: box.value }));
            """ % (json.dumps(QTY), _keys(COKE)))
        self.assertEqual([s["code"] for s in got["seen"]], [COKE])
        self.assertEqual(got["value"], "24", "店员填的数量被扫码接成了一串")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class NoContentShapedProxyTests(unittest.TestCase):
    """判据里不许再出现「内容长得像什么」的代理判据。

    实测过一次:拿「框里残渣像不像 yyyy-mm-dd」当判据,人手 120ms 打的 20271231 在真
    Chromium 里留下 202712-03-01(判成机器),而枪打进已填 2027-12-31 的框留下 2027-12-14
    ——一个合法日期(判成人)。方向刚好反过来,错的那一半是静默改效期。
    """

    def test_same_cadence_same_verdict_no_matter_what_residue_is_left(self):
        # 同一串、同一节拍,只把残渣换掉:结论必须一模一样。变了就说明残渣在参与判断。
        got = _run("""
            const run = async () => {
                const verdicts = {};
                for (const [name, residue] of [
                    ['messy', '202712-03-01'], ['legal', '2027-12-14'], ['empty', ''],
                ]) {
                    const box = dateField(%s, '', residue);
                    const before = seen.length;
                    await burst(%s, box, 120, { end: 'Tab' });
                    verdicts[name] = seen.length - before;
                }
                const gunBox = dateField(%s, '', '2027-12-14');
                const before = seen.length;
                await burst(%s, gunBox, 5, { end: 'Enter' });
                verdicts.gunSpeed = seen.length - before;
                out(verdicts);
            };
            run();
            """ % (json.dumps(EXPIRY), _keys("20271231"), json.dumps(EXPIRY), _keys("20271231")))
        self.assertEqual(
            [got["messy"], got["legal"], got["empty"]],
            [0, 0, 0],
            "换个残渣结论就变了 · 判据在看内容长得像什么",
        )
        # 同一串在枪速下必须判成枪 —— 否则上面三个 0 只是「什么都不发」,证明不了区分力。
        self.assertEqual(got["gunSpeed"], 1, "枪速下也不发 · 这组断言没有区分力")

    def test_judgement_signature_takes_only_measured_facts(self):
        # 判据只吃 {gap, repeat};多一个 machine / value / type 这类字段就是代理判据回来了。
        # heldKey 一起看:结论是 looksLikeGun 给的,但它把一半判据委托了出去 —— 只盯委托方
        # 等于给代理判据留了个后门,而「闸只看了一半」正是这批反复栽的地方。
        src = WEDGE.read_text(encoding="utf-8")
        for fn in ("looksLikeGun", "heldKey"):
            body = src.split("function " + fn)[1].split("\n    }")[0]
            for banned in ("machine", ".value", ".type", "test("):
                self.assertNotIn(banned, body, f"{fn} 里出现了 {banned} · 代理判据回来了")


if __name__ == "__main__":
    unittest.main()
