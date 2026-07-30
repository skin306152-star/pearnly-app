#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""建品表单条码位(src/home/sales-products*.ts)· 反证测试。

这一批的 P0/P1 全在静态断言照不到的地方,所以主力是 _sales_products_dom 那套真 node harness:
产品源码真跑一遍,断言对象是它自己导出的函数和自己 innerHTML 里的 id,不造产品里不存在的对象。

各条覆盖的失败场景(把修复回退掉,对应用例必红):
  · P0-B 楔子碎片整框覆盖 —— 人在框里手打 EAN-13,楔子按 150ms 静默把它切成几发送回来,
    够 8 位又不是前缀的那几发把框整个盖掉,最后只剩一段,状态行还绿着说没人用。存下去
    POS 永远扫不出这件货。切法由停顿落在哪决定,不由印刷分组决定,所以这里按真实时间线
    喂尾段/中段各种切法(只喂官方分组 8/850999/320014 会全绿 —— 上一轮就是这么漏掉的)。
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

DUP_PRODUCT = {"id": "p-cola", "name_th": "โค้ก", "unit_price": 15}


def _js(value) -> str:
    return json.dumps(value, ensure_ascii=False)


CODE13 = "8850999320014"

# 人在条码框里手打 EAN-13,楔子会按 150ms 静默把它切成几发送过来 —— 切在哪由停顿落在哪决定,
# 不由条码的印刷分组决定。这几种切法都是真人打字打得出来的:
#   前两条 + 第三条是审查方在真 harness 上跑出来的复现(碎片是框里那串的【尾段】);
#   第四条切出一个 8 位的【中段】(既不是前缀也不是后缀);
#   最后一条是官方印刷分组 8/850999/320014 —— 上一轮唯一验过的那种,留着防回归。
# 只验最后一条会全绿:它的第一发恰好等于框里已有的整串,前缀规则正好盖住。
TYPING_SPLITS = [
    ["8850", "999320014"],
    ["885", "0999320014"],
    ["88509", "99320014"],
    ["88", "50999320", "014"],
    ["8", "850999", "320014"],
]


class WedgeFragmentTests(unittest.TestCase):
    """P0-B · 楔子送来的碎片不许把框里手打好的位数吃掉。"""

    @classmethod
    def setUpClass(cls):
        # 一个 node 进程里按真实时间线跑完全部切法(判据本身就是时间语义,计时器不许换假的)
        cls.typed = run(SETUP + """
        (async () => {
            await openCreateForm('0000000000000');
            const splits = %s;
            const res = [];
            for (const chunks of splits) {
                field().value = '';
                await sleep(450);        // 让上一轮 400ms 防抖查重落地,别串味
                calls.length = 0;
                await typeHuman(chunks);
                await sleep(450);        // 打完这一串,防抖该查一次 —— 查的必须是整串
                res.push({ value: field().value, looked: calls.map((c) => c.url) });
            }
            out({ res });
        })();
        """ % _js(TYPING_SPLITS))

    def test_typed_ean13_survives_every_wedge_split(self):
        for chunks, got in zip(TYPING_SPLITS, self.typed["res"]):
            with self.subTest(split="/".join(chunks)):
                # 老行为:够 8 位又不是前缀的碎片整框覆盖 → 框里只剩最后那一段
                self.assertEqual(got["value"], CODE13, "手打的位数被碎片吃掉了")

    def test_no_fragment_is_ever_looked_up(self):
        """碎片各查一次 = 状态行拿半截码说「没人用这个码」,而那半截本来就没人用。"""
        want = ["/api/sales/products/lookup?barcode=" + CODE13]
        for chunks, got in zip(TYPING_SPLITS, self.typed["res"]):
            with self.subTest(split="/".join(chunks)):
                self.assertEqual(got["looked"], want)

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

    def test_gun_speed_ruler_comes_from_the_wedge_not_a_hand_copy(self):
        """速度上限手抄一份就会漂:把楔子的 GUN_MAX_GAP_MS 收紧到 1ms,同一发慢枪就不该再算枪。"""
        res = run(SETUP + """
        (async () => {
            await openCreateForm('0000000000000');
            window.PearnlyScanWedge.GUN_MAX_GAP_MS = 1;
            field().value = 'OLD';
            await sleep(450);
            gunIntoField('8850999320014', 3);
            await tick();
            out({ value: field().value });
        })();
        """)
        self.assertEqual(res["value"], "OLD8850999320014", "尺子是写死的 50,不是楔子那份")


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
            "GUN_MAX_GAP_MS",  # 枪速判据(碎片不许整框覆盖)
            "sx-p-noprice",  # 没设价不画成 ฿0.00
        )
        for marker in markers:
            self.assertIn(marker, dist, f"{marker} 没进 dist/main.js")


if __name__ == "__main__":
    unittest.main()
