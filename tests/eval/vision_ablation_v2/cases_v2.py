from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def money(value: Decimal | int | str) -> str:
    return str(Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP))


def tax_id(seed: int) -> str:
    # 前 12 位定型后补 mod-11 校验位:生产 sanity 有真校验闸,假校验位的语料税号
    # 会把回落率打爆(P1 台账 #4·2026-07-05 实弹坐实),语料必须发合法税号。
    base = f"01055{seed % 10000000:07d}"
    s = sum(int(base[i]) * (13 - i) for i in range(12))
    return base + str((11 - s % 11) % 10)


def iso_date(index: int) -> tuple[str, str]:
    day = date(2026, 6, 1) + timedelta(days=index % 28)
    if index % 11 == 0:
        return day.isoformat(), f"{day.day:02d}/{day.month:02d}/{day.year + 543}"
    if index % 7 == 0:
        return day.isoformat(), f"{day.day:02d}/{day.month:02d}/{str(day.year)[-2:]}"
    return day.isoformat(), f"{day.day:02d}/{day.month:02d}/{day.year}"


SELLERS = [
    ("Bangkok Office Supply Co., Ltd.", "123 Silom Road, Bang Rak, Bangkok"),
    ("Nakhon Fresh Mart Ltd.", "45 Mittraphap Road, Muang, Khon Kaen"),
    ("Siam Service Point Co., Ltd.", "88 Rama IX Road, Huai Khwang, Bangkok"),
    ("Plern Coffee Roasters Ltd.", "14 Nimman Road, Muang, Chiang Mai"),
    ("Thai Packaging Hub Co., Ltd.", "29 Theparak Road, Samut Prakan"),
    ("Aroi Dee Restaurant Ltd.", "77 Sukhumvit 31, Bangkok"),
]

BUYERS = [
    ("Pearnly Retail Co., Ltd.", "99/18 Sathorn Road, Bangkok"),
    ("Mango Cloud Accounting Ltd.", "12 Wireless Road, Bangkok"),
    ("Lotus Field Trading Co., Ltd.", "66 Chan Road, Bangkok"),
    ("North Star Clinic Co., Ltd.", "21 Phahonyothin Road, Bangkok"),
]

PRODUCTS = [
    ("กระดาษ A4 80 แกรม", "ream"),
    ("หมึกพิมพ์ HP 680", "pc"),
    ("กาแฟคั่วกลาง 250g", "bag"),
    ("ค่าบริการจัดส่ง", "job"),
    ("ข้าวกล่องพนักงาน", "box"),
    ("น้ำดื่ม 600ml", "pack"),
    ("อุปกรณ์ทำความสะอาด", "set"),
    ("ค่าซ่อมเครื่องพิมพ์", "job"),
]

TRAPS = [
    "baseline",
    "thermal_receipt",
    "cash_change",
    "quantity_as_amount",
    "zero_total",
    "discount_before_vat",
    "wht",
    "long_numbers",
    "thai_date",
    "copy_duplicate",
    "credit_note",
    "foreign_currency",
    "non_invoice",
    "handwritten_note",
    "overlapping_columns",
    "thousands_sticky",
    "multi_invoice",
    "tax_exempt",
]

PHOTO_PROFILES = [
    "wood_table_angle",
    "laminated_counter_shadow",
    "handheld_low_light",
    "folded_receipt",
    "curled_a4",
    "coffee_stain",
    "motion_blur",
    "phone_flash",
]

BANK_SOURCES = {
    "kbank": {
        "name": "KASIKORNBANK",
        "color": (37, 139, 64),
        "url": "https://www.kasikornbank.com/en/personal/Digital-banking/kplus/functions/request-statement/Pages/index.html",
        "note": "K PLUS request statement workflow, skeleton only.",
    },
    "scb": {
        "name": "Siam Commercial Bank",
        "color": (77, 45, 135),
        "url": "https://www.scb.co.th/en/personal-banking/digital-banking/scb-easy/how-to/request-statement",
        "note": "SCB EASY account statement request workflow, skeleton only.",
    },
    "bbl": {
        "name": "Bangkok Bank",
        "color": (22, 88, 170),
        "url": "https://www.bangkokbank.com/en/Personal/Digital-Banking/dStatement",
        "note": "Bangkok Bank dStatement service page, skeleton only.",
    },
    "bay": {
        "name": "Krungsri Bank",
        "color": (255, 198, 41),
        "url": "https://www.krungsri.com/en/business/digital-solutions/sme-solutions/krungsri-biz-online/recommend-new-service/statement-1-year",
        "note": "Krungsri Biz Online statement request guide, skeleton only.",
    },
    "ttb": {
        "name": "TMBThanachart Bank",
        "color": (20, 104, 190),
        "url": "https://www.ttbbank.com/en/ttb-touch/userguide/deposit-enriched-statement",
        "note": "ttb Touch generated deposit statement guide, skeleton only.",
    },
    "gsb": {
        "name": "Government Savings Bank",
        "color": (231, 50, 137),
        "url": "https://www.gsb.or.th/online_service/estatement-savings/",
        "note": "GSB MyMo e-statement request page, skeleton only.",
    },
    "ktb": {
        "name": "Krungthai Bank",
        "color": (16, 157, 219),
        "url": "https://krungthai.com/th/content/personal/krungthai-next/request-statement",
        "note": "Krungthai NEXT statement request guide, skeleton only.",
    },
}


def invoice_cases() -> list[dict]:
    cases: list[dict] = []
    for index in range(90):
        trap = TRAPS[index % len(TRAPS)]
        case = _invoice_case(index + 1, trap)
        cases.append(case)
    return cases


def _invoice_case(seq: int, trap: str) -> dict:
    seller = SELLERS[seq % len(SELLERS)]
    buyer = BUYERS[(seq // 2) % len(BUYERS)]
    doc_type = "simplified_tax_invoice" if trap == "thermal_receipt" else "tax_invoice"
    doc_type = "credit_note" if trap == "credit_note" else doc_type
    is_not_invoice = trap == "non_invoice"
    is_copy = trap == "copy_duplicate"
    inv_no = f"IV26-{seq:05d}" if not is_not_invoice else None
    if trap == "long_numbers":
        inv_no = f"INV-2026-0000-{seq:06d}-BKK-WH-09"
    date_value, date_raw = iso_date(seq)
    if trap == "thai_date":
        date_raw = date_raw if "2569" in date_raw else date_raw[:6] + "2569"
    items, subtotal = _invoice_items(seq, trap)
    discount = Decimal("0.00")
    if trap in {"discount_before_vat", "overlapping_columns"}:
        discount = (subtotal * Decimal("0.05")).quantize(CENT)
    taxable = subtotal - discount
    vat = (
        Decimal("0.00")
        if trap in {"foreign_currency", "tax_exempt", "zero_total"}
        else taxable * Decimal("0.07")
    )
    wht_rate = "3.00" if trap == "wht" else ""
    wht_amount = taxable * Decimal("0.03") if trap == "wht" else Decimal("0.00")
    total = taxable + vat - wht_amount
    currency = "USD" if trap == "foreign_currency" else ""
    if trap == "zero_total":
        subtotal = discount = vat = wht_amount = total = Decimal("0.00")
        items = [{"name": "ส่วนลดคูปองเต็มจำนวน", "qty": "1", "price": "0.00", "subtotal": "0.00"}]
    if trap == "credit_note":
        subtotal, vat, total = -abs(subtotal), -abs(vat), -abs(total)
        for item in items:
            item["price"] = "-" + item["price"]
            item["subtotal"] = "-" + item["subtotal"]
    if is_not_invoice:
        inv_no = None
        items = []
        subtotal = vat = discount = wht_amount = Decimal("0.00")
        total_amount = None
        doc_type = "other"
    else:
        total_amount = money(total)
    cash_amount = ""
    change_amount = ""
    payment = "transfer" if seq % 4 == 0 else "cash"
    if trap == "cash_change":
        paid = ((total // Decimal("100")) + 1) * Decimal("100")
        cash_amount = money(paid)
        change_amount = money(paid - total)
        payment = "cash"
    gt = {
        "document_type": doc_type,
        "is_not_invoice": is_not_invoice,
        "is_copy_or_duplicate": is_copy,
        "invoice_number": inv_no,
        "date": date_value if not is_not_invoice else None,
        "date_raw": date_raw if not is_not_invoice else "",
        "seller_name": seller[0] if not is_not_invoice else "",
        "seller_tax": tax_id(seq) if not is_not_invoice else "",
        "seller_addr": seller[1] if not is_not_invoice else "",
        "buyer_name": buyer[0] if doc_type == "tax_invoice" else "",
        "buyer_tax": tax_id(seq + 9000) if doc_type == "tax_invoice" else "",
        "buyer_addr": buyer[1] if doc_type == "tax_invoice" else "",
        "subtotal": money(subtotal) if not is_not_invoice else "",
        "vat": money(vat) if not is_not_invoice else "",
        "wht_rate": wht_rate,
        "wht_amount": money(wht_amount) if trap == "wht" else "",
        "discount": money(discount) if discount else "",
        "total_amount": total_amount,
        "cash_amount": cash_amount,
        "change_amount": change_amount,
        "payment_method": payment if not is_not_invoice else "",
        "currency": currency,
        "items": items,
        "notes": _invoice_note(trap),
        "category": "office" if seq % 2 else "food",
        "additional_invoices": [_extra_invoice(seq)] if trap == "multi_invoice" else [],
    }
    kind = (
        "receipt"
        if trap in {"thermal_receipt", "cash_change", "folded_receipt"} or seq % 3
        else "a4"
    )
    return {
        "id": f"inv_v2_{seq:03d}",
        "image": f"images/inv_v2_{seq:03d}.jpg",
        "ground_truth": f"ground_truth/inv_v2_{seq:03d}.json",
        "trap": trap,
        "photo_profile": PHOTO_PROFILES[seq % len(PHOTO_PROFILES)],
        "render": {"kind": kind},
        "gt": gt,
    }


def _invoice_items(seq: int, trap: str) -> tuple[list[dict], Decimal]:
    rows = 1 + (seq % 4)
    if trap == "quantity_as_amount":
        rows = 2
    items = []
    subtotal = Decimal("0.00")
    for offset in range(rows):
        name, unit = PRODUCTS[(seq + offset) % len(PRODUCTS)]
        qty = Decimal((seq + offset) % 4 + 1)
        price = Decimal(35 + ((seq * 17 + offset * 29) % 480))
        if trap == "foreign_currency":
            price = Decimal("12.50") + Decimal(offset * 4)
        if trap == "quantity_as_amount" and offset == 0:
            name = "จำนวนสินค้า 6091 ห้ามอ่านเป็นยอดเงิน"
            qty = Decimal("6091")
            price = Decimal("1.00")
        line_total = qty * price
        subtotal += line_total
        items.append(
            {
                "name": f"{name} ({unit})",
                "qty": money(qty).rstrip("0").rstrip("."),
                "price": money(price),
                "subtotal": money(line_total),
            }
        )
    return items, subtotal


def _invoice_note(trap: str) -> str:
    notes = {
        "quantity_as_amount": "Description contains large numeric token that is not an amount.",
        "thousands_sticky": "Printed with tight thousands separators and low contrast.",
        "handwritten_note": "Handwritten approval note appears near the total.",
        "non_invoice": "Synthetic purchase memo, not an invoice.",
        "tax_exempt": "VAT exempt line, total equals subtotal.",
    }
    return notes.get(trap, "")


def _extra_invoice(seed: int) -> dict:
    subtotal = Decimal("860.00") + Decimal(seed)
    vat = subtotal * Decimal("0.07")
    total = subtotal + vat
    return {
        "document_type": "tax_invoice",
        "is_not_invoice": False,
        "is_copy_or_duplicate": False,
        "invoice_number": f"IV26-X{seed:04d}",
        "date": "2026-06-21",
        "date_raw": "21/06/2026",
        "seller_name": "Second Page Vendor Co., Ltd.",
        "seller_tax": tax_id(seed + 3000),
        "seller_addr": "8 Ratchada Road, Bangkok",
        "buyer_name": "Pearnly Retail Co., Ltd.",
        "buyer_tax": tax_id(seed + 9000),
        "buyer_addr": "99/18 Sathorn Road, Bangkok",
        "subtotal": money(subtotal),
        "vat": money(vat),
        "wht_rate": "",
        "wht_amount": "",
        "discount": "",
        "total_amount": money(total),
        "cash_amount": "",
        "change_amount": "",
        "payment_method": "transfer",
        "currency": "",
        "items": [
            {
                "name": "ค่าบริการเพิ่มเติม",
                "qty": "1",
                "price": money(subtotal),
                "subtotal": money(subtotal),
            }
        ],
        "notes": "",
        "category": "service",
        "additional_invoices": [],
    }


def bank_cases() -> list[dict]:
    cases: list[dict] = []
    seq = 1
    for code, source in BANK_SOURCES.items():
        for variant in range(8):
            cases.append(_bank_case(seq, code, source, variant))
            seq += 1
    return cases


def _bank_case(seq: int, code: str, source: dict, variant: int) -> dict:
    opening = Decimal(25000 + seq * 317)
    balance = opening
    entries = []
    rows = 9 + (variant % 5)
    for row in range(rows):
        txn_date = date(2026, 6, 1) + timedelta(days=row * 2 + variant)
        is_deposit = (row + seq) % 3 == 0
        amount = Decimal(420 + ((seq * 41 + row * 97) % 4600))
        deposit = amount if is_deposit else Decimal("0.00")
        withdrawal = Decimal("0.00") if is_deposit else amount
        balance += deposit - withdrawal
        description = [
            "PromptPay REF 6091 ",
            "POS batch 10280137 ",
            "Monthly bank fee ",
            "Supplier INV-26-",
            "Interest credit",
        ][(row + variant) % 5]
        entries.append(
            {
                "transaction_date": txn_date.isoformat(),
                "transaction_date_raw": txn_date.strftime("%d/%m/%y"),
                "description": f"{description}{seq:03d}",
                "reference": f"{code.upper()}-{seq:03d}-{row:04d}",
                "deposit": money(deposit) if deposit else "",
                "withdrawal": money(withdrawal) if withdrawal else "",
                "amount": money(amount),
                "direction": "deposit" if is_deposit else "withdrawal",
                "balance": money(balance),
            }
        )
    gt = {
        "document_type": "bank_statement",
        "bank_name": source["name"],
        "bank_code": code,
        "account_name": "Pearnly Retail Co., Ltd.",
        "account_number": f"{100 + seq}-{variant:03d}-{seq:05d}-9",
        "account_last4": f"{seq:04d}"[-4:],
        "period_start": "2026-06-01",
        "period_end": "2026-06-30",
        "opening_balance": money(opening),
        "closing_balance": money(balance),
        "entries": entries,
    }
    return {
        "id": f"bank_{code}_{variant + 1:02d}",
        "image": f"bank/images/bank_{code}_{variant + 1:02d}.jpg",
        "ground_truth": f"bank/ground_truth/bank_{code}_{variant + 1:02d}.json",
        "bank_code": code,
        "layout_source": source,
        "photo_profile": PHOTO_PROFILES[(seq + variant) % len(PHOTO_PROFILES)],
        "render": {"variant": variant, "theme": source["color"]},
        "gt": gt,
    }


def gl_cases() -> list[dict]:
    return [_gl_case(index + 1) for index in range(12)]


def _gl_case(seq: int) -> dict:
    opening = Decimal(40000 + seq * 1250)
    balance = opening
    entries = []
    for row in range(12 + seq % 4):
        txn_date = date(2026, 6, 1) + timedelta(days=row)
        debit = Decimal(0)
        credit = Decimal(0)
        if (row + seq) % 2:
            debit = Decimal(800 + row * 137 + seq * 9)
            balance += debit
        else:
            credit = Decimal(600 + row * 121 + seq * 7)
            balance -= credit
        amount = debit or credit
        entries.append(
            {
                "transaction_date": txn_date.isoformat(),
                "transaction_date_raw": txn_date.strftime("%d/%m/%y"),
                "voucher_no": f"JV{seq:02d}{row:04d}.1",
                "account_code": "1112-07",
                "description": f"Bank movement batch 6091 row {row + 1}",
                "debit": money(debit) if debit else "",
                "credit": money(credit) if credit else "",
                "amount": money(amount),
                "direction": "deposit" if debit else "withdrawal",
                "balance": money(balance),
            }
        )
    return {
        "id": f"gl_v2_{seq:02d}",
        "image": f"gl/images/gl_v2_{seq:02d}.jpg",
        "ground_truth": f"gl/ground_truth/gl_v2_{seq:02d}.json",
        "photo_profile": PHOTO_PROFILES[seq % len(PHOTO_PROFILES)],
        "gt": {
            "document_type": "general_ledger",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "account_name": "Bank Account - Operating",
            "account_number": "1112-07",
            "opening_balance": money(opening),
            "closing_balance": money(balance),
            "entries": entries,
        },
    }


def vat_cases() -> list[dict]:
    return [_vat_case(index + 1) for index in range(12)]


def _vat_case(seq: int) -> dict:
    entries = []
    total_subtotal = Decimal(0)
    total_vat = Decimal(0)
    for row in range(10 + seq % 5):
        day = date(2026, 6, 1) + timedelta(days=row + seq)
        subtotal = Decimal(700 + seq * 23 + row * 157)
        vat = subtotal * Decimal("0.07")
        total = subtotal + vat
        total_subtotal += subtotal
        total_vat += vat
        entries.append(
            {
                "seq_no": str(row + 1),
                "transaction_date": day.isoformat(),
                "transaction_date_raw": day.strftime("%d/%m/%y"),
                "invoice_no": f"IV26-VAT-{seq:02d}-{row + 1:03d}",
                "customer_name": BUYERS[(row + seq) % len(BUYERS)][0],
                "customer_tax": tax_id(seq * 100 + row),
                "customer_branch": "สำนักงานใหญ่" if row % 2 else "00000",
                "subtotal": money(subtotal),
                "vat": money(vat),
                "total": money(total),
            }
        )
    return {
        "id": f"vat_v2_{seq:02d}",
        "image": f"vat/images/vat_v2_{seq:02d}.jpg",
        "ground_truth": f"vat/ground_truth/vat_v2_{seq:02d}.json",
        "photo_profile": PHOTO_PROFILES[(seq + 3) % len(PHOTO_PROFILES)],
        "gt": {
            "document_type": "vat_report",
            "seller_name": SELLERS[seq % len(SELLERS)][0],
            "seller_tax": tax_id(seq + 6000),
            "period_year": "2026",
            "period_month": "06",
            "total_subtotal": money(total_subtotal),
            "total_vat": money(total_vat),
            "total_total": money(total_subtotal + total_vat),
            "entries": entries,
        },
    }
