# -*- coding: utf-8 -*-
"""MR.ERP xlsx · 9 种 sheet schema 定义 + 错误码友好提示 + sheet 收集/命名 helper.

mrerp_xlsx_generator 拆分 leaf。纯数据 + 纯 helper,0 逻辑改。stub-first 口子:物料到了
改 MRERP_SHEET_SCHEMAS / MRERP_ERROR_FRIENDLY,不动其他代码。

schema sheet 列字段(按出现顺序映射 sheet):
  - header_columns  → Worksheet     (必填 · 不能空)
  - detail_columns  → Worksheet 1   (可空 · 空则不创建该 sheet)
  - tail_columns    → Worksheet 2   (可空)
  - sheet4_columns  → Worksheet 3   (可空 · 付款代扣税专用)
"""

from typing import Any, Dict, List, Tuple

# ============================================================
# 9 种 sheet schema(stub-first · 物料到了改这里)
# ============================================================
# schema 格式:
# {
#     'header_columns':  [{'key': 'invoice_no', 'label': '...', 'type': 'str', 'max': 30}, ...],
#     'detail_columns':  [...] | None,   # 空 / None → 不创建 Worksheet 1
#     'tail_columns':    [...] | None,   # 空 / None → 不创建 Worksheet 2
#     'sheet4_columns':  [...] | None,   # 空 / None → 不创建 Worksheet 3(付款代扣税专用)
#     'stub': True | False,              # True = 物料未到 · 字段是猜测
# }

MRERP_SHEET_SCHEMAS: Dict[str, Dict[str, Any]] = {
    # ✅ 销售-赊销(物料 1 真实样本对齐 v27.8.1.4 · Korn 实际导出 SC 单)
    # Worksheet: 18 列 · Worksheet 1: 8 列 · Worksheet 2: 3 列
    "sales_credit": {
        "stub": False,
        "sheet_count_expected": 3,
        "label_zh": "销售-赊销",
        "label_th": "ขายเชื่อ",
        "label_en": "Sales (credit)",
        "label_ja": "売上(掛)",
        # Worksheet · 单据头(严格按 Korn 真样本列顺序)
        "header_columns": [
            {"key": "invoice_no", "label": "เลขที่", "type": "str", "max": 30},
            {"key": "invoice_date", "label": "วันที่", "type": "date"},
            {
                "key": "tax_rate_str",
                "label": "อัตราภาษี",
                "type": "str",
                "max": 14,
                "default": "7 (แยก)",
            },
            {"key": "branch_code", "label": "สาขา", "type": "str", "max": 14, "default": "00000"},
            {"key": "department", "label": "แผนก", "type": "str", "max": 14, "default": "BOI1"},
            {"key": "job", "label": "งาน", "type": "str", "max": 14, "default": "00002"},
            {
                "key": "salesman",
                "label": "พนักงานขาย",
                "type": "str",
                "max": 30,
                "default": "กร ทดสอบ",
            },
            {"key": "delivery_date", "label": "กำหนดส่งสินค้า", "type": "date"},
            {"key": "customer_code", "label": "รหัสลูกค้า", "type": "str", "max": 50},
            {"key": "customer_bill", "label": "รหัสลูกค้า (บิล)", "type": "str", "max": 50},
            {"key": "bill_no", "label": "เลขที่บิล", "type": "str", "max": 30},
            {"key": "bill_date", "label": "วันที่", "type": "date"},
            {
                "key": "sales_area",
                "label": "พื้นที่การขาย",
                "type": "str",
                "max": 30,
                "default": "สุพรรณบุรี",
            },
            {
                "key": "shipping_type",
                "label": "ประเภทขนส่ง",
                "type": "str",
                "max": 30,
                "default": "ขนส่งโดยบริษัท",
            },
            {"key": "discount", "label": "หักส่วนลด", "type": "num", "default": 0},
            {"key": "note1", "label": "หมายเหตุ 1", "type": "str", "max": 50},
            {"key": "note2", "label": "หมายเหตุ 2", "type": "str", "max": 50},
            {"key": "note3", "label": "หมายเหตุ 3", "type": "str", "max": 50},
        ],
        # Worksheet 1 · 商品明细(每行 1 件商品 · 关联 invoice_no)
        "detail_columns": [
            {"key": "invoice_no", "label": "เลขที่", "type": "str", "max": 30},
            {
                "key": "product_code",
                "label": "รหัสสินค้า",
                "type": "str",
                "max": 30,
                "default": "123",
            },
            {"key": "department", "label": "แผนก", "type": "str", "max": 14, "default": "BOI1"},
            {"key": "job", "label": "งาน", "type": "str", "max": 14, "default": "00002"},
            {"key": "warehouse", "label": "คลัง", "type": "str", "max": 14, "default": "0000"},
            {"key": "qty", "label": "จำนวน", "type": "num"},
            {"key": "unit_price", "label": "ราคา/หน่วย", "type": "num"},
            {"key": "amount", "label": "จำนวนเงิน", "type": "num"},
        ],
        # Worksheet 2 · 尾(押金 / 是否开销售单)
        "tail_columns": [
            {"key": "invoice_no", "label": "เลขที่", "type": "str", "max": 30},
            {"key": "deposit_no", "label": "เลขที่เงินมัดจำ", "type": "str", "max": 30},
            {"key": "is_sales_issued", "label": "ออกใบขาย", "type": "str", "max": 14},
        ],
    },
    # 🟡 销售-现金(stub · TODO 物料 1 · 7 列收款方式待定 · 预期 3 sheet)
    "sales_cash": {
        "stub": True,
        "sheet_count_expected": 3,
        "label_zh": "销售-现金 · 待物料",
        "label_th": "ขายสด · รอตัวอย่าง",
        "label_en": "Sales (cash) · WAIT MATERIAL",
        "label_ja": "売上(現金) · 物料待ち",
        # TODO 物料 1 · 现金销售真实样本到达后填:头 18 列 + 7 列收款方式 + 明细 8 + 尾 3
        "header_columns": [],
        "detail_columns": [],
        "tail_columns": [],
    },
    # 🟡 采购-赊购(stub · TODO 物料 2 · 头 16 + 明细 8 + 尾 3 · 预期 3 sheet)
    "purchase_credit": {
        "stub": True,
        "sheet_count_expected": 3,
        "label_zh": "采购-赊购 · 待物料",
        "label_th": "ซื้อเชื่อ · รอตัวอย่าง",
        "label_en": "Purchase (credit) · WAIT MATERIAL",
        "label_ja": "仕入(掛) · 物料待ち",
        # TODO 物料 2 · 采购赊购样本到达后填字段名
        "header_columns": [],
        "detail_columns": [],
        "tail_columns": [],
    },
    # 🟡 采购-现金(stub · TODO 物料 2 · 预期 3 sheet)
    "purchase_cash": {
        "stub": True,
        "sheet_count_expected": 3,
        "label_zh": "采购-现金 · 待物料",
        "label_th": "ซื้อสด · รอตัวอย่าง",
        "label_en": "Purchase (cash) · WAIT MATERIAL",
        "label_ja": "仕入(現金) · 物料待ち",
        # TODO 物料 2 · 采购现金样本到达后填字段名
        "header_columns": [],
        "detail_columns": [],
        "tail_columns": [],
    },
    # ✅ 客户档案(已有完整 25 列样本)· 1 sheet
    "customer": {
        "stub": False,
        "sheet_count_expected": 1,
        "label_zh": "客户档案",
        "label_th": "แฟ้มลูกค้า",
        "label_en": "Customer master",
        "label_ja": "取引先マスタ",
        "header_columns": [
            {"key": "customer_code", "label": "รหัสลูกค้า", "type": "str", "max": 50},
            {"key": "customer_name", "label": "ชื่อลูกค้า", "type": "str", "max": 50},
            {"key": "tax_id", "label": "เลขผู้เสียภาษี", "type": "str", "max": 20},
            {"key": "branch_code", "label": "สาขา", "type": "str", "max": 14, "default": "00000"},
            {"key": "address1", "label": "ที่อยู่ 1", "type": "str", "max": 50},
            {"key": "address2", "label": "ที่อยู่ 2", "type": "str", "max": 50},
            {"key": "address3", "label": "ที่อยู่ 3", "type": "str", "max": 50},
            {"key": "phone", "label": "โทรศัพท์", "type": "str", "max": 30},
            {"key": "fax", "label": "แฟกซ์", "type": "str", "max": 30},
            {"key": "email", "label": "อีเมล", "type": "str", "max": 50},
            {"key": "contact_person", "label": "ผู้ติดต่อ", "type": "str", "max": 50},
            {"key": "credit_limit", "label": "วงเงินเครดิต", "type": "num"},
            {"key": "credit_days", "label": "เครดิต(วัน)", "type": "num"},
            {"key": "salesman_code", "label": "พนักงานขาย", "type": "str", "max": 14},
            {"key": "group_code", "label": "กลุ่มลูกค้า", "type": "str", "max": 14},
            {"key": "zone_code", "label": "เขตการขาย", "type": "str", "max": 14},
            {"key": "price_level", "label": "ระดับราคา", "type": "str", "max": 14},
            {"key": "tax_rate_str", "label": "อัตราภาษี", "type": "str", "max": 14},
            {"key": "is_wht", "label": "หัก ณ ที่จ่าย", "type": "str", "max": 14},
            {"key": "wht_rate_str", "label": "อัตราหัก", "type": "str", "max": 14},
            {"key": "bank_name", "label": "ธนาคาร", "type": "str", "max": 30},
            {"key": "bank_account", "label": "เลขบัญชี", "type": "str", "max": 30},
            {"key": "note", "label": "หมายเหตุ", "type": "str", "max": 50},
            {"key": "is_active", "label": "สถานะ", "type": "str", "max": 14, "default": "A"},
            {"key": "created_date", "label": "วันที่สร้าง", "type": "date"},
        ],
        "detail_columns": None,
        "tail_columns": None,
    },
    # ✅ 商品档案(已知 29 列结构)· 1 sheet
    "product": {
        "stub": False,
        "sheet_count_expected": 1,
        "label_zh": "商品档案",
        "label_th": "แฟ้มสินค้า",
        "label_en": "Product master",
        "label_ja": "商品マスタ",
        "header_columns": [
            {"key": f"col_{i}", "label": f"Col{i}", "type": "str", "max": 50} for i in range(1, 30)
        ],
        "detail_columns": None,
        "tail_columns": None,
    },
    # ✅ 财务收款(已知 头20 + 核销3 + 支票5)· 3 sheet
    "receipt": {
        "stub": False,
        "sheet_count_expected": 3,
        "label_zh": "财务收款",
        "label_th": "รับชำระ",
        "label_en": "Receipt",
        "label_ja": "入金",
        "header_columns": [
            {"key": f"h_{i}", "label": f"H{i}", "type": "str", "max": 50} for i in range(1, 21)
        ],
        "detail_columns": [
            {"key": f"d_{i}", "label": f"D{i}", "type": "str", "max": 50} for i in range(1, 4)
        ],
        "tail_columns": [
            {"key": f"t_{i}", "label": f"T{i}", "type": "str", "max": 50} for i in range(1, 6)
        ],
    },
    # ✅ 财务付款(已知 多 Sheet4 = 15 列代扣税)· 4 sheet
    # 当前 stub-ish:Sheet1-3 列名待物料 · Sheet4 用 P1-P15 占位
    "payment": {
        "stub": False,
        "sheet_count_expected": 4,
        "label_zh": "财务付款",
        "label_th": "จ่ายชำระ",
        "label_en": "Payment",
        "label_ja": "出金",
        "header_columns": [
            {"key": f"h_{i}", "label": f"H{i}", "type": "str", "max": 50} for i in range(1, 21)
        ],
        "detail_columns": [
            {"key": f"d_{i}", "label": f"D{i}", "type": "str", "max": 50} for i in range(1, 4)
        ],
        "tail_columns": [
            {"key": f"t_{i}", "label": f"T{i}", "type": "str", "max": 50} for i in range(1, 6)
        ],
        "sheet4_columns": [
            {"key": f"wht_{i}", "label": f"WHT{i}", "type": "str", "max": 50} for i in range(1, 16)
        ],
    },
    # 🟡 会计凭证(stub · TODO 物料 3 · 头 6 + 分录 7 · 预期 2 sheet)
    "journal": {
        "stub": True,
        "sheet_count_expected": 2,
        "label_zh": "会计凭证 · 待物料",
        "label_th": "สมุดรายวัน · รอตัวอย่าง",
        "label_en": "Journal · WAIT MATERIAL",
        "label_ja": "仕訳 · 物料待ち",
        # TODO 物料 3 · 会计凭证样本到达后填字段名
        "header_columns": [],
        "detail_columns": [],
    },
}


# ============================================================
# 错误码 → 4 语友好提示(stub · TODO 物料 4)
# ============================================================
MRERP_ERROR_FRIENDLY: Dict[str, Dict[str, str]] = {}


def get_error_friendly(error_code: str, lang: str = "zh") -> str:
    """物料 4 未到时 fallback · 直接显示原始错误码"""
    entry = MRERP_ERROR_FRIENDLY.get(error_code or "", {})
    return entry.get(lang) or entry.get("en") or (error_code or "")


# ============================================================
# 内部工具 · 收集 schema 的所有 sheet 列(动态 1-4 sheet)
# ============================================================
def _collect_sheet_groups(schema: Dict[str, Any]) -> List[Tuple[str, List[Dict[str, Any]]]]:
    """
    根据 schema 收集要建的 sheet · 按固定顺序:
      header → Worksheet
      detail → Worksheet 1
      tail   → Worksheet 2
      sheet4 → Worksheet 3

    某段为空(None / 空 list)→ 不创建该 sheet。
    返回:[(group_name, columns), ...] · 至少 1 个(否则报错)
    """
    groups: List[Tuple[str, List[Dict[str, Any]]]] = []
    for key in ("header_columns", "detail_columns", "tail_columns", "sheet4_columns"):
        cols = schema.get(key)
        if cols:  # 非空 list / None / [] 都跳过
            group_name = key.replace("_columns", "")
            groups.append((group_name, cols))
    return groups


def _sheet_title(idx: int) -> str:
    """idx=0 → 'Worksheet' · idx>=1 → 'Worksheet N'(空格分隔 · 铁律 28)"""
    if idx == 0:
        return "Worksheet"
    return f"Worksheet {idx}"
