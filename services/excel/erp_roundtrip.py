# -*- coding: utf-8 -*-
"""ERP 复核工作簿的「回导规格」· 写侧和读侧共用的唯一一份定义。

会计的实际动作是一个闭环:导出 → 在 Excel 里挑错 → 把对的行删掉 → 改错的行 →
去 ERP 删掉错单 → 把改后的表格导回 Pearnly 重推。这份规格保证那个环能闭上。

两条硬约束:

1. **方向不靠猜,靠行所在的 Sheet。** 销项/进项各一张表,判不出方向的落「待判」表。
   会计发现分错了就把那行剪到另一张表 —— 回导时 Sheet 名当显式方向,压过税号自动判定
   (见 services/erp/express_push/direction.explicit_direction)。会计不必学新概念、
   不必填方向字段,挪一行就是改一次分类。

2. **各表守各自的列位合同。** 销项前 12 列是与 MR.ERP 约定的公式合同(不动列位),
   进项沿用 ภ.พ.30 进项税明细的法定列。回导列一律追加在各自合同列之后,不插队。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

# ── Sheet 名 = 方向的唯一事实源 ────────────────────────────────────────────
SHEET_SALES = "ขาย"
SHEET_PURCHASE = "ซื้อ"
SHEET_PENDING = "รอจำแนก"  # 方向判不出 / 被闸拦下 · 会计裁决后挪走
SHEET_SUMMARY = "สรุป"  # 本批新建主档清单 · 只读不回导

DIRECTION_BY_SHEET: Dict[str, Optional[str]] = {
    SHEET_SALES: "sales",
    SHEET_PURCHASE: "purchase",
    SHEET_PENDING: None,
}
DATA_SHEETS: Tuple[str, ...] = (SHEET_SALES, SHEET_PURCHASE, SHEET_PENDING)

# ── 回导列(两张数据表共用 · 追加在各自合同列之后)────────────────────────
COL_ERP_DOCNUM = "เลขที่เอกสาร ERP"
COL_ERP_ITEM = "รหัสสินค้า ERP"
COL_ERP_PARTY = "รหัสคู่ค้า ERP"
COL_PUSH_STATUS = "สถานะการส่ง"
COL_ROW_KEY = "รหัสอ้างอิงระบบ"

ROUNDTRIP_HEADERS: Tuple[str, ...] = (
    COL_ERP_DOCNUM,
    COL_ERP_ITEM,
    COL_ERP_PARTY,
    COL_PUSH_STATUS,
    COL_ROW_KEY,
)
ROUNDTRIP_WIDTHS: Tuple[int, ...] = (18, 16, 14, 16, 26)

# ── 各表的业务列名(写侧和读侧共认这一份 · 读侧按列名取值不按列位,会计插列也不散架)──
# 销项:前 12 列是 MR.ERP 公式合同,列名见 excel_template_th.HEADERS_TH。
SALES_COL_DATE = "วันที่"
SALES_COL_INVOICE = "เลขที่"
SALES_COL_PARTY = "รหัสลูกค้า"
SALES_COL_ITEM = "รหัสสินค้า"
SALES_COL_QTY = "จำนวน"
SALES_COL_PRICE = "ราคาต่อหน่วย"
SALES_COL_AMOUNT = "จำนวนเงิน"
SALES_COL_PRE_VAT = "รวมจำนวนเงินก่อนVAT"
SALES_COL_VAT = "VAT"

# 进项:沿用 ภ.พ.30 进项税明细的法定列(每行一张票 · 不拆商品行 —— 费用票整张进一个科目,
# 与销项按行动库存的粒度天然不同,不该硬捏成一样)。
PURCHASE_HEADERS: Tuple[str, ...] = (
    "ลำดับ",  # 序号
    "วันที่",  # 票面日期
    "เลขที่",  # 票号
    "ชื่อผู้ขาย",  # 卖方(供应商)
    "เลขประจำตัวผู้เสียภาษี",  # 卖方税号
    "สาขา",  # 分店
    "มูลค่าก่อนภาษี",  # 税前金额
    "ภาษีซื้อ",  # 进项税
    "รวมทั้งสิ้น",  # 合计
    "หมวดค่าใช้จ่าย",  # 费用类别
)
PURCHASE_WIDTHS: Tuple[int, ...] = (6, 12, 18, 32, 20, 10, 16, 14, 16, 16)

PURCHASE_COL_DATE = PURCHASE_HEADERS[1]
PURCHASE_COL_INVOICE = PURCHASE_HEADERS[2]
PURCHASE_COL_PARTY = PURCHASE_HEADERS[3]
PURCHASE_COL_PARTY_TAX = PURCHASE_HEADERS[4]
PURCHASE_COL_PRE_VAT = PURCHASE_HEADERS[6]
PURCHASE_COL_VAT = PURCHASE_HEADERS[7]
PURCHASE_COL_TOTAL = PURCHASE_HEADERS[8]
PURCHASE_COL_CATEGORY = PURCHASE_HEADERS[9]

# 待判表:方向没定,给的是「为什么没定」+ 最低限度的识别信息,会计裁决后剪到上面两张表。
PENDING_COL_REASON = "เหตุผล"
PENDING_HEADERS: Tuple[str, ...] = (
    "วันที่",
    "เลขที่",
    "คู่ค้า",  # 对手方(方向未定时不预设是客户还是供应商)
    "เลขประจำตัวผู้เสียภาษี",
    "รวมทั้งสิ้น",
    PENDING_COL_REASON,
)
PENDING_WIDTHS: Tuple[int, ...] = (12, 18, 32, 20, 16, 36)

PENDING_COL_DATE = PENDING_HEADERS[0]
PENDING_COL_INVOICE = PENDING_HEADERS[1]
PENDING_COL_PARTY = PENDING_HEADERS[2]
PENDING_COL_TOTAL = PENDING_HEADERS[4]

# ── 推送状态标签(泰文 · 与表格其余部分同语言)────────────────────────────
_STATUS_LABEL = {
    "success": "สำเร็จ",
    "pending": "รอส่ง",
    "queued": "รอส่ง",
    "failed": "ล้มเหลว",
    "error": "ล้มเหลว",
    "manual": "ตรวจสอบเอง",
    "skipped_dup": "ซ้ำ · ข้าม",
}
STATUS_UNKNOWN = "-"


def status_label(status: Any, reason: Any = None) -> str:
    """推送状态 → 表格里给会计看的文本。带原因时附在后面,便于直接判断该不该去 ERP 删单。"""
    s = str(status or "").strip().lower()
    label = _STATUS_LABEL.get(s)
    if not label:
        return STATUS_UNKNOWN
    r = str(reason or "").strip()
    return f"{label} · {r[:60]}" if r else label


# ── 回导键 ────────────────────────────────────────────────────────────────
# 票号是会计最常改的字段(纠正错号就是这个流程的主要目的之一),按票号配对必断,
# 故另立一列不随内容变的键。格式 PRN:<history_id>:<行序>。
_KEY_PREFIX = "PRN"


def encode_row_key(history_id: Any, line_index: int = 0) -> str:
    hid = str(history_id or "").strip()
    if not hid:
        return ""
    return f"{_KEY_PREFIX}:{hid}:{int(line_index)}"


def decode_row_key(raw: Any) -> Optional[Tuple[str, int]]:
    """解回 (history_id, 行序);不是我们的键(会计手打的备注等)→ None,不硬猜。"""
    s = str(raw or "").strip()
    if not s.startswith(_KEY_PREFIX + ":"):
        return None
    parts = s.split(":")
    if len(parts) != 3 or not parts[1].strip():
        return None
    try:
        return parts[1].strip(), int(parts[2])
    except ValueError:
        return None


# ── 表头指纹:认出这是我们自己导出的工作簿 ────────────────────────────────
def is_roundtrip_sheet(headers: Sequence[Any]) -> bool:
    """表头是否带全回导列。命中 → 走确定性解析(纯读单元格·不过大模型);
    不命中 → 交回原有的通用表格路,不抢别人的活。"""
    got = {str(h).strip() for h in (headers or []) if str(h or "").strip()}
    return all(h in got for h in ROUNDTRIP_HEADERS)


def sheet_direction(sheet_name: Any) -> Optional[str]:
    """Sheet 名 → 方向。未知表名返回 None(与「待判」同待遇:不自动推)。"""
    return DIRECTION_BY_SHEET.get(str(sheet_name or "").strip())


def is_data_sheet(sheet_name: Any) -> bool:
    return str(sheet_name or "").strip() in DATA_SHEETS


def roundtrip_values(
    *,
    docnum: Any = "",
    item_code: Any = "",
    party_code: Any = "",
    push_status: Any = None,
    push_reason: Any = None,
    row_key: Any = "",
) -> List[Any]:
    """按 ROUNDTRIP_HEADERS 顺序生成这 5 格的值(写侧唯一入口·保证顺序不漂)。"""
    return [
        str(docnum or "").strip(),
        str(item_code or "").strip(),
        str(party_code or "").strip(),
        status_label(push_status, push_reason),
        str(row_key or "").strip(),
    ]
