# -*- coding: utf-8 -*-
from __future__ import annotations
import json
import shutil
import subprocess
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
try:
    import qrcode
except Exception:  # pragma: no cover
    qrcode = None
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "services" / "export" / "fonts"
FONT = str(FONT_DIR / "Sarabun-Regular.ttf")
FONT_B = str(FONT_DIR / "Sarabun-Bold.ttf")
SELLERS = [("CP ALL, 7-Eleven สาขาสีลม", "0107542000011"), ("บริษัท เซ็นทรัล ฟู้ด รีเทล จำกัด", "0105544060428"), ("บริษัท สยามแม็คโคร จำกัด (มหาชน)", "0107537000521"), ("Lotus's สาขาพระราม 4", "0107543000121"), ("PTT Station Cafe Amazon", "0107561000013"), ("ร้านอาหารบ้านสวนป้าลี", "0735559001248"), ("บริษัท เอเชีย ออฟฟิศ ซัพพลาย จำกัด", "0105562033104"), ("บริษัท เมืองไทยโลจิสติกส์ จำกัด", "0105558123456")]
BUYERS = [("บริษัท ดาต้าทูลส์ จำกัด", "0735527000289"), ("บริษัท เพิร์นลี่ เทค จำกัด", "0105564061523"), ("หจก. สกิน แอนด์ โค", "0903563007788"), ("", "")]
ITEMS = [("น้ำดื่ม 600ml", "1", "10.00"), ("กาแฟเย็น", "2", "45.00"), ("สปาเก็ตตี้", "1", "59.00"), ("กระดาษ A4", "3", "120.00"), ("ค่าขนส่ง", "1", "80.00"), ("ข้าวกล่อง", "4", "65.00"), ("น้ำมันดีเซล ลิตร", "12.35", "32.12"), ("บริการซ่อมแซม", "1", "1500.00"), ("สายชาร์จ USB-C", "2", "199.00"), ("นมสด", "3", "28.00")]
DEGS = [["motion_blur_mid"], ["thermal_fade"], ["glare"], ["crease"], ["low_res", "jpeg_artifact"]]
def d(v) -> Decimal:
    return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
def m(v) -> str:
    return f"{d(v):.2f}"
def fnt(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)
def mkdirs():
    for p in [OUT / "images", OUT / "ground_truth", OUT / "bank", OUT / "gl", OUT / "vat"]:
        if p.exists():
            if OUT.resolve() not in p.resolve().parents:
                raise RuntimeError(f"refuse to clear {p}")
            shutil.rmtree(p)
    for p in [
        OUT / "images",
        OUT / "ground_truth",
        OUT / "bank" / "images",
        OUT / "bank" / "ground_truth",
        OUT / "gl" / "images",
        OUT / "gl" / "ground_truth",
        OUT / "vat" / "images",
        OUT / "vat" / "ground_truth",
    ]:
        p.mkdir(parents=True, exist_ok=True)
def right(draw, xy, text, font, fill=(25, 25, 25)):
    x, y = xy
    box = draw.textbbox((0, 0), str(text), font=font)
    draw.text((x - box[2], y), str(text), font=font, fill=fill)
def center(draw, y, text, font, w, fill=(25, 25, 25)):
    box = draw.textbbox((0, 0), str(text), font=font)
    draw.text(((w - box[2]) / 2, y), str(text), font=font, fill=fill)
def line(draw, y, w):
    draw.line((34, y, w - 34, y), fill=(60, 60, 60), width=1)
def qr_img(text, size=92):
    if not qrcode:
        return Image.new("RGB", (size, size), "white")
    qr = qrcode.QRCode(border=1, box_size=3)
    qr.add_data(text)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB").resize((size, size))
def receipt(case, compact=False):
    rows = case["items"] + case.get("printed_only_items", [])
    h = 500 + len(rows) * 34 + len(case.get("extras", [])) * 29
    w = 760 if compact else 900
    img = Image.new("RGB", (w, h), (252, 250, 238))
    draw = ImageDraw.Draw(img)
    y = 26
    center(draw, y, case["seller_name"], fnt(30, True), w)
    y += 38
    center(draw, y, "TAX ID " + case["seller_tax"], fnt(22), w)
    y += 30
    center(draw, y, "ใบกำกับภาษีอย่างย่อ / RECEIPT", fnt(25, True), w)
    y += 38
    line(draw, y, w)
    y += 14
    draw.text((38, y), "เลขที่ / No.", font=fnt(22), fill=(25, 25, 25))
    right(draw, (w - 38, y), case["invoice_number"], fnt(22))
    y += 28
    draw.text((38, y), "วันที่ / Date", font=fnt(22), fill=(25, 25, 25))
    right(draw, (w - 38, y), case["date_raw"], fnt(22))
    y += 34
    line(draw, y, w)
    y += 14
    for it in rows:
        draw.text((38, y), it["name"][:34], font=fnt(22), fill=(20, 20, 20))
        right(draw, (w - 230, y), it.get("qty", ""), fnt(22))
        right(draw, (w - 130, y), it.get("price", ""), fnt(22))
        right(draw, (w - 38, y), it.get("subtotal", ""), fnt(22))
        y += 34
    for extra in case.get("extras", []):
        draw.text((38, y), extra[0], font=fnt(20), fill=(35, 35, 35))
        right(draw, (w - 38, y), extra[1], fnt(20))
        y += 29
    y += 4
    line(draw, y, w)
    y += 16
    for label, key in [
        ("SUBTOTAL", "subtotal"),
        ("DISCOUNT", "discount"),
        ("VAT", "vat"),
        ("WHT", "wht_amount"),
        ("TOTAL / ยอดสุทธิ", "total_amount"),
        ("CASH / รับเงิน", "cash_amount"),
        ("CHANGE / เงินทอน", "change_amount"),
    ]:
        val = case.get(key) or ""
        if val and val != "0.00" or key in ("subtotal", "vat", "total_amount"):
            draw.text((46, y), label, font=fnt(23, key == "total_amount"), fill=(20, 20, 20))
            right(draw, (w - 48, y), val, fnt(26, key == "total_amount"))
            y += 34
    if case.get("currency"):
        draw.text((46, y), "CURRENCY", font=fnt(22), fill=(20, 20, 20))
        right(draw, (w - 48, y), case["currency"], fnt(23, True))
        y += 32
    img.paste(qr_img(case["id"]), (w - 130, h - 118))
    center(draw, h - 45, "ขอบคุณที่ใช้บริการ", fnt(23), w)
    if case.get("handwritten"):
        draw.line((w - 330, h - 190, w - 90, h - 210), fill=(36, 73, 180), width=4)
        draw.text((w - 320, h - 255), "รวม " + case["total_amount"], font=fnt(42, True), fill=(36, 73, 180))
    return img
def a4_invoice(case):
    w, h = 1240, 1754
    img = Image.new("RGB", (w, h), (255, 255, 250))
    draw = ImageDraw.Draw(img)
    y = 70
    title = case.get("doc_title") or "ใบกำกับภาษี / TAX INVOICE"
    center(draw, y, title, fnt(42, True), w)
    y += 70
    draw.text((70, y), case["seller_name"], font=fnt(32, True), fill=(20, 20, 20))
    draw.text((70, y + 42), "เลขประจำตัวผู้เสียภาษี " + case["seller_tax"], font=fnt(24), fill=(20, 20, 20))
    right(draw, (w - 70, y), "No. " + (case["invoice_number"] or "-"), fnt(28, True))
    right(draw, (w - 70, y + 38), case["date_raw"], fnt(24))
    y += 120
    draw.text((70, y), "Buyer: " + case.get("buyer_name", ""), font=fnt(25), fill=(20, 20, 20))
    draw.text((70, y + 32), "Buyer Tax: " + case.get("buyer_tax", ""), font=fnt(23), fill=(20, 20, 20))
    y += 86
    xs = [70, 160, 680, 840, 1010, 1160]
    for x in xs:
        draw.line((x, y, x, y + 880), fill=(40, 40, 40), width=1)
    draw.line((70, y, 1160, y), fill=(40, 40, 40), width=2)
    for x, t in zip(xs[:-1], ["#", "รายการ", "จำนวน", "ราคา", "จำนวนเงิน"]):
        draw.text((x + 10, y + 12), t, font=fnt(23, True), fill=(20, 20, 20))
    y += 54
    rows = case["items"] + case.get("printed_only_items", [])
    for i, it in enumerate(rows, 1):
        draw.line((70, y, 1160, y), fill=(190, 190, 190), width=1)
        vals = [str(i), it["name"][:40], it.get("qty", ""), it.get("price", ""), it.get("subtotal", "")]
        for x, t in zip(xs[:-1], vals):
            draw.text((x + 10, y + 10), t, font=fnt(19 if len(rows) > 15 else 23), fill=(20, 20, 20))
        y += 42 if len(rows) > 15 else 50
    draw.line((70, y, 1160, y), fill=(40, 40, 40), width=2)
    y += 30
    for extra in case.get("extras", []):
        draw.text((100, y), extra[0], font=fnt(22), fill=(30, 30, 30))
        right(draw, (1120, y), extra[1], fnt(22))
        y += 30
    y = 1390
    for label, key in [("Subtotal", "subtotal"), ("Discount", "discount"), ("VAT", "vat"), ("WHT", "wht_amount"), ("Grand Total", "total_amount")]:
        val = case.get(key) or ""
        if val and val != "0.00" or key in ("subtotal", "vat", "total_amount"):
            draw.text((760, y), label, font=fnt(28, key == "total_amount"), fill=(20, 20, 20))
            right(draw, (1120, y), val, fnt(30, key == "total_amount"))
            y += 42
    if case.get("handwritten"):
        draw.text((210, 1450), "ยอดรวมเขียนมือ " + case["total_amount"], font=fnt(50, True), fill=(32, 80, 190))
        draw.line((200, 1515, 610, 1480), fill=(32, 80, 190), width=5)
    return img
def multi_receipt(case):
    w, h = 1350, 1750
    bg = Image.new("RGB", (w, h), (238, 232, 218))
    tickets = [case] + case["additional_invoices"]
    for i, c in enumerate(tickets):
        im = receipt(c, compact=True)
        im = im.resize((520, int(im.height * 520 / im.width)))
        im = im.rotate([-4, 3, -2][i % 3], expand=True, fillcolor=(238, 232, 218))
        bg.paste(im, (80 + (i % 2) * 650, 70 + (i // 2) * 760))
    return bg
def render_invoice(case):
    if case.get("layout") == "multi":
        return multi_receipt(case)
    if case.get("layout") in ("a4", "dense", "doc", "stack"):
        return a4_invoice(case)
    return receipt(case)
def add_noise(a, amount, rng):
    n = rng.normal(0, amount, a.shape).astype(np.int16)
    return np.clip(a.astype(np.int16) + n, 0, 255).astype(np.uint8)
def degrade(img, tags, seed):
    rng = np.random.default_rng(seed)
    a = np.array(img.convert("RGB"))
    for tag in tags:
        if tag.startswith("motion_blur"):
            k = {"low": 5, "mid": 11, "high": 19}.get(tag.split("_")[-1], 9)
            kernel = np.zeros((k, k)); kernel[k // 2, :] = 1 / k
            a = cv2.filter2D(a, -1, kernel)
        elif tag in ("defocus_blur",):
            a = cv2.GaussianBlur(a, (9, 9), 0)
        elif tag in ("thermal_fade",):
            grad = np.linspace(0.72, 1.18, a.shape[0])[:, None, None]
            a = np.clip((a * grad + 32), 0, 255).astype(np.uint8)
            a = add_noise(a, 8, rng)
        elif tag in ("glare",):
            ov = a.copy()
            cv2.ellipse(ov, (a.shape[1] * 2 // 3, a.shape[0] // 3), (220, 95), -18, 0, 360, (255, 255, 255), -1)
            a = cv2.addWeighted(ov, 0.42, a, 0.58, 0)
        elif tag in ("shadow",):
            x = np.linspace(0.55, 1.0, a.shape[1])[None, :, None]
            a = np.clip(a * x, 0, 255).astype(np.uint8)
        elif tag in ("crease", "fold_crease", "crumple"):
            for i in range(3 if tag == "crumple" else 1):
                x = int(a.shape[1] * (0.25 + 0.22 * i))
                cv2.line(a, (x, 0), (x + 40, a.shape[0]), (210, 210, 210), 5)
                cv2.line(a, (x + 7, 0), (x + 47, a.shape[0]), (90, 90, 90), 1)
        elif tag == "rotate_90":
            a = cv2.rotate(a, cv2.ROTATE_90_CLOCKWISE)
        elif tag.startswith("skew"):
            angle = -15 if "-" in tag else 15
            mat = cv2.getRotationMatrix2D((a.shape[1] / 2, a.shape[0] / 2), angle, 1)
            a = cv2.warpAffine(a, mat, (a.shape[1], a.shape[0]), borderValue=(245, 242, 232))
        elif tag in ("perspective", "phone_photo_skew"):
            h, w = a.shape[:2]; dx = int(w * 0.08); dy = int(h * 0.05)
            src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
            dst = np.float32([[dx, dy], [w - dx // 2, 0], [w - dx, h - dy], [0, h]])
            a = cv2.warpPerspective(a, cv2.getPerspectiveTransform(src, dst), (w, h), borderValue=(236, 229, 215))
        elif tag in ("low_res",):
            h, w = a.shape[:2]
            a = cv2.resize(cv2.resize(a, (max(1, w // 3), max(1, h // 3))), (w, h), interpolation=cv2.INTER_LINEAR)
        elif tag in ("jpeg_artifact",):
            ok, enc = cv2.imencode(".jpg", a, [int(cv2.IMWRITE_JPEG_QUALITY), 24])
            a = cv2.imdecode(enc, 1) if ok else a
        elif tag in ("torn", "partial_page"):
            pts = np.array([[0, 0], [a.shape[1] // 5, 0], [0, a.shape[0] // 4]], np.int32)
            cv2.fillPoly(a, [pts], (238, 232, 218))
            if tag == "partial_page":
                a = a[: int(a.shape[0] * 0.78), :]
        elif tag in ("dark",):
            a = np.clip(a * 0.58, 0, 255).astype(np.uint8)
        elif tag in ("overexposed",):
            a = np.clip(a * 1.25 + 35, 0, 255).astype(np.uint8)
        elif tag in ("bg_clutter",):
            pad = 95
            bg = np.zeros((a.shape[0] + pad * 2, a.shape[1] + pad * 2, 3), dtype=np.uint8)
            bg[:] = (188, 157, 118)
            bg = add_noise(bg, 13, rng)
            bg[pad: pad + a.shape[0], pad: pad + a.shape[1]] = a
            a = bg
        elif tag in ("flatbed_scan",):
            a = add_noise(a, 4, rng)
        elif tag in ("moire",):
            yy = np.sin(np.arange(a.shape[0])[:, None] / 3) * 10
            a = np.clip(a.astype(np.int16) + yy[:, :, None], 0, 255).astype(np.uint8)
    return Image.fromarray(a)
def save_img(img, path):
    img.save(path, "JPEG", quality=86, optimize=True)
def jdump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def base_case(cid, scenario, traps, degs, idx, layout="pos"):
    seller = SELLERS[(idx + len(traps)) % len(SELLERS)]
    buyer = BUYERS[idx % len(BUYERS)]
    its = []
    for k in range(2 + idx % 4):
        name, qty, price = ITEMS[(idx + k) % len(ITEMS)]
        its.append({"name": name, "qty": qty, "price": price, "subtotal": m(d(qty) * d(price))})
    sub = sum(d(x["subtotal"]) for x in its)
    vat = d(sub * Decimal("0.07")) if idx % 3 else Decimal("0")
    total = sub + vat
    return {
        "id": cid, "name": cid, "file": cid + ".jpg", "document_type": "tax_invoice",
        "is_not_invoice": False, "is_copy_or_duplicate": False,
        "seller_name": seller[0], "seller_tax": seller[1], "seller_addr": "กรุงเทพมหานคร",
        "buyer_name": buyer[0], "buyer_tax": buyer[1], "buyer_addr": "",
        "invoice_number": f"IV{69 + idx % 3}/{10000 + idx:05d}",
        "date": "2026-07-05", "date_raw": "05/07/2569",
        "subtotal": m(sub), "vat": m(vat), "wht_rate": "", "wht_amount": "", "discount": "0.00",
        "total_amount": m(total), "cash_amount": "", "change_amount": "", "payment_method": "transfer",
        "currency": "", "items": its, "items_count": len(its), "notes": "", "category": "ค่าใช้จ่าย",
        "additional_invoices": [], "scenario": scenario, "traps": traps, "degradation": degs,
        "_note": "", "layout": layout, "extras": [],
    }
def tune(case, trap_no, v):
    sub = d(case["subtotal"])
    if trap_no == 1:
        case["items"] = [{"name": "ข้าวกล่อง", "qty": "1", "price": "109.00", "subtotal": "109.00"}, {"name": "น้ำดื่ม", "qty": "1", "price": "10.00", "subtotal": "10.00"}, {"name": "กาแฟเย็น", "qty": "1", "price": "48.00", "subtotal": "48.00"}]
        case.update(document_type="simplified_tax_invoice", total_amount="167.00", subtotal="167.00", vat="0.00", cash_amount="200.00", change_amount="33.00", payment_method="cash")
        case["extras"] += [("เงินสดรับมา", "200.00"), ("เงินทอน", "33.00")]
    elif trap_no == 2:
        case["items"] = [{"name": "ชาไทย 3 แก้ว แก้วละ 50", "qty": "3", "price": "50.00", "subtotal": "150.00"}]
        case.update(subtotal="150.00", vat="0.00", total_amount="150.00", items_count=1)
    elif trap_no == 3:
        case["extras"] += [("โทร 089-123-4567", ""), ("สมาชิก 7000123456789", ""), ("POS 202607050001", "")]
    elif trap_no == 4:
        case["extras"] += [("สะสมแต้ม", "560"), ("ประหยัด ฿26", "")]
    elif trap_no == 5:
        case["extras"] += [("ก่อนภาษี", m(sub)), ("ภาษีมูลค่าเพิ่ม 7%", case["vat"]), ("ปัดเศษ", "-0.03")]
        case["total_amount"] = m(d(case["total_amount"]) - Decimal("0.03"))
    elif trap_no == 6:
        if v % 3 == 0:
            case["extras"].append(("VAT INCLUDED", ""))
        elif v % 3 == 1:
            case["extras"].append(("VAT EXCLUDED", case["vat"]))
        else:
            case.update(vat="0.00", total_amount=case["subtotal"]); case["extras"].append(("NON VAT", "0.00"))
    elif trap_no == 7:
        case["items"] = [{"name": "ค่าบริการที่ปรึกษา", "qty": "1", "price": "1000.00", "subtotal": "1000.00"}]
        case.update(subtotal="1000.00", vat="70.00", wht_rate="3", wht_amount="30.00", total_amount="1040.00")
        case["extras"] += [("หัก ณ ที่จ่าย 3%", "30.00"), ("จ่ายสุทธิ", "1040.00")]
    elif trap_no == 8:
        case.update(discount="50.00", total_amount=m(d(case["total_amount"]) - 50))
        case["extras"].append(("ส่วนลดสมาชิก", "50.00"))
    elif trap_no == 9:
        raw = ["05/07/69", "5 ก.ค. 2569", "2026/07/05", "05-07-2567", "07/05/69"][v]
        case.update(date_raw=raw, date="2026-07-05" if v != 3 else "2024-07-05")
    elif trap_no == 10:
        case["items"] = [{"name": "Airport shuttle service", "qty": "1", "price": "110.75", "subtotal": "110.75"}]
        case.update(currency="USD" if v % 2 else "EUR", total_amount="118.50", subtotal="110.75", vat="7.75")
        case["extras"].append(("Foreign currency", case["currency"]))
    elif trap_no == 11:
        case["layout"] = "multi"
        case["additional_invoices"] = [base_case(f"{case['id']}_B", "multi_invoice_same_image", ["same_image_extra_invoice"], [], v + 40), base_case(f"{case['id']}_C", "multi_invoice_same_image", ["same_image_extra_invoice"], [], v + 50)]
    elif trap_no == 12:
        docs = [("ใบสั่งซื้อ / PURCHASE ORDER", "order_evidence"), ("ใบเสนอราคา / QUOTATION", "other"), ("ใบส่งของ / DELIVERY NOTE", "other"), ("COPY สำเนา", "other"), ("ใบจองสินค้า", "order_evidence")]
        title, dtype = docs[v % len(docs)]
        case.update(layout="doc", doc_title=title, document_type=dtype, is_not_invoice=True, is_copy_or_duplicate="COPY" in title)
    elif trap_no == 13:
        case["layout"] = "dense"
        case["items"] = [{"name": ITEMS[i % len(ITEMS)][0], "qty": "1", "price": m(18 + i * 7.25), "subtotal": m(18 + i * 7.25)} for i in range(18)]
        sub = sum(d(x["subtotal"]) for x in case["items"]); vat = d(sub * Decimal("0.07"))
        case.update(subtotal=m(sub), vat=m(vat), total_amount=m(sub + vat), items_count=18)
    elif trap_no == 14:
        case.update(layout="a4", handwritten=True)
    elif trap_no == 15:
        case.update(layout="stack")
        case["extras"] += [("คงเหลือ 12,450.00", ""), ("ยอดก่อนหน้า 11,840.00", "")]
    elif trap_no == 16:
        case["printed_only_items"] = [{"name": "ของแถมโปรโมชั่น 0 บาท", "qty": "1", "price": "0.00", "subtotal": "0.00"}]
        case["extras"].append(("บริจาค 0 บาท", "0.00"))
    case["_note"] = "; ".join(case["traps"] + case["degradation"])
    case["items_count"] = len(case["items"])
    return case
TRAP_NAMES = {
    1: ("cash_change_trap", ["cash_gt_total", "change_line"]),
    2: ("qty_unit_price_trap", ["qty_looks_like_amount", "unit_price_only"]),
    3: ("long_digit_interference", ["phone_no", "member_no", "pos_no"]),
    4: ("points_saving_trap", ["loyalty_points", "saving_not_discount"]),
    5: ("competing_amounts", ["gross_vat_rounding_total"]),
    6: ("vat_three_states", ["vat_included_excluded_none"]),
    7: ("wht_withholding", ["wht_rate_amount"]),
    8: ("discount_net_payable", ["discount_line"]),
    9: ("thai_buddhist_date", ["be_year", "two_digit_year"]),
    10: ("foreign_currency", ["foreign_currency"]),
    11: ("multi_invoice_same_image", ["same_image_multi_invoice"]),
    12: ("non_invoice_decoy", ["po_quote_delivery_copy"]),
    13: ("dense_micro_rows", ["micro_text", "many_line_items"]),
    14: ("handwritten_total", ["handwritten_amount"]),
    15: ("stacked_vertical_layout", ["stacked_columns"]),
    16: ("zero_baht_promo", ["zero_baht_promo_line"]),
}
def gt_invoice(case):
    skip = {"layout", "extras", "printed_only_items", "handwritten", "doc_title"}
    out = {k: v for k, v in case.items() if k not in skip}
    out["additional_invoices"] = [gt_invoice(x) for x in out.get("additional_invoices", [])]
    return out
def generate_invoices(manifest):
    for i in range(10):
        c = base_case(f"base_sharp_{i + 1:03d}", "sharp_baseline", [], [], i, "pos" if i % 2 else "a4")
        img = render_invoice(c)
        save_img(img, OUT / "images" / c["file"])
        jdump(OUT / "ground_truth" / f"{c['id']}.json", gt_invoice(c))
        manifest.append({"id": c["id"], "file": "images/" + c["file"], "gt": f"ground_truth/{c['id']}.json", "scenario": c["scenario"], "traps": [], "degradation": []})
    seq = 1
    for trap_no, (scn, traps) in TRAP_NAMES.items():
        reps = 6 if trap_no == 12 else 5
        for v in range(reps):
            deg = DEGS[v % len(DEGS)]
            cid = f"trap{trap_no:02d}_{scn}_{v + 1:03d}"
            c = tune(base_case(cid, scn, traps[:], deg[:], seq, "pos"), trap_no, v)
            img = degrade(render_invoice(c), deg, 1000 + seq)
            save_img(img, OUT / "images" / c["file"])
            jdump(OUT / "ground_truth" / f"{c['id']}.json", gt_invoice(c))
            manifest.append({"id": c["id"], "file": "images/" + c["file"], "gt": f"ground_truth/{c['id']}.json", "scenario": scn, "traps": c["traps"], "degradation": deg})
            seq += 1
def table_image(title, meta, headers, rows, totals=None):
    w, h = 1700, 1200
    img = Image.new("RGB", (w, h), (255, 255, 252))
    draw = ImageDraw.Draw(img)
    center(draw, 34, title, fnt(40, True), w)
    y = 100
    for s in meta:
        draw.text((70, y), s, font=fnt(25), fill=(20, 20, 20)); y += 32
    y += 14
    widths = [150, 560, 190, 190, 190, 220][: len(headers)]
    x0 = 60
    xs = [x0]
    for ww in widths:
        xs.append(xs[-1] + ww)
    for x in xs:
        draw.line((x, y, x, 1040), fill=(70, 70, 70), width=1)
    draw.line((x0, y, xs[-1], y), fill=(70, 70, 70), width=2)
    for x, hdr in zip(xs, headers):
        draw.text((x + 8, y + 10), hdr, font=fnt(22, True), fill=(20, 20, 20))
    y += 48
    small = fnt(18 if len(rows) > 16 else 21)
    for row in rows:
        draw.line((x0, y, xs[-1], y), fill=(205, 205, 205), width=1)
        for x, val in zip(xs, row):
            draw.text((x + 8, y + 8), str(val)[:42], font=small, fill=(20, 20, 20))
        y += 38 if len(rows) > 16 else 44
        if y > 1010:
            break
    draw.line((x0, y, xs[-1], y), fill=(70, 70, 70), width=2)
    y += 28
    for k, v in (totals or []):
        draw.text((1040, y), k, font=fnt(24, True), fill=(20, 20, 20)); right(draw, (1560, y), v, fnt(24, True)); y += 32
    return img
def bank_case(i):
    banks = [("ธนาคารกสิกรไทย", "kbank"), ("ธนาคารไทยพาณิชย์", "scb"), ("ธนาคารกรุงเทพ", "bbl"), ("ธนาคารกรุงไทย", "ktb"), ("ธนาคารกรุงศรี", "bay"), ("ธนาคารทหารไทยธนชาต", "ttb")]
    bank = banks[i % len(banks)]
    opening = d(-35000 if i < 6 else 10000 + i * 771)
    bal = opening; entries = []
    for r in range(10 + i % 9):
        dep = d(0); wd = d(0)
        if (r + i) % 3 == 0:
            dep = d(2500 + r * 211 + i * 17); bal += dep; direction = "deposit"
        else:
            wd = d(1430 + r * 137 + i * 19); bal -= wd; direction = "withdrawal"
        entries.append({"transaction_date": f"2025-12-{r + 1:02d}", "description": f"โอนเงิน REF{i:02d}{r:04d}", "reference": "KPLUS", "deposit": m(dep) if dep else "", "withdrawal": m(wd) if wd else "", "amount": m(dep or wd), "balance": m(bal), "direction": direction})
    traps = []
    if i < 6: traps.append("overdraft_negative")
    if i % 6 in (0, 1): traps.append("stacked_columns")
    if i % 8 == 0: traps.append("partial_page_only")
    deg = [["phone_photo_skew", "shadow"], ["flatbed_scan"], ["glare"], ["fold_crease"], ["low_res", "jpeg_artifact"], ["moire"], ["dark"], ["overexposed"]][i % 8]
    cid = f"bank_{bank[1]}_{i + 1:02d}"
    total_dep = sum(d(e["deposit"] or 0) for e in entries); total_wd = sum(d(e["withdrawal"] or 0) for e in entries)
    data = {"id": cid, "file": f"bank/images/{cid}.jpg", "doc_type": "bank_statement", "document_type": "bank_statement", "bank_name": bank[0], "bank_code": bank[1], "account_name": "บริษัท ดาต้าทูลส์ จำกัด", "account_number": f"102-3-{82640+i:05d}-{i%10}", "account_last4": f"{82640+i:04d}"[-4:], "period_start": "2025-12-01", "period_end": "2025-12-31", "opening_balance": m(opening), "closing_balance": m(bal), "entry_count": len(entries), "total_deposit": m(total_dep), "total_withdrawal": m(total_wd), "entries": entries, "scenario": "stacked_columns" if "stacked_columns" in traps else "bank_statement_photo", "traps": traps, "degradation": deg, "_note": "synthetic bank statement with reconciled running balance"}
    rows = [[e["transaction_date"][5:], e["description"], e["reference"], e["withdrawal"], e["deposit"], e["balance"]] for e in entries]
    img = table_image(bank[0], [data["account_name"], data["account_number"], "01/12/2568 - 31/12/2568"], ["Date", "Description", "Ref", "Withdrawal", "Deposit", "Balance"], rows, [("Opening", data["opening_balance"]), ("Closing", data["closing_balance"])])
    return data, degrade(img, deg, 3000 + i)
def gl_case(i):
    cid = f"gl_bank_cash_{i + 1:02d}"
    opening = d(50000 + i * 333); bal = opening; entries = []
    for r in range(12 + i % 6):
        debit = d(1200 + r * 90) if (r + i) % 2 == 0 else d(0)
        credit = d(950 + r * 75) if not debit else d(0)
        bal += debit - credit
        entries.append({"transaction_date": f"2026-01-{r + 1:02d}", "voucher_no": f"JV681{r:03d}.{i}", "account_code": "1112-07", "description": f"รับ/จ่าย เลขงาน 6091-{r}", "debit": m(debit) if debit else "", "credit": m(credit) if credit else "", "amount": m(debit or credit), "direction": "deposit" if debit else "withdrawal", "balance": m(bal)})
    traps = ["stacked_columns"] if i < 4 else []
    if i % 4 == 0: traps.append("voucher_number_like_amount")
    if 4 <= i < 7: traps.append("rounding_tail_difference")
    deg = [["phone_photo_skew"], ["fold_crease", "shadow"], ["low_res"], ["flatbed_scan"], ["glare"], ["moire"]][i % 6]
    total_debit = sum(d(e["debit"] or 0) for e in entries); total_credit = sum(d(e["credit"] or 0) for e in entries)
    data = {"id": cid, "file": f"gl/images/{cid}.jpg", "doc_type": "general_ledger", "document_type": "general_ledger", "period_start": "2026-01-01", "period_end": "2026-01-31", "account_name": "เงินฝากธนาคาร", "account_number": "1112-07", "opening_balance": m(opening), "closing_balance": m(bal), "entry_count": len(entries), "total_debit": m(total_debit), "total_credit": m(total_credit), "entries": entries, "scenario": "gl_stacked" if i < 4 else "gl_photo", "traps": traps, "degradation": deg, "_note": "GL balance chain is continuous"}
    rows = [[e["transaction_date"][5:], e["voucher_no"], e["account_code"], e["description"], e["debit"] or e["credit"], e["balance"]] for e in entries]
    img = table_image("สมุดบัญชีแยกประเภททั่วไป", [data["account_name"], "Period 01/01/2569 - 31/01/2569"], ["Date", "Voucher", "Acct", "Description", "Debit/Credit", "Balance"], rows, [("Total Debit", data["total_debit"]), ("Total Credit", data["total_credit"]), ("Closing", data["closing_balance"])])
    return data, degrade(img, deg, 4000 + i)
def vat_case(i):
    cid = f"vat_{'sales' if i % 2 == 0 else 'purchase'}_{i + 1:02d}"
    report_type = "sales" if i % 2 == 0 else "purchase"; rows = []
    total_sub = total_vat = Decimal("0")
    for r in range(9 + i % 8):
        sub = d(500 + r * 137 + i * 21); vat = d(0 if (i < 3 and r % 4 == 0) else sub * Decimal("0.07"))
        total = sub + vat; total_sub += sub; total_vat += vat
        rows.append({"seq_no": str(r + 1), "transaction_date": f"2026-02-{r + 1:02d}", "transaction_date_raw": f"{r + 1:02d}/02/2569", "invoice_no": f"IV69/{i:02d}{r:03d}", "customer_name": f"บริษัท ลูกค้า {r + 1}", "customer_tax": f"01055{i%10}{r:07d}"[:13], "customer_branch": "สำนักงานใหญ่", "subtotal": m(sub), "vat": m(vat), "total": m(total), "pre_vat_amount": m(sub), "buyer_tax": f"01055{i%10}{r:07d}"[:13]})
    deg = [["phone_photo_skew"], ["flatbed_scan"], ["fold_crease"], ["low_res", "jpeg_artifact"], ["glare"], ["partial_page"]][i % 6]
    traps = []
    if i < 4: traps.append("multi_page_total")
    if i < 3: traps.append("zero_vat_rows")
    total_total = total_sub + total_vat
    data = {"id": cid, "file": f"vat/images/{cid}.jpg", "doc_type": "vat_report", "document_type": "vat_report", "report_type": report_type, "period": "2026-02", "period_year": "2026", "period_month": "02", "seller_name": "บริษัท ดาต้าทูลส์ จำกัด", "seller_tax": "0735527000289", "row_count": len(rows), "total_pre_vat": m(total_sub), "total_subtotal": m(total_sub), "total_vat": m(total_vat), "total_amount": m(total_total), "total_total": m(total_total), "rows": rows, "entries": rows, "scenario": "vat_report_photo", "traps": traps, "degradation": deg, "_note": "row VAT totals reconcile with report summary"}
    table_rows = [[x["seq_no"], x["transaction_date_raw"], x["invoice_no"], x["customer_name"], x["subtotal"], x["vat"]] for x in rows]
    img = table_image("รายงานภาษี" + ("ขาย" if report_type == "sales" else "ซื้อ"), ["บริษัท ดาต้าทูลส์ จำกัด", "เดือน 02/2569"], ["No", "Date", "Invoice", "Customer", "Net", "VAT"], table_rows, [("Total Net", data["total_subtotal"]), ("Total VAT", data["total_vat"]), ("Grand", data["total_total"])])
    return data, degrade(img, deg, 5000 + i)
def generate_recon(manifest):
    for kind, count, maker in [("bank", 24, bank_case), ("gl", 12, gl_case), ("vat", 12, vat_case)]:
        for i in range(count):
            data, img = maker(i)
            save_img(img, OUT / kind / "images" / f"{data['id']}.jpg")
            jdump(OUT / kind / "ground_truth" / f"{data['id']}.json", data)
            manifest.append({"id": data["id"], "file": data["file"], "gt": f"{kind}/ground_truth/{data['id']}.json", "doc_type": data["doc_type"], "scenario": data["scenario"], "traps": data["traps"], "degradation": data["degradation"]})
def main():
    mkdirs()
    invoice_manifest = []
    recon_manifest = []
    generate_invoices(invoice_manifest)
    generate_recon(recon_manifest)
    (OUT / "manifest.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in invoice_manifest), encoding="utf-8")
    (OUT / "manifest_recon.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in recon_manifest), encoding="utf-8")
    summary = {"invoice_count": len(invoice_manifest), "bank_count": 24, "gl_count": 12, "vat_count": 12}
    jdump(OUT / "summary.json", summary)
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if npx:
        subprocess.run([npx, "prettier", "--write", "**/*.json"], cwd=OUT, check=False)
    print(json.dumps(summary, ensure_ascii=False))
if __name__ == "__main__":
    main()
