#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_inventory_scan_frontend.py

入库弹窗扫码加行(src/home/inventory-scan*.ts)的守门。

两层:
  1. 真 node 跑 TS(esbuild 现转,同 test_format_date_frontend 的招):落行判定 / 数量累加 /
     数量框里被枪写进去的码怎么摘回来 / 单位码信封 / 取景框几何。这几条是店员真实动作的判据
     ——「同一个码扫两次要落回同一行」错了就是一箱货加出十几行,而「批次品也合并」错了是
     第二箱的效期被悄悄换成第一箱的(POS 的 FEFO 与近效期告警从此按错日期算)。
  2. 接缝断言:扫码只挂在收货弹窗、数量框对枪 opt-in、查商品走既有 lookup 端点、
     批次显隐借 onProductChange 一套、带码建品走跨页带码桥的那个名字、关弹窗必放相机。
     这些跨文件约定 node 里跑不到,但漂了功能就是坏的(且都能在源里确定性地读出来)。
"""

from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOME_DIR = PROJECT_ROOT / "src" / "home"
SCAN_TS = HOME_DIR / "inventory-scan.ts"
UI_TS = HOME_DIR / "inventory-scan-ui.ts"
CAM_TS = HOME_DIR / "inventory-scan-camera.ts"
MODALS_TS = HOME_DIR / "inventory-modals.ts"
COMMON_TS = HOME_DIR / "inventory-common.ts"
# 桥的另一端(建品侧)· 被断言的名字必须来自真产物,不能是这份测试自己编的
BRIDGE_TS = HOME_DIR / "sales-products-scan.ts"
SCAN_CSS = PROJECT_ROOT / "static" / "home-58-inventory-scan.css"
CSS_BUILD = PROJECT_ROOT / "scripts" / "build-home-css.mjs"
DIST_MAIN = PROJECT_ROOT / "static" / "dist" / "main.js"

# 同级依赖里不参与判定的两个(网络 / 商品名本地化)用桩顶掉;扫码自己的三个模块真编译,
# 被验的是纯判定,不碰网络也不碰 DOM。
DRIVER = r"""
const esbuild = require('esbuild');
const fs = require('fs');
const path = require('path');
const dir = process.argv[1];
const STUB = { salesFetch: () => {}, salesErrMsg: () => '', localizedName: () => '' };
const cache = {};

function load(name) {
    if (cache[name]) return cache[name];
    const src = fs.readFileSync(path.join(dir, name + '.ts'), 'utf8');
    const { code } = esbuild.transformSync(src, { loader: 'ts', format: 'cjs' });
    const mod = { exports: {} };
    new Function('module', 'exports', 'require', code)(mod, mod.exports, (spec) => {
        const base = path.basename(spec).replace(/\.js$/, '');
        // inventory-common 真编译:效期判据(isPlausibleDate/isSaneExpiry)在这里,桩掉就没人验
        return /^inventory-(scan|common)/.test(base) ? load(base) : STUB;
    });
    cache[name] = mod.exports;
    return mod.exports;
}

const { planRow, bumpQty, stripScanned, acceptsCode, matchedUnit } = load('inventory-scan');
const { frameBox, notFoundHtml } = load('inventory-scan-ui');
const { isPlausibleDate, isSaneExpiry } = load('inventory-common');

let bad = 0;
function eq(got, want, msg) {
    const g = JSON.stringify(got), w = JSON.stringify(want);
    if (g !== w) { bad++; console.error('FAIL ' + msg + ' got=' + g + ' want=' + w); }
}
const row = (productId, unit) => ({ productId, unit: unit || '' });
const hit = (productId, unit, tracksBatch) => ({ productId, unit: unit || '', tracksBatch: !!tracksBatch });

// 落行:同商品先命中(不然一箱一箱扫会加出一堆重复行),没有才用空行,空行用完才追加
eq(planRow([row(''), row('')], hit('p1')), { kind: 'fill', index: 0 }, 'first scan fills the blank row');
eq(planRow([row('p1'), row('')], hit('p1')), { kind: 'bump', index: 0 }, 'same code again bumps that row');
eq(planRow([row('p1'), row('')], hit('p2')), { kind: 'fill', index: 1 }, 'new code takes the next blank');
eq(planRow([row('p1'), row('p2')], hit('p3')), { kind: 'append', index: -1 }, 'no blank left -> append');
eq(planRow([row('p1'), row('p2')], hit('p2')), { kind: 'bump', index: 1 }, 'bump wins over append');

// 批次品不许合并:一行只带一组批号/效期,第二箱(别的批号/效期)合进第一行 = 两箱全落在
// 第一箱那个效期下,FEFO 出货顺序与近效期告警从此按错日期算。宁可多一行让店员填这箱的。
eq(planRow([row('p-milk'), row('')], hit('p-milk', '', true)), { kind: 'fill', index: 1 },
   'batch item never bumps: second box gets its own row');
eq(planRow([row('p-milk'), row('p2')], hit('p-milk', '', true)), { kind: 'append', index: -1 },
   'batch item with no blank left -> append, still never bump');
eq(planRow([row('p-milk'), row('')], hit('p-milk', '', false)), { kind: 'bump', index: 0 },
   'non-batch item still merges (clerk scanning the same carton twice)');

// 箱码与瓶码是同一件货的两种入库单位:合并会把「1 箱」当成「1 瓶」入库
eq(planRow([row('p1', 'ลัง'), row('')], hit('p1', '')), { kind: 'fill', index: 1 },
   'a box line does not absorb a bottle scan');
eq(planRow([row('p1', 'ลัง'), row('')], hit('p1', 'ลัง')), { kind: 'bump', index: 0 },
   'same box code again bumps the box line');

// 命中的是哪个单位由后端答(matched_by/matched_unit · 与建品侧读同一份信封)
eq(matchedUnit({ product: { id: 'p1' }, matched_by: 'unit', matched_unit: 'ลัง' }), 'ลัง',
   'unit code hit carries the unit');
// 主码命中时 POS 那条同名接口会把 base_unit 填进 matched_unit,照单全收 = 每一行都贴个没用的单位
eq(matchedUnit({ product: { id: 'p1' }, matched_by: 'product', matched_unit: 'ขวด' }), '',
   'main barcode hit -> base unit, not a box scan');
eq(matchedUnit({ product: { id: 'p1' }, matched_unit: 'ลัง' }), 'ลัง',
   'matched_by absent but a unit name is given -> still a unit hit');
eq(matchedUnit({ product: { id: 'p1' } }), '', 'nothing said -> base unit');
eq(matchedUnit(null), '', 'no body -> base unit');

// 数量:一次一件。空/脏值当 0 起算;拆零品小数不留浮点尾巴
eq(bumpQty(''), '1', 'blank qty -> 1');
eq(bumpQty('0'), '1', 'zero -> 1');
eq(bumpQty('11'), '12', 'integer +1');
eq(bumpQty('2.5'), '3.5', 'fractional +1');
eq(bumpQty('0.1'), '1.1', 'no float tail on 0.1+1');
eq(bumpQty('abc'), '1', 'garbage -> 1');
eq(bumpQty('  7 '), '8', 'trims');

// 枪扫进数量框:字符照旧落进了框里(楔子只吃 Enter/Tab),得摘回去
eq(stripScanned('8850999320014', '8850999320014'), '', 'whole value was the code');
eq(stripScanned('248850999320014', '8850999320014'), '24', 'code appended after a real qty');
eq(stripScanned('28850999320014' + '4', '8850999320014'), '24', 'code inserted mid value');
eq(stripScanned('24', '8850999320014'), '24', 'no code in there -> untouched');
eq(stripScanned('', '8850999320014'), '', 'empty stays empty');

// 光标在数量框里时人可能正在打数量:三四位打得快也会被楔子当一串码,靠长度分开。
// 零售条码最短 8 位(EAN-8/UPC-E),店里没有 8 位数的数量。
eq(acceptsCode('24', true), false, 'typed qty is not a barcode');
eq(acceptsCode('240', true), false, 'three fast digits in a field is not a barcode');
eq(acceptsCode('12345678', true), true, 'EAN-8 length passes in a field');
eq(acceptsCode('8850999320014', true), true, 'EAN-13 passes in a field');
eq(acceptsCode('123456', false), true, 'short code ok when focus is not in a field');
eq(acceptsCode('12', false), false, 'below wedge MIN_LENGTH always rejected');

// 效期:一串条码打进 type=date 会留下 49012-03-31(date 控件收得下 6 位年份)。扫码那层靠
// 「框里现在不是个像样日期」认出这是机器打的(不必猜速度),提交那层靠它把坏值拦在流水外。
eq(isPlausibleDate('2027-05-20'), true, 'a date a person finished typing');
eq(isPlausibleDate('49012-03-31'), false, 'five-digit year is what a barcode leaves behind');
eq(isPlausibleDate('0490-12-31'), false, 'four digits but nobody stocks goods expiring in year 490');
eq(isPlausibleDate(''), false, 'half-typed date is not finished');
eq(isPlausibleDate('2027-5-20'), false, 'not the yyyy-mm-dd a date input emits');
// 提交闸:没填是允许的(不是每箱货都有效期),填了就必须像样
eq(isSaneExpiry(''), true, 'no expiry is allowed');
eq(isSaneExpiry('   '), true, 'blank is still no expiry');
eq(isSaneExpiry('2027-05-20'), true, 'a normal expiry passes');
eq(isSaneExpiry('49012-03-31'), false, 'the barcode-wrecked date is refused');
eq(isSaneExpiry('0490-12-31'), false, 'implausible year is refused');

// 未命中卡必须把扫到的码带进 DOM:店员靠它分辨码贴错了还是这货没建档
globalThis.t = (k) => k;
globalThis.escapeHtml = (s) => String(s == null ? '' : s);
const card = notFoundHtml('9999999999999');
if (card.indexOf('9999999999999') < 0) { bad++; console.error('FAIL scanned code missing from the not-found card'); }

// 取景框必须【小于】真正解码的区域:预览是 object-fit:cover(只裁不补),
// 框比解码区大就会出现「框里对准了却读不出」。且必须居中。
const crop = { width: 0.9, height: 0.5 };
const box = frameBox(crop);
if (!(box.width < crop.width * 100)) { bad++; console.error('FAIL frame wider than crop'); }
if (!(box.height < crop.height * 100)) { bad++; console.error('FAIL frame taller than crop'); }
eq(box.left, (100 - box.width) / 2, 'frame centered horizontally');
eq(box.top, (100 - box.height) / 2, 'frame centered vertically');

if (bad) process.exit(1);
console.log('OK');
"""


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class InventoryScanPureTests(unittest.TestCase):
    def test_scan_decisions_in_real_node(self):
        # 显式 utf-8:失败信息里有泰文单位名(ลัง),按 Windows 默认 cp874 解会炸成
        # UnicodeDecodeError,红的原因反而看不见了。
        proc = subprocess.run(
            ["node", "-e", DRIVER, str(HOME_DIR)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, msg=(proc.stdout + proc.stderr))
        self.assertIn("OK", proc.stdout)


class InventoryScanWiringTests(unittest.TestCase):
    """跨文件的约定 —— node 里跑不到、只能在源里确定性读出来的那几条。

    ⚠️ 2026-07-31 起,凡是「跑一遍就能读出来」的都不在这里了,搬去
    `test_inventory_scan_behavior.py` 真跑真断。原因是实锤:把 `unmountInvScan()` 的函数体
    整个包进 `if (false)`(字面一个字没删),这一堆字符串断言照样全绿 —— 相机灯永远亮着、
    楔子永不反注册,没有一条会红。留在这里的只剩两类:
      · 两端各在一个文件里的契约(桥的名字、信封字段名、后端 InLine 收不收 unit_name)
      · 「不许自己另写一套」这类否定式架构规矩(node 里跑不出「没做某事」)
    往这里加断言之前先问一句:这条能不能改成跑一遍读结果?能就别加在这儿。
    """

    @classmethod
    def setUpClass(cls):
        cls.scan = SCAN_TS.read_text(encoding="utf-8")
        cls.ui = UI_TS.read_text(encoding="utf-8")
        cls.cam = CAM_TS.read_text(encoding="utf-8")
        cls.modals = MODALS_TS.read_text(encoding="utf-8")

    def test_wedge_is_exclusive_while_modal_open(self):
        # 独占与否是楔子内部的事(subs 里那个 exclusive 标记不对外),从外面读不出来 ——
        # 只能在这里钉源码。真实效果(枪扫的码不漏进底下的库存页)归 E2E。
        self.assertIn("{ exclusive: true }", self.scan)

    def test_create_bridge_is_the_one_the_product_form_exports(self):
        # 上一轮这里调的是一个全仓没有定义的名字(死胡同:点了没反应)。桥的名字只有一个,
        # 两端必须对得上 —— 建品侧挂 window,入库侧照这个名字调。桥【怎么被调用的】
        # (带不带 overlay、返回 false 时回落成什么)已在 behavior 那份里真跑真断。
        bridge = "openProductFormWithBarcode"
        self.assertIn(bridge, BRIDGE_TS.read_text(encoding="utf-8"), "建品侧没挂这个桥")
        self.assertIn(bridge, self.scan, "入库侧没按这个名字调")

    def test_dead_cross_document_handoff_is_gone_from_the_receive_side(self):
        # 只读不写的跨文档键当年就没生效过;入库侧不许再留它的痕迹。
        self.assertNotIn("pearnly_new_product_barcode", self.scan)
        self.assertNotIn("openSalesProductWithBarcode", self.scan)

    def test_batch_visibility_reuses_onproductchange(self):
        # 「不许自己另写一套」是否定式规矩:跑一遍只能证明批次格露出来了,证不了它是【借的】
        # 那一套 —— 扫码侧自己画一份也能让测试绿。所以这条只能在源里读。
        # 格露没露出来那一半已在 behavior 那份里真跑真断。
        self.assertIn("syncRow: onProductChange", self.modals)
        for own in ("batchcell", "expiry_date", "style.display"):
            self.assertNotIn(own, self.scan, f"扫码侧不许自己画批次格({own})")
        # 「这商品管不管批次」取查码回来的那一条(权威),不取列表缓存 —— 列表被搜索/筛选
        # 过时缓存里根本没有刚扫到的货。
        self.assertIn("product.track_batch", self.scan)
        self.assertNotIn("invApi", self.scan)

    def test_track_batch_reaches_the_row_from_the_lookup_answer(self):
        # 上一轮 syncRow 只收 row:那边照旧拿商品 id 去列表缓存里查,刚建完的货查不到 → 当成
        # 非批次品 → 批号格永不出现 → 一批批次品静默落进散装桶。这条接缝在两个文件之间,
        # 真跑那条路的是 scripts/_inv_p1_verify.cjs::freshProduct;这里只钉住契约别再退回去。
        self.assertIn("syncRow: (row: HTMLElement, tracksBatch: boolean) => void;", self.scan)
        self.assertIn("active.host.syncRow(row, hit.tracksBatch);", self.scan)
        self.assertIn("function onProductChange(row: HTMLElement, scanned?: boolean)", self.modals)
        # 查码应答优先于缓存,且记下来 —— 店员在下拉里切走再切回来时缓存照旧答不出
        self.assertIn("scannedTrackBatch.set(id, scanned)", self.modals)
        self.assertIn("const isBatch = !!id && tracksBatch(id);", self.modals)

    def test_batch_fields_take_the_gun_and_expiry_has_a_backstop(self):
        # 批号/效期框不 opt-in = 枪扫整发被吞(零回调、行不出现),而那串数字照旧落进 date 控件。
        row = self.modals.split("data-batchcell")[1].split("</span>")[0]
        for field in ('data-k="batch_no"', 'data-k="expiry_date"'):
            decl = row.split(field)[1].split(">")[0]
            self.assertIn("data-enable-barcode", decl, f"{field} 没对枪 opt-in")
        # 效期框不许写 max:实测一旦写上,人手逐段敲日期敲不出结果,而条码会被夹成
        # 0490-12-31 这种「看着正常」的假日期 —— 比 49012 更难被发现。
        self.assertNotIn("max=", row.split('data-k="expiry_date"')[1].split(">")[0])
        # 进流水前的最后一道
        self.assertIn("if (raw.some((r) => !isSaneExpiry(r.expiry_date)))", self.modals)
        self.assertIn("inv-err-bad-expiry", self.modals)

    def test_failed_codes_survive_the_next_item(self):
        # 一格消息位共用一个 setMsg 时,后一件的「已加入」把前一件的「这个码没建档」盖掉:
        # 店员按屏上反馈收货,被盖掉的那件就是扫了没进单也没人告诉他的货。
        ui = UI_TS.read_text(encoding="utf-8")
        for fn in ("pushFail", "replaceFail", "resolveFail", "resetFeedback", "paintNote"):
            self.assertIn(f"export function {fn}", ui, f"待办队列缺 {fn}")
        self.assertIn("pushFail(part('msg'), code, html)", self.scan, "失败没进队列")
        self.assertIn("resolveFail(part('msg'), code)", self.scan, "命中后没销掉那一条")
        # 相机面板往同一格里写字:它也必须走瞬时行,否则一开相机就把待办全抹了
        self.assertIn("paintNote(scanPart(host.maskId, 'msg')", self.cam)
        self.assertNotIn("paintMsg", self.scan + self.cam + ui, "旧的单格画法还留着 = 两套并存")
        # 每条自己一行、自己一个颜色(整块只有一个 tone 时,绿的「已加入」会被涂成黄的)
        self.assertIn(".inv-scan-line", SCAN_CSS.read_text(encoding="utf-8"))

    def test_lookup_envelope_field_names_match_the_other_consumer(self):
        # 建品侧(sales-products-scan.ts)也读这个信封:两边读同一份后端应答,字段名各写各的
        # 就会有一边永远读不到(那正是「绿字说没人用、POS 却扫到别的商品」那条老路)。
        bridge = BRIDGE_TS.read_text(encoding="utf-8")
        for field in ("matched_by", "matched_unit"):
            self.assertIn(field, bridge, f"建品侧没读 {field}")
            self.assertIn(field, self.scan, f"入库侧没读 {field}")
        self.assertIn("'product'", self.scan, "主码命中那一档没被区分出来")

    def test_unit_name_is_a_real_backend_field_not_a_frontend_invention(self):
        # 单位随行提交、后端 resolve_factor 折算(前端不自己乘系数)。字段值怎么落到行上
        # 已在 behavior 那份里真跑真断;这里只钉【后端确实收这个字段】—— 那一端在另一个
        # 语言的另一个文件里,node 跑不到,而两边不一致就是「屏上有单位、入库按瓶算」。
        self.assertIn("if (r.unit_name) ln.unit_name = r.unit_name;", self.modals)
        self.assertIn("unit_name?: string;", COMMON_TS.read_text(encoding="utf-8"))
        routes = (PROJECT_ROOT / "routes" / "inventory_routes.py").read_text(encoding="utf-8")
        self.assertRegex(routes, r"class InLine\(BaseModel\):[\s\S]{0,200}unit_name")
        # 标签得有脸:CSS 在另一个文件里,跑不出来
        self.assertIn(".inv-runit", SCAN_CSS.read_text(encoding="utf-8"))

    def test_four_states_all_have_a_visible_tone(self):
        # 每个状态都得真能看见:第一版 tip 那档设了文字但 CSS 里没有对应显隐,屏上什么都没有。
        css = SCAN_CSS.read_text(encoding="utf-8")
        src = self.scan + self.cam
        for tone in ("busy", "ok", "warn", "err", "tip"):
            self.assertRegex(src, r"[mM]sg\((?:host, )?'" + tone + r"'", f"{tone} 档没人用")
            self.assertIn(f".inv-scan-msg.{tone}", css, f"{tone} 档 CSS 里没有脸")
        self.assertIn(".inv-scan-msg:empty", css, "空态没收起 → 空盒子占位")

    def test_new_css_is_bundled_and_token_only(self):
        css = SCAN_CSS.read_text(encoding="utf-8")
        self.assertIn("home-58-inventory-scan.css", CSS_BUILD.read_text(encoding="utf-8"))
        self.assertEqual([], re.findall(r"#[0-9a-fA-F]{3,6}\b", css), "裸 hex 不随暗夜令牌翻面")

    def test_built_bundle_carries_the_scan_bar(self):
        # 部署只发 dist:源改了没重新打包 = 线上没这功能。
        dist = DIST_MAIN.read_text(encoding="utf-8")
        for marker in ("inv-scan-msg", "inv-runit", "openProductFormWithBarcode"):
            # assertTrue 而非 assertIn:失败时 assertIn 会把整个 1MB bundle 打进日志
            self.assertTrue(marker in dist, f"dist 里没有 {marker} · 忘了重新打包")

    def test_no_debug_leftovers(self):
        for src in (self.scan, self.ui, self.cam):
            self.assertNotIn("console.log", src)


if __name__ == "__main__":
    unittest.main()
