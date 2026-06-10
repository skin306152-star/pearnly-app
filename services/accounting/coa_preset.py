# -*- coding: utf-8 -*-
"""泰标科目表预置 + 默认角色映射(TFRS for NPAEs 口径 · docs/accounting/01)。

每套账首次用做账时按此 seed(幂等:已有预置行早退)。预置科目 is_preset=TRUE 不可删可停;
规则引擎只认角色(account_mappings.role),用户改映射不动规则代码。
"""

from __future__ import annotations

# (code, name_zh, name_th, acct_type)
PRESET_ACCOUNTS = (
    ("1010", "现金", "เงินสด", "asset"),
    ("1020", "银行存款", "เงินฝากธนาคาร", "asset"),
    ("1130", "应收账款", "ลูกหนี้การค้า", "asset"),
    ("1140", "进项税", "ภาษีซื้อ", "asset"),
    ("1145", "被预扣税(我方预付)", "ภาษีถูกหัก ณ ที่จ่าย", "asset"),
    ("1150", "存货", "สินค้าคงเหลือ", "asset"),
    ("1160", "VAT 留抵", "ภาษีมูลค่าเพิ่มขอคืน", "asset"),
    ("1510", "设备", "อุปกรณ์", "asset"),
    ("2010", "应付账款", "เจ้าหนี้การค้า", "liability"),
    ("2030", "销项税", "ภาษีขาย", "liability"),
    ("2040", "应交 VAT", "ภาษีมูลค่าเพิ่มค้างจ่าย", "liability"),
    ("2050", "预扣税应缴", "ภาษีหัก ณ ที่จ่ายค้างจ่าย", "liability"),
    ("3010", "实收资本", "ทุน", "equity"),
    ("3020", "留存收益", "กำไรสะสม", "equity"),
    ("4010", "销售收入", "รายได้จากการขาย", "revenue"),
    ("4020", "服务收入", "รายได้ค่าบริการ", "revenue"),
    ("4900", "其他收入", "รายได้อื่น", "revenue"),
    ("5010", "销售成本", "ต้นทุนขาย", "expense"),
    ("5210", "租金", "ค่าเช่า", "expense"),
    ("5220", "水电费", "ค่าสาธารณูปโภค", "expense"),
    ("5230", "工资", "เงินเดือน", "expense"),
    ("5240", "运费", "ค่าขนส่ง", "expense"),
    ("5250", "广告费", "ค่าโฆษณา", "expense"),
    ("5260", "专业服务费", "ค่าธรรมเนียมวิชาชีพ", "expense"),
    ("5270", "维修费", "ค่าซ่อมแซม", "expense"),
    ("5290", "杂项费用", "ค่าใช้จ่ายเบ็ดเตล็ด", "expense"),
)

# 角色 → 预置科目编号(规则引擎经 account_mappings 解析,seed 时按此建默认映射)
ROLE_DEFAULTS = {
    "cash": "1010",
    "bank": "1020",
    "ar": "1130",
    "input_vat": "1140",
    "wht_prepaid": "1145",
    "inventory": "1150",
    "vat_receivable": "1160",
    "ap": "2010",
    "output_vat": "2030",
    "vat_payable": "2040",
    "wht_payable": "2050",
    "sales_revenue": "4010",
    "service_revenue": "4020",
    "cogs": "5010",
    "expense_default": "5290",
}

ACCT_TYPES = ("asset", "liability", "equity", "revenue", "expense")


def ensure_seeded(cur, *, tenant_id: str, workspace_client_id: int) -> None:
    """本套账首次接触做账 → seed 预置科目 + 默认映射;已 seed 早退(幂等)。"""
    cur.execute(
        "SELECT 1 FROM chart_of_accounts "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND is_preset LIMIT 1",
        (tenant_id, workspace_client_id),
    )
    if cur.fetchone():
        return

    code_to_id = {}
    for sort, (code, name_zh, name_th, acct_type) in enumerate(PRESET_ACCOUNTS):
        cur.execute(
            "INSERT INTO chart_of_accounts "
            "(tenant_id, workspace_client_id, code, name_zh, name_th, acct_type, "
            " is_preset, sort) "
            "VALUES (%s, %s, %s, %s, %s, %s, TRUE, %s) "
            "ON CONFLICT (tenant_id, workspace_client_id, code) DO UPDATE SET "
            "is_preset = TRUE RETURNING id",
            (tenant_id, workspace_client_id, code, name_zh, name_th, acct_type, sort),
        )
        code_to_id[code] = cur.fetchone()["id"]

    for role, code in ROLE_DEFAULTS.items():
        cur.execute(
            "INSERT INTO account_mappings (tenant_id, workspace_client_id, role, account_id) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (tenant_id, workspace_client_id, role) DO NOTHING",
            (tenant_id, workspace_client_id, role, code_to_id[code]),
        )
