from __future__ import annotations

import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_REGULAR = [
    "C:/Windows/Fonts/NotoSansThai-Regular.ttf",
    "C:/Windows/Fonts/Sarabun-Regular.ttf",
    "C:/Windows/Fonts/tahoma.ttf",
    "C:/Windows/Fonts/LeelUIsl.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
FONT_BOLD = [
    "C:/Windows/Fonts/NotoSansThai-Bold.ttf",
    "C:/Windows/Fonts/Sarabun-Bold.ttf",
    "C:/Windows/Fonts/tahomabd.ttf",
    "C:/Windows/Fonts/LeelaUIb.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for path in FONT_BOLD if bold else FONT_REGULAR:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.ImageFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), str(text), font=face)
    return right - left, bottom - top


def right_text(
    draw: ImageDraw.ImageDraw, x: int, y: int, text: str, face, fill=(30, 30, 30)
) -> None:
    width, _ = text_size(draw, str(text), face)
    draw.text((x - width, y), str(text), font=face, fill=fill)


def center_text(
    draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, face, fill=(30, 30, 30)
) -> None:
    width, height = text_size(draw, str(text), face)
    x0, y0, x1, y1 = box
    draw.text(
        (x0 + (x1 - x0 - width) / 2, y0 + (y1 - y0 - height) / 2), str(text), font=face, fill=fill
    )


def paper(width: int, height: int, color=(250, 248, 238)) -> Image.Image:
    base = Image.new("RGB", (width, height), color)
    noise = np.random.default_rng(width + height).normal(0, 2.2, (height, width, 1))
    arr = np.array(base).astype(np.float32) + noise
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def render_invoice_paper(case: dict) -> Image.Image:
    gt = case["gt"]
    if gt["is_not_invoice"]:
        return _render_non_invoice(case)
    if case["render"]["kind"] == "receipt":
        return _render_receipt(case)
    return _render_invoice_a4(case)


def _render_receipt(case: dict) -> Image.Image:
    gt = case["gt"]
    rows = len(gt["items"])
    height = 720 + rows * 74 + (220 if gt["additional_invoices"] else 0)
    img = paper(760, height, (247, 245, 231))
    draw = ImageDraw.Draw(img)
    small = font(26)
    normal = font(31)
    bold = font(35, True)
    y = 34
    center_text(draw, (0, y, 760, y + 44), gt["seller_name"], bold)
    y += 52
    center_text(draw, (0, y, 760, y + 36), gt["seller_addr"][:58], small)
    y += 42
    center_text(draw, (0, y, 760, y + 42), _invoice_title(gt), bold)
    y += 58
    draw.text((44, y), f"No: {gt['invoice_number']}", font=normal, fill=(25, 25, 25))
    y += 42
    draw.text((44, y), f"Date: {gt['date_raw']}", font=normal, fill=(25, 25, 25))
    if gt["is_copy_or_duplicate"]:
        draw.text((470, y - 42), "COPY", font=font(48, True), fill=(150, 20, 20))
    y += 56
    _dash(draw, y, 760)
    y += 28
    for item in gt["items"]:
        draw.text((44, y), item["name"][:31], font=normal, fill=(20, 20, 20))
        right_text(draw, 710, y, _print_money(item["subtotal"], gt["currency"]), normal)
        y += 38
        draw.text((70, y), f"{item['qty']} x {item['price']}", font=small, fill=(70, 70, 70))
        y += 44
    _dash(draw, y, 760)
    y += 34
    y = _total_line(draw, y, "Subtotal", gt["subtotal"], normal, 710, gt["currency"])
    if gt["discount"]:
        y = _total_line(draw, y, "Discount", gt["discount"], normal, 710, gt["currency"])
    y = _total_line(draw, y, "VAT", gt["vat"], normal, 710, gt["currency"])
    if gt["wht_amount"]:
        y = _total_line(draw, y, "WHT", gt["wht_amount"], normal, 710, gt["currency"])
    y += 6
    y = _total_line(draw, y, "TOTAL", gt["total_amount"], bold, 710, gt["currency"])
    if gt["cash_amount"]:
        y = _total_line(draw, y, "Cash", gt["cash_amount"], normal, 710, gt["currency"])
        y = _total_line(draw, y, "Change", gt["change_amount"], normal, 710, gt["currency"])
    if gt["buyer_name"]:
        y += 20
        draw.text((44, y), f"Buyer: {gt['buyer_name'][:42]}", font=small, fill=(50, 50, 50))
        y += 34
        draw.text((44, y), f"Tax ID: {gt['buyer_tax']}", font=small, fill=(50, 50, 50))
    if gt["additional_invoices"]:
        y += 50
        _dash(draw, y, 760)
        y += 26
        draw.text((44, y), "Second invoice on same page:", font=small, fill=(60, 60, 60))
        y += 36
        extra = gt["additional_invoices"][0]
        draw.text(
            (44, y),
            f"{extra['invoice_number']} total {extra['total_amount']}",
            font=small,
            fill=(40, 40, 40),
        )
    if "handwritten" in case["trap"]:
        _handwrite(draw, 66, height - 135, "approved / paid", seed=13)
    return img


def _render_invoice_a4(case: dict) -> Image.Image:
    gt = case["gt"]
    img = paper(1240, 1754, (252, 251, 244))
    draw = ImageDraw.Draw(img)
    normal = font(31)
    small = font(25)
    bold = font(40, True)
    draw.rectangle((0, 0, 1240, 96), fill=(38, 43, 56))
    draw.text((64, 26), gt["seller_name"], font=bold, fill=(255, 255, 255))
    center_text(draw, (820, 22, 1180, 82), _invoice_title(gt), font(34, True), fill=(255, 255, 255))
    draw.text((64, 126), gt["seller_addr"], font=small, fill=(40, 40, 40))
    draw.text((64, 166), f"Tax ID {gt['seller_tax']}", font=small, fill=(40, 40, 40))
    draw.text((820, 128), f"No. {gt['invoice_number']}", font=normal, fill=(25, 25, 25))
    draw.text((820, 170), f"Date {gt['date_raw']}", font=normal, fill=(25, 25, 25))
    draw.rounded_rectangle((64, 244, 1168, 398), radius=12, outline=(180, 180, 180), width=2)
    draw.text((92, 270), "Buyer", font=font(28, True), fill=(50, 50, 50))
    draw.text((92, 312), gt["buyer_name"] or "Walk-in customer", font=normal, fill=(20, 20, 20))
    draw.text((92, 354), gt["buyer_tax"] or "-", font=small, fill=(60, 60, 60))
    headers = ["Item", "Qty", "Unit", "Amount"]
    rows = [[i["name"], i["qty"], i["price"], i["subtotal"]] for i in gt["items"]]
    _grid(draw, 64, 456, [650, 130, 170, 230], 54, headers, rows, 40)
    y = 456 + 54 + len(rows) * 54 + 36
    if gt["is_copy_or_duplicate"]:
        draw.text((760, y - 24), "COPY", font=font(92, True), fill=(150, 35, 35))
    y = _total_line(draw, y, "Subtotal", gt["subtotal"], normal, 1135, gt["currency"], 780)
    if gt["discount"]:
        y = _total_line(draw, y, "Discount", gt["discount"], normal, 1135, gt["currency"], 780)
    y = _total_line(draw, y, "VAT", gt["vat"], normal, 1135, gt["currency"], 780)
    if gt["wht_amount"]:
        y = _total_line(draw, y, "WHT", gt["wht_amount"], normal, 1135, gt["currency"], 780)
    y += 14
    y = _total_line(
        draw, y, "Grand Total", gt["total_amount"], font(38, True), 1135, gt["currency"], 780
    )
    if gt["notes"]:
        draw.text((64, 1540), gt["notes"][:80], font=small, fill=(70, 70, 70))
    if "handwritten" in case["trap"]:
        _handwrite(draw, 84, 1450, "manager checked", seed=case["id"].count("v"))
    return img


def _render_non_invoice(case: dict) -> Image.Image:
    img = paper(1040, 1380, (250, 249, 242))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 1040, 110), fill=(62, 72, 84))
    draw.text((70, 36), "Purchase Memo", font=font(42, True), fill=(255, 255, 255))
    draw.text(
        (70, 170),
        "This is a synthetic internal memo, not a tax invoice.",
        font=font(32),
        fill=(35, 35, 35),
    )
    draw.text((70, 230), "Topic: supplier quotation review", font=font(31), fill=(35, 35, 35))
    for index in range(12):
        y = 330 + index * 62
        draw.line((70, y, 970, y), fill=(190, 190, 185), width=2)
        draw.text(
            (82, y + 12),
            f"{index + 1}. review item {6091 + index} / not an amount",
            font=font(25),
            fill=(65, 65, 65),
        )
    _handwrite(draw, 90, 1160, "please compare vendors", seed=9)
    return img


def render_bank_paper(case: dict) -> Image.Image:
    gt = case["gt"]
    theme = tuple(case["render"]["theme"])
    img = paper(1700, 1200, (252, 252, 246))
    draw = ImageDraw.Draw(img)
    dark = _readable_text(theme)
    draw.rectangle((0, 0, 1700, 118), fill=theme)
    draw.text((70, 32), gt["bank_name"], font=font(42, True), fill=dark)
    draw.text((1160, 38), "Synthetic Account Statement", font=font(31, True), fill=dark)
    draw.text(
        (70, 154),
        f"Account: {gt['account_name']}  {gt['account_number']}",
        font=font(29),
        fill=(30, 30, 30),
    )
    draw.text(
        (70, 197),
        f"Period: {gt['period_start']} to {gt['period_end']}",
        font=font(27),
        fill=(55, 55, 55),
    )
    draw.text((1180, 154), f"Opening {gt['opening_balance']}", font=font(28), fill=(30, 30, 30))
    draw.text(
        (1180, 197), f"Closing {gt['closing_balance']}", font=font(28, True), fill=(30, 30, 30)
    )
    headers = ["Date", "Description", "Reference", "Withdrawal", "Deposit", "Balance"]
    rows = [
        [
            e["transaction_date_raw"],
            e["description"][:36],
            e["reference"],
            e["withdrawal"],
            e["deposit"],
            e["balance"],
        ]
        for e in gt["entries"]
    ]
    y = 272
    widths = [160, 500, 260, 230, 210, 230]
    if case["render"]["variant"] % 3 == 1:
        widths = [165, 470, 290, 210, 220, 235]
    _grid(draw, 55, y, widths, 50, headers, rows, 43, header_fill=_soft_color(theme))
    draw.text(
        (70, 1118),
        "Layout skeleton only. All account data is synthetic.",
        font=font(23),
        fill=(80, 80, 80),
    )
    return img


def render_gl_paper(case: dict) -> Image.Image:
    gt = case["gt"]
    img = paper(1650, 1160, (252, 251, 244))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 1650, 105), fill=(52, 65, 75))
    draw.text((62, 30), "General Ledger - Bank Account", font=font(39, True), fill=(255, 255, 255))
    draw.text(
        (62, 142),
        f"Account {gt['account_number']} / {gt['account_name']}",
        font=font(29),
        fill=(35, 35, 35),
    )
    draw.text(
        (62, 184),
        f"Period {gt['period_start']} to {gt['period_end']}",
        font=font(27),
        fill=(60, 60, 60),
    )
    headers = ["Date", "Voucher", "Account", "Description", "Debit", "Credit", "Balance"]
    rows = [
        [
            e["transaction_date_raw"],
            e["voucher_no"],
            e["account_code"],
            e["description"][:32],
            e["debit"],
            e["credit"],
            e["balance"],
        ]
        for e in gt["entries"]
    ]
    _grid(draw, 45, 260, [145, 185, 140, 430, 200, 200, 220], 48, headers, rows, 41)
    draw.text(
        (62, 1084),
        f"Opening {gt['opening_balance']}   Closing {gt['closing_balance']}",
        font=font(27, True),
        fill=(30, 30, 30),
    )
    return img


def render_vat_paper(case: dict) -> Image.Image:
    gt = case["gt"]
    img = paper(1650, 1160, (252, 251, 244))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 1650, 105), fill=(86, 55, 96))
    draw.text((62, 30), "VAT Report", font=font(40, True), fill=(255, 255, 255))
    draw.text(
        (62, 142),
        f"{gt['seller_name']}  Tax ID {gt['seller_tax']}",
        font=font(28),
        fill=(35, 35, 35),
    )
    draw.text(
        (62, 184),
        f"Period {gt['period_month']}/{gt['period_year']}",
        font=font(27),
        fill=(60, 60, 60),
    )
    headers = ["No", "Date", "Invoice", "Customer", "Tax ID", "Subtotal", "VAT", "Total"]
    rows = [
        [
            e["seq_no"],
            e["transaction_date_raw"],
            e["invoice_no"],
            e["customer_name"][:26],
            e["customer_tax"],
            e["subtotal"],
            e["vat"],
            e["total"],
        ]
        for e in gt["entries"]
    ]
    _grid(draw, 42, 260, [70, 135, 225, 350, 210, 185, 155, 185], 47, headers, rows, 40)
    draw.text(
        (840, 1082),
        f"Totals {gt['total_subtotal']} / VAT {gt['total_vat']} / Grand {gt['total_total']}",
        font=font(27, True),
        fill=(30, 30, 30),
    )
    return img


def _grid(
    draw,
    x: int,
    y: int,
    widths: list[int],
    row_h: int,
    headers: list[str],
    rows: list[list[str]],
    font_size: int,
    header_fill=None,
) -> None:
    header_fill = header_fill or (224, 228, 232)
    face = font(font_size - 12)
    head_face = font(font_size - 10, True)
    total_w = sum(widths)
    draw.rectangle((x, y, x + total_w, y + row_h), fill=header_fill, outline=(120, 120, 120))
    cursor = x
    for idx, header in enumerate(headers):
        draw.rectangle(
            (cursor, y, cursor + widths[idx], y + row_h), outline=(130, 130, 130), width=2
        )
        draw.text((cursor + 10, y + 13), header, font=head_face, fill=(30, 30, 30))
        cursor += widths[idx]
    for row_index, row in enumerate(rows):
        top = y + row_h + row_index * row_h
        fill = (255, 255, 250) if row_index % 2 else (244, 245, 241)
        draw.rectangle((x, top, x + total_w, top + row_h), fill=fill, outline=(170, 170, 170))
        cursor = x
        for col_index, value in enumerate(row):
            value = str(value or "")
            box = (cursor, top, cursor + widths[col_index], top + row_h)
            if col_index >= len(row) - 3:
                right_text(draw, box[2] - 10, top + 13, value, face, fill=(28, 28, 28))
            else:
                draw.text((cursor + 10, top + 13), value, font=face, fill=(28, 28, 28))
            cursor += widths[col_index]


def _dash(draw: ImageDraw.ImageDraw, y: int, width: int) -> None:
    for x in range(38, width - 38, 22):
        draw.line((x, y, x + 12, y), fill=(35, 35, 35), width=2)


def _total_line(
    draw,
    y: int,
    label: str,
    value: str | None,
    face,
    right: int,
    currency: str = "",
    left: int = 44,
) -> int:
    draw.text((left, y), label, font=face, fill=(25, 25, 25))
    right_text(draw, right, y, _print_money(value or "", currency), face, fill=(25, 25, 25))
    return y + int(face.size * 1.25)


def _print_money(value: str, currency: str = "") -> str:
    if not value:
        return ""
    printed = f"({value[1:]})" if value.startswith("-") else value
    return f"{printed} {currency}".rstrip()


def _invoice_title(gt: dict) -> str:
    return {
        "tax_invoice": "ใบกำกับภาษี / TAX INVOICE",
        "simplified_tax_invoice": "ใบกำกับภาษีอย่างย่อ",
        "credit_note": "ใบลดหนี้ / CREDIT NOTE",
    }.get(gt["document_type"], "เอกสาร")


def _handwrite(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, seed: int) -> None:
    rng = random.Random(seed)
    face = font(36)
    for idx, char in enumerate(text):
        draw.text(
            (x + idx * 17 + rng.randint(-1, 2), y + rng.randint(-2, 2)),
            char,
            font=face,
            fill=(28, 55, 142),
        )
    draw.line((x - 6, y + 48, x + len(text) * 18, y + 55), fill=(28, 55, 142), width=3)


def _soft_color(color: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(int(c * 0.22 + 220 * 0.78) for c in color)


def _readable_text(color: tuple[int, int, int]) -> tuple[int, int, int]:
    luminance = 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]
    return (30, 30, 30) if luminance > 155 else (255, 255, 255)
