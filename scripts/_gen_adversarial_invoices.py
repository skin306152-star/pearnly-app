# -*- coding: utf-8 -*-
"""对抗性测试发票生成器:复用 _gen_test_invoices 的渲染基建(Sarabun/§86 版式),
专为压测「商品明细落 Express 商品主档 STMAS」而设计 —— 商品多而杂,覆盖:
  · 与昨日已推商品精确同名(测 find-or-create 复用,不应重复建档)
  · 超 40 字符长品名(测 STKDES C(40) 截断致去重失效 → 重复建档)
  · 共享前 40 字符的两个长名(测截断碰撞 → 同名不同码)
  · 空格/大小写变体(_norm 应归一 → 复用)
  · 拼写/声调差异(应视为不同 → 各自建档)
  · 特殊字符/型号/中泰英混排/小数数量

输出:~/Desktop/test_invoices_adversarial/ + README(列每张商品 + 预期落库行为)。
运行:python scripts/_gen_adversarial_invoices.py
"""

from __future__ import annotations

import importlib.util
import os
import sys
from decimal import Decimal

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "_gen_test_invoices", os.path.join(_HERE, "_gen_test_invoices.py")
)
g = importlib.util.module_from_spec(_spec)
sys.modules["_gen_test_invoices"] = g  # dataclass 解析需模块在 sys.modules
_spec.loader.exec_module(g)

OUT_ROOT = os.path.join(os.path.expanduser("~"), "Desktop", "test_invoices_adversarial")

OWN = g.OWN  # 自家 = DATAT 账套 มานะชัยบริการ 0735527000289(销项卖方)

# 油品店买家(各不同·HS 现销/赊销)
BUYERS = {
    "garage": {
        "name": "อู่ช่างเอกการช่าง",
        "addr": "45/7 ถนนรามอินทรา แขวงอนุสาวรีย์ เขตบางเขน กรุงเทพฯ 10220",
        "tax": "0105556700123",
    },
    "fleet": {
        "name": "บริษัท ขนส่งทรัพย์รุ่งเรือง จำกัด",
        "addr": "199 หมู่ 5 ถนนบางนา-ตราด ตำบลบางเสาธง อำเภอบางเสาธง สมุทรปราการ 10570",
        "tax": "0115560088442",
    },
    "taxi": {
        "name": "สหกรณ์แท็กซี่สุวรรณภูมิ จำกัด",
        "addr": "88 ถนนกิ่งแก้ว ตำบลราชาเทวะ อำเภอบางพลี สมุทรปราการ 10540",
        "tax": "0994000155661",
    },
}


def I(desc, qty, price):
    return g.Item(desc, Decimal(str(qty)), Decimal(str(price)))


def inv(num, fname, title, expected, buyer, items, inv_no, date, payment):
    return g.Invoice(
        num,
        fname,
        "adversarial",
        title,
        expected,
        "推送(商品落库压测)",
        OWN,
        buyer,
        items,
        inv_no,
        date,
        payment=payment,
    )


def build():
    S = []

    # A1 — 与昨日重复 + 近似变体混打(测复用 vs 去重脆弱)
    S.append(
        inv(
            "A1",
            "A1_repeat_and_variants",
            "重复+近似变体",
            "短名精确同名应复用昨日PN;长名/带前缀变体会另建",
            BUYERS["garage"],
            [
                I("PERFORMA NGV 10W-40 (10/1L)", 6, 185),  # = PN00020 → 应复用
                I("น้ำกลั่น", 12, 15),  # = PN00019 → 应复用
                I("PTT DYNAMIC PREMIER (10/1)", 4, 220),  # = PN00027 → 应复用
                I("AUTOMAT (10/1L)", 3, 195),  # = PN00028 → 应复用
                I("น้ำมันเครื่อง PERFORMA NGV 10W-40 (10/1L)", 2, 190),  # >40 长名 → 重复建档(bug)
                I(
                    "PERFORMA NGV 10W-40 ( 10 / 1 L )", 2, 185
                ),  # 空格变体 → _norm 归一应复用 PN00020
                I("performa ngv 10w-40 (10/1l)", 1, 185),  # 大小写变体 → 应复用 PN00020
                I("ผ้าเบรกหน้า", 4, 320),  # = PN00029 → 应复用
                I("ผ้าเบรคหน้า", 4, 320),  # ค/ก 拼写差异 → 视为不同,另建
            ],
            "HS6901-101",
            (2025, 12, 24),
            "เงินสด",
        )
    )

    # A2 — 超 40 字符长名 + 共享前 40 碰撞
    common = "ชุดซ่อมระบบหัวฉีดคอมมอนเรลดีเซลพร้อมอะไหล่แท้เบอร์"  # 长(>40)公共前缀
    S.append(
        inv(
            "A2",
            "A2_long_name_truncation",
            "超长品名截断碰撞",
            "前40字符相同的两个长名→STKDES截断后同名(应暴露截断去重缺陷)",
            BUYERS["fleet"],
            [
                I(common + " A-001", 1, 4500),  # 截断后 = common[:40]
                I(common + " B-002", 1, 4800),  # 截断后同上 → 商品库两条同名不同码
                I(
                    "น้ำมันเครื่องสังเคราะห์แท้ 100% เกรดส่งออกสำหรับเครื่องยนต์ดีเซลคอมมอนเรล",
                    2,
                    1250,
                ),  # 单条超长
                I(
                    "ค่าบริการตรวจเช็คและบำรุงรักษาเครื่องยนต์ตามระยะ 40000 กิโลเมตร", 1, 3500
                ),  # 长服务名
                I("แบตเตอรี่รถยนต์ 12V 70Ah", 2, 2850),  # = PN00032 → 应复用
                I("ไส้กรองโซลินอยด์ Bosch 0445110xxx", 1, 1900),  # 型号/特殊字符
            ],
            "HS6901-102",
            (2025, 12, 25),
            "เงินเชื่อ",
        )
    )

    # A3 — 特殊字符/数字/型号密集(测字段宽度与编码)
    S.append(
        inv(
            "A3",
            "A3_special_chars_models",
            "特殊字符型号密集",
            "斜杠/×/#/% 与型号码不应破坏建档",
            BUYERS["garage"],
            [
                I("ฟิวส์ 30A/32V (แพ็ค 10)", 5, 45),
                I("สายพานไทม์มิ่ง 104RU25", 2, 680),
                I("โอริง 9.8×2.4 mm (ถุง 50)", 3, 120),
                I("น็อตล้อ M12×1.5 (ชุด 20)", 4, 95),
                I("หัวเทียน NGK Iridium IX BKR6EIX", 8, 240),
                I('ยางปัดน้ำฝน 18"+24" (คู่)', 6, 320),
                I("น้ำยาแอร์ R-134a (กระป๋อง 1kg)", 10, 180),
                I("โช้คอัพหน้า KYB #341234 (ต้น)", 2, 1450),
            ],
            "HS6901-103",
            (2025, 12, 26),
            "เงินสด",
        )
    )

    # A4 — 中泰英混排 + 长名 + 服务行(贴近真实杂单)
    S.append(
        inv(
            "A4",
            "A4_mixed_lang_services",
            "中泰英混排+服务",
            "多语言/长服务名应原样落库(截断到40)",
            BUYERS["taxi"],
            [
                I("เครื่องฟอกอากาศในรถ 车载空气净化器 Model CA-220", 3, 890),
                I("กล้องติดรถยนต์ 行车记录仪 70mai A810 Dash Cam", 2, 2490),
                I("ค่าบริการล้างและเคลือบสีรถยนต์แบบเซรามิกเกรดพรีเมียม", 1, 3900),
                I(
                    "น้ำมันเครื่อง PTT DYNAMIC PREMIER (10/1L)", 5, 215
                ),  # >40 → 测是否再重复(对照昨日 PN00031/36)
                I("จารบีอเนกประสงค์", 6, 85),  # = PN00030(注:昨日误建成 STKTYP=0)
                I("ค่าแรงช่าง (ชั่วโมง)", 8, 250),
            ],
            "HS6901-104",
            (2025, 12, 27),
            "เงินเชื่อ",
        )
    )

    # A5 — 大批量明细(14 行·测多行 STCRD 与多次 ensure_item)
    items = [
        I("PTT V-120D #40 (10/1L)", 4, 175),  # = PN00025 → 复用
        I("V-120B #40 (10/1L)", 4, 170),  # = PN00026 → 复用
        I("PERFORMA SEMI SYN (6/4L)", 3, 560),  # = PN00024 → 复用
        I("หัวเชื้อดีเซล (24/0.17)", 5, 95),  # = PN00023 → 复用
        I("น้ำยาลดความร้อน", 6, 140),  # = PN00022 → 复用
        I("BRAKE EXTRA (12/0.5L)", 4, 130),  # = PN00021 → 复用
        I("น้ำมันเกียร์อัตโนมัติ ATF DEXRON VI (12/1L)", 3, 195),  # 新
        I("น้ำมันพวงมาลัยเพาเวอร์ PSF (12/1L)", 3, 165),  # 新
        I("สเปรย์หล่อลื่นโซ่ Chain Lube 400ml", 7, 145),  # 新
        I("ผ้าเบรกหลัง Compact (ชุด)", 3, 290),  # 新
        I("กรองอากาศ K&N 33-2304", 2, 1850),  # 新/型号
        I("ใบปัดน้ำฝนซิลิโคน 20 นิ้ว", 5, 160),  # 新
        I("น้ำมันเบรก DOT4 (12/0.5L)", 4, 110),  # 新
        I("ลูกหมากแร็ค 555 (คู่)", 2, 780),  # 新
    ]
    S.append(
        inv(
            "A5",
            "A5_bulk_14_lines",
            "大批量14行",
            "多行(部分复用+多新建)·测多次ensure_item与STCRD多行",
            BUYERS["fleet"],
            items,
            "HS6901-105",
            (2025, 12, 28),
            "เงินสด",
        )
    )
    return S


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    scen = build()
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    for v in scen:
        path = os.path.join(OUT_ROOT, v.fname + ".pdf")
        c = canvas.Canvas(path, pagesize=A4)
        c.setTitle(f"[{v.num}] {v.title}")
        c.setSubject(v.expected)
        c.setAuthor("Pearnly adversarial corpus (Opus 4.8)")
        g.render_standard(c, v)
        c.showPage()
        c.save()
    _write_readme(scen)
    print(f"Generated {len(scen)} adversarial PDFs -> {OUT_ROOT}")


def _norm(name):
    s = (name or "").strip().lower()
    return "".join(ch for ch in s if not ch.isspace() and ch != "\xa0")


def _write_readme(scen):
    # 已知昨日已存在 PN 主档(短名·可复用):归一名 → PN
    existing = {
        "performangv10w-40(10/1l)": "PN00020",
        "น้ำกลั่น": "PN00019",
        "pttdynamicpremier(10/1)": "PN00027",
        "automat(10/1l)": "PN00028",
        "ผ้าเบรกหน้า": "PN00029",
        "แบตเตอรี่รถยนต์12v70ah": "PN00032",
        "pttv-120d#40(10/1l)": "PN00025",
        "v-120b#40(10/1l)": "PN00026",
        "performasemisyn(6/4l)": "PN00024",
        "หัวเชื้อดีเซล(24/0.17)": "PN00023",
        "น้ำยาลดความร้อน": "PN00022",
        "brakeextra(12/0.5l)": "PN00021",
        "จารบีอเนกประสงค์": "PN00030",
    }
    lines = [
        "# 对抗性测试发票 · 商品落库压测(5 张)",
        "",
        "目的:验证商品明细是否真落进 Express 商品主档 STMAS、在商品库列表/库存卡/单据明细都可见,",
        "并暴露 `find-or-create` 在长品名(>40 字符)下的去重缺陷。",
        "",
        "## 上传前(同主语料):工作区主体税号设 `0735527000289`(มานะชัยบริการ)、上传时选中它。",
        "卖方=自家(销项 HS);买方为各油品店客户。",
        "",
        "## 每张商品明细 + 预期落库行为",
        "",
    ]
    for v in scen:
        lines.append(f"### {v.num} · {v.title} ({v.fname}.pdf) — {v.inv_no}")
        lines.append("")
        lines.append("| 商品名 | 长度 | 预期 STMAS 行为 |")
        lines.append("|---|---|---|")
        for it in v.items:
            n = _norm(it.desc)
            L = len(it.desc)
            if n in existing:
                exp = f"复用 {existing[n]}(精确/归一同名)"
            elif L > 40:
                exp = "⚠️ 长名>40 截断 → 可能重复建档(缺陷)"
            else:
                exp = "新建 PN"
            lines.append(f"| `{it.desc}` | {L} | {exp} |")
        lines.append("")
    lines += [
        "## 验证方法(推送后)",
        "1. 读 STMAS.DBF:数 PN##### 增量、查 STATUS 是否 ''、长名是否产生重复码。",
        "2. 读 STCRD.DBF:单据明细行是否引用正确 PN 码。",
        "3. Express GUI 商品库列表:STATUS='' 且 CDX 重建后,新商品应可见。",
        "4. 重点核对:`PERFORMA NGV 10W-40 (10/1L)` 等短名应复用、不新增重复;",
        "   长名(`น้ำมันเครื่อง ...`、`ชุดซ่อม... A/B`)是否如预期重复(暴露缺陷)。",
    ]
    with open(os.path.join(OUT_ROOT, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
