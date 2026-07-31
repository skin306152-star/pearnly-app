#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""建品表单条码位(src/home/sales-products*.ts)· 反证测试。

这一批的 P0/P1 全在静态断言照不到的地方,所以主力是 _sales_products_dom 那套真 node harness:
产品源码真跑一遍,断言对象是它自己导出的函数和自己 innerHTML 里的 id,不造产品里不存在的对象。

各条覆盖的失败场景(把修复回退掉,对应用例必红):
  · P0-B 人手打字被当成扫码 —— 判据只有一份,在楔子里(static/scan/scan-wedge.js),所以
    RealWedgeInTheBarcodeFieldTests 装的是楔子本体,不是喂桩回调:楔子发一发过来,建品表单
    就整框覆盖(那是扫码唯一的正当用途),于是「会不会发过来」才是真判据。前提取【框里已有
    码】那一档 —— 这个表单本来就是带码预填开出来的,空框被覆盖没有代价,已有码被覆盖就是
    店员手打的那串当场消失。人手 80ms/字符一发都不许发出来,枪 8ms/字符必须发出来并整框换
    掉,两条方向相反,少一条就能靠"永远不回调/永远回调"蒙混过关。
  · P1-F 贴码即点保存绕过查重 —— 查重是 400ms 防抖 + 异步,save() 不等它就等于放行,
    同一个码落两个商品,POS 扫出来永远是先建的那个。
  · P1-D 跨页带码桥 —— overlay 模式必须原地叠开,跳页会把半张入库单丢掉;开不出来要如实回 false。
  · P1-J 单位码口径 —— 后端信封是 matched_by/matched_unit,读错字段名 = 单位码那句话一次都不显示。
  · P2-5/P2-9 取景框 —— 比例必须从引擎 cropRatio 现算(手抄必漂),边框在暗色主题下要看得见。
"""

import json
import os
import re
import unittest

from tests.unit._sales_products_dom import run

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _read(*parts: str) -> str:
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def _luminance(hex_value: str) -> float:
    """WCAG 相对亮度(sRGB)。"""
    h = hex_value.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    chans = []
    for i in (0, 2, 4):
        c = int(h[i : i + 2], 16) / 255
        chans.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * chans[0] + 0.7152 * chans[1] + 0.0722 * chans[2]


# 每个场景都从这里起步:装楔子桩 → 真开建品表单 → 拿到产品自己渲染的条码框。
# wedgeCb 是产品自己注册进来的那只回调,喂它 = 走真的 onWedge → applyCode。
SETUP = """
let wedgeCb = null;
let wedgeExclusive = null;
window.PearnlyScanWedge = {
    register(cb, opts) {
        wedgeCb = cb;
        wedgeExclusive = !!(opts && opts.exclusive);
        return () => { if (wedgeCb === cb) { wedgeCb = null; wedgeExclusive = null; } };
    },
};
loadProducts();
const field = () => document.getElementById('sx-pf-barcode');
const stateHtml = () => document.getElementById('sx-pf-bc-state').innerHTML;
const mask = () => document.getElementById('sales-prod-mask');
const wrote = () => calls.filter((c) => c.method === 'POST' || c.method === 'PATCH').length;
// 一个字符落进框 = 浏览器插入 + 发 input 事件,产品的 oninput 就挂在这上面
function keyIn(ch) { field().value += ch; field().oninput(); }
// 人手打字:块内 80ms/字符(高于枪速上限 50、低于楔子 MAX_GAP_MS 150 → 块内不被切开)
async function typeHuman(chunks) {
    for (const chunk of chunks) {
        for (const ch of chunk) { await sleep(80); keyIn(ch); }
        await sleep(170);                 // 超过 MAX_GAP_MS → 楔子把这一块当"一发"吐回来
        wedgeCb(chunk, field());
    }
}
// 条码枪打进条码框:光标在框里,字符照旧落进框(楔子只吃末尾那个 Enter)
function gunIntoField(code, gapMs) {
    for (const ch of code) { if (gapMs) spin(gapMs); keyIn(ch); }
    wedgeCb(code, field());
}
// 条码枪:光标不在条码框里,按键被楔子截走,框里什么都没落
const gunElsewhere = (code) => wedgeCb(code, document.getElementById('sx-p-save'));
async function openCreateForm(seed) {
    const ok = window.openProductFormWithBarcode(seed, { overlay: true });
    await tick();
    return ok;
}
"""

# 装真楔子的那一套:不注册桩订阅者,让产品自己去 window.PearnlyScanWedge 拿真的那一份。
# applied 记的是【真楔子真发出来的每一发】—— 判据是"有没有发生",不是"发生了怎么办"。
SETUP_REAL_WEDGE = """
installRealWedge();
const applied = [];
const realRegister = window.PearnlyScanWedge.register;
window.PearnlyScanWedge.register = (cb, opts) =>
    realRegister((code, target, info) => { applied.push(code); return cb(code, target, info); }, opts);
loadProducts();
const field = () => document.getElementById('sx-pf-barcode');
async function openCreateForm(seed) {
    const ok = window.openProductFormWithBarcode(seed, { overlay: true });
    await tick();
    return ok;
}
"""

DUP_PRODUCT = {"id": "p-cola", "name_th": "โค้ก", "unit_price": 15}


def _js(value) -> str:
    return json.dumps(value, ensure_ascii=False)


CODE13 = "8850999320014"

# 人在条码框里手打字的速度。真机实测 100~260ms/字符;取 80ms 是【最快的那一档人手】——
# 比典型值快得多,离枪速上限(50ms)最近。慢慢打的那种永远绿,验它等于没验。
HUMAN_GAP_MS = 80
# 带 intercharacter delay 的慢枪。理想枪是 0ms,判据得是个区间不是个点。
GUN_GAP_MS = 8
# 蓝牙 HID / 带 transmit delay 的枪的常见节拍:> GUN_MAX_GAP_MS(50)攒得成串但判不成枪速,
# < MAX_GAP_MS(150)楔子仍然认下这一整串 —— 这一段正是引擎自己承诺要出声的那个区间。
SLOW_GUN_GAP_MS = 80

# 建品表单是【带码预填】开出来的(别处扫到未建档的码 → 「去建这个商品」),所以
# 「框里已有内容」才是这个表单的常态,空框那一档反倒是少数。病灶只在有内容那一档出现:
# 覆盖一个空框没有代价,覆盖一个已有码的框 = 店员手打的那串当场消失。
PREFILLED = "9876543210987"


class RealWedgeInTheBarcodeFieldTests(unittest.TestCase):
    """P0-B · 装【真楔子】(static/scan/scan-wedge.js 本体)跑一遍,不是喂桩回调。

    上一版这几条是拿桩楔子直接把碎片喂给建品表单,断言表单自己把碎片挡掉 —— 那是在验
    「消费方自带的第二把尺子」。尺子现在只剩一把、在楔子里(消费方拿到回调就是拿到结论),
    于是那些用例既红又没意义:它们要求产品防住一件真楔子根本不会做的事。

    换掉之后判据是【真楔子在这个真表单上会不会发出回调】:
      · 人手打字(80ms/字符,最快的那一档)—— 一发都不许发出来,框里的字一个不许少;
      · 枪扫(8ms/字符)—— 必须发出来,而且整框换成新码。
    两条方向相反,少一条就能靠「永远不回调」或「永远回调」蒙混过关。
    """

    @classmethod
    def setUpClass(cls):
        cls.res = run(SETUP_REAL_WEDGE + """
        (async () => {
            const res = {};
            // ① 人手在【已有码】的框里改码:楔子不该插手,一个字符都不许丢
            await openCreateForm(%(pre)s);
            field().focus();
            calls.length = 0;
            await typeAt('8850999320014', field(), %(human)d);
            await sleep(260);            // 过了楔子的 150ms 收尾窗口
            res.human = { value: field().value, callbacks: applied.slice() };
            await sleep(450);            // 手打的 400ms 防抖查重落地
            res.humanLooked = calls.map((c) => c.url).filter((u) => u.indexOf('lookup') >= 0);

            // ② 同一个框、同样已有码,这回是枪:必须整框换成新码
            // 重开表单即换一份订阅(bindBarcodeField 头一句就是 releaseBarcodeField)
            await openCreateForm(%(pre)s);
            field().focus();
            calls.length = 0;
            applied.length = 0;
            await typeAt('8850999320014', field(), %(gun)d);
            press('Enter', field(), 9999);
            await sleep(60);
            res.gun = { value: field().value, callbacks: applied.slice() };
            res.gunLooked = calls.map((c) => c.url).filter((u) => u.indexOf('lookup') >= 0);
            out(res);
        })();
        """ % {"pre": _js(PREFILLED), "human": HUMAN_GAP_MS, "gun": GUN_GAP_MS})

    def test_human_typing_never_reaches_the_form(self):
        """楔子发一发过来,建品表单就会整框覆盖(那是扫码唯一的正当用途)。所以判据得挡在
        楔子那一层:人手打字期间一发都不许发出来。发了 = 框里的码被自己打的半截盖掉。"""
        self.assertEqual(self.res["human"]["callbacks"], [], "人手打字被当成扫码发过来了")

    def test_every_digit_the_human_typed_is_still_in_the_field(self):
        """框里已有码这一档才有代价:预填的 13 位 + 手打的 13 位都得在。"""
        self.assertEqual(self.res["human"]["value"], PREFILLED + CODE13, "手打的位数被吃掉了")

    def test_no_half_code_is_ever_looked_up_while_typing(self):
        """拿半截码去查重,状态行会绿着说「没人用这个码」—— 那半截本来就没人用。"""
        for url in self.res["humanLooked"]:
            with self.subTest(url=url):
                self.assertIn(PREFILLED + CODE13, url, "查的是半截码")

    def test_a_real_gun_burst_replaces_the_prefilled_code(self):
        """反方向:挡人手不许把真枪也挡掉。框里有旧码时整框换成新码,才是覆盖的正当用途。"""
        self.assertEqual(self.res["gun"]["callbacks"], [CODE13], "真枪扫没送到表单")
        self.assertEqual(self.res["gun"]["value"], CODE13, "枪扫没把旧码整框换掉")

    def test_the_gun_code_is_the_one_looked_up(self):
        want = "/api/sales/products/lookup?barcode=" + CODE13
        self.assertIn(want, self.res["gunLooked"])


class BurstJudgedAsTypingIsNotSilentTests(unittest.TestCase):
    """判成「人在打字」的那一发接在旧码后面时,屏上不许是一句绿色的「没人用这个码」。

    这是慢枪(蓝牙 HID / 带 transmit delay,真机常年 50~100ms/字符)那一档的代价:引擎
    在这一段【故意】偏向人手 —— 它与店员手打的节拍是叠着的,没有哪个阈值分得开。判错一半
    不是问题,判错之后没人知道才是:字符已经接在旧码后面凑成 26 位,400ms 的防抖照旧拿那条串
    去查重,回一句绿字。店员照那句话点保存,落库的条码 POS 永远扫不出这件货。
    真浏览器那一半在 scripts/_r3_slowgun_verify.cjs(真键盘节拍 + 真 CSS)。
    """

    @classmethod
    def setUpClass(cls):
        cls.res = run(SETUP_REAL_WEDGE + """
        // 断言对象是产品自己 innerHTML 出来的那段标记(harness 的元素表也是从它注册的)
        const stateHtml = () => document.getElementById('sx-pf-bc-state').innerHTML;
        const green = () => stateHtml().indexOf('sx-bc-ok') >= 0;
        // 只认【这一刻画出来的】那段标记:harness 的元素表是只加不删的,拿 getElementById
        // 问「按钮在不在」会问到上一例留下的那个节点 —— 那种绿正是本仓栽过的假绿
        const hasWayBack = () => stateHtml().indexOf('data-scan-typed') >= 0;
        (async () => {
            const res = {};
            // ① 慢枪接在预填的旧码后面:框里成了拼接串
            await openCreateForm(%(pre)s);
            field().focus();
            calls.length = 0;
            await typeAt(%(code)s, field(), %(slow)d);
            await sleep(260);
            await sleep(500);              // 让 400ms 防抖那次查重也落地
            res.stitched = {
                value: field().value,
                html: stateHtml(),
                green: green(),
                wayBack: hasWayBack(),
            };
            // ② 点那条回路:框还原成这一发之前的样子,再整框按这个码走
            if (hasWayBack()) document.getElementById('sx-bc-usetyped').onclick();
            await sleep(80);
            res.recovered = { value: field().value };
            res.lookedAfter = calls
                .map((c) => c.url)
                .filter((u) => u.indexOf('lookup') >= 0);

            // ③ 对照:同一发慢枪落进【空框】—— 框里的值就等于那个码,没有歧义,不许弹提示
            await openCreateForm('');
            field().value = '';   // harness 的元素表跨表单复用同一个节点,值不会自己归零
            field().focus();
            calls.length = 0;
            await typeAt(%(code)s, field(), %(slow)d);
            await sleep(260);
            await sleep(500);
            res.empty = { value: field().value, green: green(), wayBack: hasWayBack() };
            out(res);
        })();
        """ % {"pre": _js(PREFILLED), "code": _js(CODE13), "slow": SLOW_GUN_GAP_MS})

    def test_the_burst_really_stitched_onto_the_old_code(self):
        """前提:这一发确实把框写脏了。没写脏就没有歧义,下面几条也就没验到东西。"""
        self.assertEqual(self.res["stitched"]["value"], PREFILLED + CODE13)

    def test_no_green_line_blesses_the_stitched_string(self):
        self.assertFalse(
            self.res["stitched"]["green"],
            "屏上回了绿字 —— 那串 26 位的东西不是任何一个码,却被说成「可以用」",
        )

    def test_the_burst_is_shown_with_a_way_back(self):
        self.assertIn(CODE13, self.res["stitched"]["html"], "没把这一串摆出来,店员认不出是哪一发")
        self.assertTrue(self.res["stitched"]["wayBack"], "判错了却没给一点就补回来的路")

    def test_taking_the_way_back_restores_the_field_and_looks_up_that_code(self):
        self.assertEqual(self.res["recovered"]["value"], CODE13, "回路没把框补回来")
        self.assertIn(
            "/api/sales/products/lookup?barcode=" + CODE13,
            self.res["lookedAfter"],
            "框改好看了,查的却不是这个码",
        )

    def test_the_same_burst_into_an_empty_field_stays_quiet(self):
        """误报反证:空框那一档框里的值就等于那个码 —— 再弹提示只是噪音,绿字才是对的。"""
        self.assertEqual(self.res["empty"]["value"], CODE13)
        self.assertFalse(self.res["empty"]["wayBack"], "空框也弹提示 —— 手打录码会被这句话骚扰")
        self.assertTrue(self.res["empty"]["green"], "空框那一档的查重结果被一起压掉了")


class FormAppliesWhatTheWedgeSendsTests(unittest.TestCase):
    """消费方这一侧的契约:楔子发过来 = 结论已经下了,整框写进去 + 立刻查重。

    这里可以用桩楔子 —— 验的是「发过来之后怎么办」。上面那个类用真楔子验的是另一半:
    「到底会不会发过来」。两半合起来才是完整的一条链,少哪一半都能自圆其说。
    """

    def test_gun_scan_still_fills_the_field(self):
        """长度门槛不许把真枪扫也挡掉 —— 挡掉了这功能就白做。"""
        res = run(SETUP + """
        (async () => {
            await openCreateForm('0000000000000');
            field().value = '';
            calls.length = 0;
            gunElsewhere('8850999320014');
            await tick();
            out({ value: field().value, looked: calls.map((c) => c.url), exclusive: wedgeExclusive });
        })();
        """)
        self.assertEqual(res["value"], "8850999320014")
        self.assertEqual(res["looked"], ["/api/sales/products/lookup?barcode=8850999320014"])
        # 建品弹窗开着时枪只该喂这个框,底下页面的订阅者不该也吃一份
        self.assertTrue(res["exclusive"])

    def test_gun_burst_into_the_focused_field_wins(self):
        """光标就在条码框里时扫一枪:空框要填上,框里有旧码要整个换掉(整框覆盖唯一的正当用途)。

        3ms/字符 = 带 intercharacter delay 的慢枪,不是理想的 0ms —— 判据得是个区间不是个点。
        """
        res = run(SETUP + """
        (async () => {
            await openCreateForm('0000000000000');
            field().value = '';
            await sleep(450);
            calls.length = 0;
            gunIntoField('8850999320014', 0);       // 背靠背的快枪
            await tick();
            const fresh = { value: field().value, looked: calls.map((c) => c.url) };

            field().value = 'OLD-8851';             // 框里是上一件货的旧码
            await sleep(450);
            gunIntoField('8850999320014', 3);       // 3ms/字符的慢枪
            await tick();
            out({ fresh, replaced: field().value });
        })();
        """)
        self.assertEqual(res["fresh"]["value"], "8850999320014")
        self.assertEqual(
            res["fresh"]["looked"], ["/api/sales/products/lookup?barcode=8850999320014"]
        )
        self.assertEqual(res["replaced"], "8850999320014", "旧码没被换掉,存下去谁也扫不出")

    def test_the_form_keeps_no_ruler_of_its_own(self):
        """尺子只此一把,在楔子里。

        上一版这条是「把楔子的 GUN_MAX_GAP_MS 改成 1ms,消费方该跟着变」—— 那假设消费方自己
        也在按速度判一遍,正是三个消费方各写各的尺子那个病根。消费方现在拿到回调就是拿到结论,
        于是那条既红又是在要求一件不该发生的事。真正要防的是尺子被【抄】回来:抄一份就会漂,
        而漂了没有任何征兆(改楔子的人不知道这里还有一份)。所以判据换成"这里一份都不许有"。
        """
        src = _read("src", "home", "sales-products-scan.ts")
        for token in ("GUN_MAX_GAP_MS", "GUN_MIN_LENGTH", "burstIsGunSpeed", "info.gap", "MAX_GAP"):
            with self.subTest(token=token):
                self.assertNotIn(token, src, f"消费方又抄了一把尺子:{token}")
        # 只此一把的那份必须还在楔子里(闸不许因为楔子改名而静默失效)
        wedge = _read("static", "scan", "scan-wedge.js")
        self.assertIn("function looksLikeGun", wedge)
        self.assertIn("GUN_MAX_GAP_MS", wedge)


class SaveBlocksOnConflictTests(unittest.TestCase):
    """P1-F · 保存必须把查重推到落定再决定拦不拦。"""

    PASTE_THEN_SAVE = """
        (async () => {
            await openCreateForm('0000000000000');
            answer = () => %(reply)s;
            document.getElementById('sx-pf-th').value = 'ใหม่';
            field().value = '8850999320014';
            field().oninput();              // 贴码触发 400ms 防抖,不等它跑完
            %(wait)s
            calls.length = 0;
            await document.getElementById('sx-p-save').onclick();
            await tick();
            out({
                wrote: wrote(),
                looked: calls.filter((c) => c.method === 'GET').length,
                toast: toasts[toasts.length - 1] || null,
                open: !!mask() && mask().style.display === 'flex',
                state: stateHtml(),
            });
        })();
    """

    def _run(self, reply: str, wait: str = "") -> dict:
        return run(SETUP + self.PASTE_THEN_SAVE % {"reply": reply, "wait": wait})

    def test_paste_then_save_within_debounce_is_blocked(self):
        res = self._run(
            "reply({ product: %s, matched_by: 'product', matched_unit: null })" % _js(DUP_PRODUCT)
        )
        # 老行为:防抖没跑完 → checkState 'idle' → barcodeConflict() 为 null → 直接 POST 出去
        self.assertEqual(res["wrote"], 0, "撞码的商品被存下去了")
        self.assertEqual(res["looked"], 1, "保存时没有现查一次")
        self.assertEqual(res["toast"], ['sx-p-bc-dup|{"name":"โค้ก"}', "error"])
        self.assertTrue(res["open"], "拦下来了却把表单关了,人没法改")
        # 拦住之后必须给出路,不能只说「不行」
        self.assertIn("sx-p-bc-dup-open", res["state"])

    def test_save_while_check_in_flight_is_blocked(self):
        """checkState === 'checking' 时点保存同样不许放行。"""
        res = self._run(
            "new Promise((r) => setTimeout(() => r(reply("
            "{ product: %s, matched_by: 'product', matched_unit: null })), 40))" % _js(DUP_PRODUCT),
            wait="await new Promise((r) => setTimeout(r, 420));",
        )
        self.assertEqual(res["wrote"], 0, "查重在飞的时候点保存被放行了")
        self.assertEqual(res["toast"], ['sx-p-bc-dup|{"name":"โค้ก"}', "error"])

    def test_free_barcode_still_saves(self):
        """没撞码不许被拦 —— 拦错了等于建不了品。"""
        res = self._run("reply(null, 404)")
        self.assertEqual(res["wrote"], 1)

    def test_lookup_failure_does_not_block_save(self):
        """查不了 ≠ 撞码:凭一次网络失败拦住保存是撒谎(唯一约束在 DB 那层兜底)。"""
        res = self._run("reply({ detail: 'boom' }, 500)")
        self.assertEqual(res["wrote"], 1)


class UnitBarcodeCopyTests(unittest.TestCase):
    """P1-J · 命中的是箱码/瓶码时,话要说清是「哪个单位的码」。"""

    ENVELOPE = "reply({ product: %s, matched_by: 'unit', matched_unit: 'ลัง' })" % _js(DUP_PRODUCT)

    def test_unit_hit_says_which_unit_not_just_taken(self):
        res = run(SETUP + """
        (async () => {
            answer = () => %s;
            await openCreateForm('8850999320014');
            out({ state: stateHtml(), text: SCAN.barcodeConflictText() });
        })();
        """ % self.ENVELOPE)
        # 老行为读的是 d.unit.unit_name(后端从来没发过这个形状)→ 单位名恒空 → 落回含糊那句
        self.assertEqual(res["text"], 'sx-p-bc-dup-unit|{"name":"โค้ก","unit":"ลัง"}')
        self.assertIn("sx-p-bc-dup-unit", res["state"])
        self.assertIn("ลัง", res["state"])

    def test_own_unit_barcode_is_self_not_conflict(self):
        """撞码卡点「去编辑那个商品」→ 编辑态再扫它自己的箱码:是 self,不拦,且说清是哪个单位。"""
        res = run(SETUP + """
        (async () => {
            answer = () => %s;
            await openCreateForm('8850999320014');
            document.getElementById('sx-bc-goedit').onclick();   // 真按钮,产品自己渲染的 id
            await tick();
            gunElsewhere('8850999320014');
            await tick();
            document.getElementById('sx-pf-th').value = 'โค้ก';
            calls.length = 0;
            await document.getElementById('sx-p-save').onclick();
            await tick();
            out({ state: stateHtml(), conflict: SCAN.barcodeConflictText(), wrote: wrote() });
        })();
        """ % self.ENVELOPE)
        self.assertIn("sx-p-bc-self-unit", res["state"])
        self.assertIn("ลัง", res["state"])
        self.assertEqual(res["conflict"], "", "自己的码被当成撞码")
        self.assertEqual(res["wrote"], 1, "改自己的商品被自己的条码拦住了")

    def test_unit_copy_keys_exist_in_all_four_languages(self):
        i18n = _read("static", "i18n-data.js")
        for key in ("sx-p-bc-dup-unit", "sx-p-bc-self-unit"):
            self.assertEqual(i18n.count(f"'{key}'"), 4, f"{key} 四语没齐")
            for line in re.findall(rf"'{key}': ('.*?'|\".*?\")", i18n):
                self.assertIn("{unit}", line, f"{key} 少了 {{unit}} 占位")


class BridgeOverlayTests(unittest.TestCase):
    """P1-D · window.openProductFormWithBarcode(code, opts) 的契约。"""

    def test_overlay_opens_in_place_without_navigating(self):
        res = run(SETUP + """
        (async () => {
            const ok = await openCreateForm('8850999320014');
            out({ ok, routed, value: field() ? field().value : null,
                  open: !!mask() && mask().style.display === 'flex' });
        })();
        """)
        # 老实现是 routeTo('sales-products') 跳走,半张入库单连行一起丢
        self.assertEqual(res["routed"], [], "overlay 模式跳页了")
        self.assertTrue(res["ok"])
        self.assertTrue(res["open"], "overlay 模式没把建品表单叠出来")
        self.assertEqual(res["value"], "8850999320014")

    def test_without_overlay_routes_to_products_page_and_carries_code(self):
        res = run(SETUP + """
        (async () => {
            const ok = window.openProductFormWithBarcode('8850999320014');
            await tick();
            out({ ok, routed, pending: SCAN.takePendingBarcode(),
                  again: SCAN.takePendingBarcode() });
        })();
        """)
        self.assertTrue(res["ok"])
        self.assertEqual(res["routed"], ["sales-products"])
        self.assertEqual(res["pending"], "8850999320014")
        # 取一次即清:留着会让下次进商品页莫名再弹一次带旧码的表单
        self.assertEqual(res["again"], "")

    def test_returns_false_when_it_cannot_open(self):
        """打不开就如实说 —— 调用方(入库侧)靠这个回落成诚实文案,不许假装成功。"""
        res = run(SETUP + """
        (async () => {
            const empty = window.openProductFormWithBarcode('   ', { overlay: true });
            delete window.routeTo;
            const noRoute = window.openProductFormWithBarcode('8850999320014');
            out({ empty, noRoute });
        })();
        """)
        self.assertFalse(res["empty"])
        self.assertFalse(res["noRoute"])


class ViewfinderTests(unittest.TestCase):
    """P2-5 / P2-9 · 取景框比例跟引擎走,边框两套主题都看得见。"""

    @staticmethod
    def _engine_crop() -> tuple:
        engine = _read("static", "scan", "scan-camera.js")
        m = re.search(r"cropRatio:\s*\{\s*width:\s*([\d.]+),\s*height:\s*([\d.]+)\s*\}", engine)
        assert m, "scan-camera.js 的 cropRatio 读不到 · 闸失效"
        return float(m.group(1)), float(m.group(2))

    @staticmethod
    def _frame_rule() -> str:
        cam = _read("src", "home", "sales-products-scan-cam.ts")
        m = re.search(r"\.sx-bcm-frame\{([^}]*)\}", cam)
        assert m, ".sx-bcm-frame 规则读不到 · 闸失效"
        return m.group(1)

    def test_frame_is_painted_from_engine_crop_ratio(self):
        crop_w, crop_h = self._engine_crop()
        res = run(SETUP + """
        (async () => {
            window.PearnlyScanCamera = {
                unsupportedReason: () => null,
                ensureLoaded: async () => ({
                    create: () => ({
                        start: async () => true,
                        retry: async () => true,
                        destroy() {},
                        cropRatio: () => ({ width: %s, height: %s }),
                    }),
                }),
            };
            CAM.openScanModal(() => {}, () => {});
            await tick();
            const f = document.getElementById('sx-bcm-frame');
            out({ style: f ? f.style : null });
        })();
        """ % (crop_w, crop_h))
        # 老行为把 5%/25%/90%/50% 手抄进 CSS,元素上没有任何 inline 尺寸
        self.assertIsNotNone(res["style"], "取景框没画出来")
        self.assertEqual(
            sorted(res["style"]),
            ["height", "left", "top", "width"],
            "取景框没按引擎 cropRatio 现算位置 · 比例又回到手抄",
        )
        pct = {k: float(str(v).rstrip("%")) for k, v in res["style"].items()}
        self.assertAlmostEqual(pct["width"], crop_w * 100, places=6)
        self.assertAlmostEqual(pct["height"], crop_h * 100, places=6)
        self.assertAlmostEqual(pct["left"], (100 - crop_w * 100) / 2, places=6)
        self.assertAlmostEqual(pct["top"], (100 - crop_h * 100) / 2, places=6)

    def test_frame_css_carries_no_hand_copied_geometry(self):
        rule = self._frame_rule()
        for prop in ("width", "height", "left", "top"):
            self.assertNotRegex(
                rule, rf"(^|;)\s*{prop}\s*:", f"{prop} 又被手抄回 CSS 了 · 比例两处写必漂"
            )

    def test_frame_border_visible_on_camera_picture_in_both_themes(self):
        """压在摄像头画面上的框线要立得住:拿最暗的底(纯黑)量对比度,两套主题都得过 3:1。"""
        m = re.search(r"border:[^;]*var\(--([a-z0-9-]+)\)", self._frame_rule())
        self.assertIsNotNone(m, "取景框边框没走令牌 · 裸 hex 不认")
        token = m.group(1)
        base = _read("static", "home-01-base.css")
        dark_block = base.split(":root.dark {")[1]
        values = {
            "light": re.search(rf"--{token}:\s*(#[0-9A-Fa-f]{{3,6}})", base).group(1),
            "dark": re.search(rf"--{token}:\s*(#[0-9A-Fa-f]{{3,6}})", dark_block).group(1),
        }
        for theme, hex_value in values.items():
            ratio = (_luminance(hex_value) + 0.05) / 0.05
            # --accent-ink 暗夜是 #1D1438(近黑),量出来 1.2:1 —— 等于没画框
            self.assertGreaterEqual(
                ratio, 3.0, f"--{token} 在{theme}主题是 {hex_value},压在画面上看不见({ratio:.2f}:1)"
            )


class HonestStateTests(unittest.TestCase):
    """状态诚实 + 无残留 · 静态守门(行为由上面几组盖住)。"""

    @classmethod
    def setUpClass(cls):
        cls.src = _read("src", "home", "sales-products-scan.ts")
        cls.cam = _read("src", "home", "sales-products-scan-cam.ts")

    def test_only_404_counts_as_free(self):
        self.assertRegex(self.src, r"r\.status === 404\)\s*next = 'free'")
        self.assertRegex(self.src, r"catch \(_\) \{\s*next = 'error';")
        self.assertIn("let next: CheckState = 'error';", self.src)

    def test_stale_lookup_response_discarded(self):
        self.assertIn("const seq = ++checkSeq;", self.src)
        self.assertIn("if (seq !== checkSeq) return;", self.src)

    def test_release_stops_camera_and_unsubscribes_wedge(self):
        rel = self.src.split("export function releaseBarcodeField()")[1]
        self.assertIn("closeScanModal()", rel)
        self.assertIn("wedgeOff()", rel)
        self.assertIn("handle.destroy()", self.cam)

    def test_unsupported_hides_button_but_shows_reason(self):
        self.assertIn("insecure_context: 'bscan.err.insecure'", self.cam)
        self.assertRegex(self.src, r"const btn = why\s*\?\s*''")
        self.assertIn("t('sx-p-bc-gun')", self.src)

    def test_no_hardcoded_user_text_and_no_debug_residue(self):
        for name, src in (("scan", self.src), ("cam", self.cam)):
            code = "\n".join(ln for ln in src.split("\n") if not re.match(r"\s*(//|\*|/\*)", ln))
            quoted = re.findall(r"'([^'\n]*)'|\"([^\"\n]*)\"", code)
            cjk = [a or b for a, b in quoted if re.search(r"[一-鿿]", a or b)]
            self.assertEqual(cjk, [], f"{name} 写死的中文文案:{cjk}")
            self.assertNotIn("console.log", src)

    def test_dead_cross_document_handoff_key_is_gone(self):
        """没有任何一处写过它 —— 只读不写的跨文档键是死代码。"""
        self.assertNotIn("pearnly_new_product_barcode", self.src)


class BuiltBundleTests(unittest.TestCase):
    """改 src/** 必须把 dist 一起提交(prod 不重建 dist)。"""

    def test_main_bundle_carries_this_batch(self):
        dist = _read("static", "dist", "main.js")
        # 压缩会改写函数名,只挑改不掉的:i18n 键、DOM id、读楔子那个属性名
        markers = (
            "sx-pf-bc-scan",
            "sx-p-bc-dup-unit",
            "matched_unit",
            # 条码框声明接枪。原来钉的是 GUN_MAX_GAP_MS —— 那是消费方自带尺子时代的痕迹,
            # 尺子收归楔子之后 main.js 里本就不该再有它,钉着它等于钉一个该消失的东西。
            "data-enable-barcode",
            "sx-p-noprice",  # 没设价不画成 ฿0.00
        )
        for marker in markers:
            self.assertIn(marker, dist, f"{marker} 没进 dist/main.js")


if __name__ == "__main__":
    unittest.main()
