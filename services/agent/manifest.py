# -*- coding: utf-8 -*-
"""工具清单(M1-SOCKET-DESIGN §3)—— 插头目录。

闭集:大脑只能从 TOOLS 里选。M1 只登记 A 档只读工具(查询/统计),B 档留到 M3。
加一个能力 = 加一个 ToolSpec(+ executor 方法 + REGISTRY_AREA + registry 登记),提示词自动跟着变。

REGISTRY_AREA:每个工具绑定它在 agent_registry.json 的功能区(routes 文件名)。manifest 登记的
工具其功能区必为相同档 —— A 档工具不能挂在 B/C/D 区。test_agent_manifest 机械核对这一致性。
"""

from __future__ import annotations

import json
from pathlib import Path

from services.agent.contracts import SlotSpec, ToolSpec

TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="list_history",
        bucket="A",
        title_th="ดูประวัติการสแกนเอกสาร",
        desc_th="ดูรายการเอกสาร/ใบเสร็จที่เคยสแกน ค้นด้วยชื่อร้านหรือเลขใบเสร็จ และกรองตามสถานะได้",
        slots=(
            SlotSpec(
                "keyword",
                required=False,
                source="model_freeform",
                desc_th="คำค้น เช่น ชื่อร้านหรือเลขใบเสร็จ",
                desc_zh="关键词(卖家/单号/文件名)",
            ),
            SlotSpec(
                "status",
                required=False,
                source="user_text",
                desc_th="สถานะ: confirmed/pending/failed",
                desc_zh="状态过滤(用户原话提到才采纳)",
            ),
        ),
        handler="list_ocr_history",
        confirm=False,
    ),
    ToolSpec(
        name="history_summary",
        bucket="A",
        title_th="สรุปจำนวนเอกสารที่สแกน",
        desc_th="สรุปเดือนนี้ว่าสแกนไปกี่ใบ/กี่รายการ ยอดรวมกี่บาท และแยกตามหมวดหมู่ (ใช้เมื่อถามจำนวนใบเอกสาร)",
        slots=(),
        handler="summarize_ocr_history",
        confirm=False,
    ),
    ToolSpec(
        name="balance",
        bucket="A",
        title_th="ดูยอดเครดิตคงเหลือ",
        desc_th="ดูยอดเงิน/เครดิตคงเหลือของบัญชี",
        slots=(),
        handler="get_balance",
        confirm=False,
    ),
    ToolSpec(
        name="usage_this_month",
        bucket="A",
        title_th="ดูปริมาณการใช้งานเดือนนี้",
        desc_th="ดูจำนวนหน้าที่ใช้โควตา/คิดค่าบริการไปเดือนนี้ (นับเป็นหน้า ไม่ใช่จำนวนใบเอกสาร)",
        slots=(),
        handler="get_usage_this_month",
        confirm=False,
    ),
    ToolSpec(
        name="list_notifications",
        bucket="A",
        title_th="ดูประวัติการแจ้งเตือน",
        desc_th="ดูรายการแจ้งเตือนที่ระบบส่งล่าสุด",
        slots=(),
        handler="list_notification_logs",
        confirm=False,
    ),
    ToolSpec(
        name="push_status",
        bucket="A",
        title_th="เช็คสถานะการส่งเข้า ERP",
        desc_th=(
            "เช็คว่าเอกสาร/บิลถูกส่งเข้า ERP แล้วหรือยัง และผลการส่งล่าสุด "
            "(เช่น 'บิล 7-11 ส่งเข้า ERP หรือยัง') ไม่ระบุใบไหน = ใบล่าสุด"
        ),
        slots=(
            SlotSpec(
                "keyword",
                required=False,
                source="model_freeform",
                desc_th="คำค้นระบุใบ เช่น ชื่อร้านหรือเลขใบเสร็จ",
                desc_zh="定位单据的关键词(店名/单号)",
            ),
        ),
        handler="get_push_status",
        confirm=False,
    ),
    ToolSpec(
        name="rd_lookup",
        bucket="A",
        title_th="ตรวจเลขผู้เสียภาษีกับกรมสรรพากร",
        desc_th=(
            "ตรวจสอบเลขประจำตัวผู้เสียภาษี 13 หลักกับกรมสรรพากร "
            "ได้ชื่อบริษัท สาขา ที่อยู่ (เลขต้องอยู่ในข้อความของผู้ใช้)"
        ),
        slots=(
            SlotSpec(
                "tax_id",
                required=True,
                source="user_text",
                desc_th="เลขผู้เสียภาษี 13 หลัก (คัดจากข้อความผู้ใช้เท่านั้น)",
                desc_zh="13 位税号(必须出现在用户原话·防编造)",
            ),
        ),
        handler="rd_lookup",
        confirm=False,
    ),
    ToolSpec(
        name="my_plan",
        bucket="A",
        title_th="ดูแพ็กเกจ/สิทธิ์การใช้งานของฉัน",
        desc_th="ดูว่าตอนนี้ใช้แพ็กเกจอะไร เครดิตคงเหลือ เก็บประวัติได้กี่วัน และวันหมดอายุแพ็กเกจ",
        slots=(),
        handler="get_my_plan",
        confirm=False,
    ),
    ToolSpec(
        name="record_expense",
        bucket="B",
        title_th="บันทึกค่าใช้จ่าย",
        desc_th=(
            "บันทึกค่าใช้จ่ายใหม่เมื่อผู้ใช้บอกจำนวนเงิน + ชื่อของ/ร้าน "
            "(เช่น 'กาแฟ 50', 'จ่ายค่าน้ำ 300') — มั่นใจก็บันทึกเลย ระบบออกการ์ดให้ (แก้/ยกเลิกได้ภายหลัง)"
        ),
        slots=(
            # amount 走 to_draft 的 amount_grounded 做钱路唯一闸(model_freeform 只放行到执行器再验,
            # 编造的钱在 to_draft 被置空 → 落缺金额追问,绝不凭空入账)。
            SlotSpec(
                "amount",
                required=False,
                source="model_freeform",
                desc_th="จำนวนเงินรวม (ตัวเลข)",
                desc_zh="总额(数字·执行器再过金额接地)",
            ),
            SlotSpec(
                "vendor_name",
                required=False,
                source="user_text",
                desc_th="ชื่อร้าน/ผู้ขาย ถ้ามี",
                desc_zh="卖家/店名(用户原话提到才采纳)",
            ),
            SlotSpec(
                "note",
                required=False,
                source="model_freeform",
                desc_th="ชื่อสินค้า/รายการที่ซื้อ",
                desc_zh="物品名(不含金额/店名)",
            ),
            SlotSpec(
                "date",
                required=False,
                source="user_text",
                desc_th="วันที่ YYYY-MM-DD ถ้าระบุ",
                desc_zh="日期(用户提到才采纳)",
            ),
        ),
        handler="record_expense",
        confirm=False,  # 高置信直录(可撤销·非不可逆)→ 不先确认;缺金额由大脑文字追问
        writes=True,
        gate="write",
    ),
    ToolSpec(
        name="undo_entry",
        bucket="B",
        title_th="ยกเลิก/ลบรายการที่บันทึกแล้ว",
        desc_th=(
            "ยกเลิกหรือลบรายการที่บันทึกไปแล้ว (เช่น 'ยกเลิกรายการล่าสุด' หรือ reply การ์ดแล้วบอกยกเลิก) "
            "ระบบหาเป้าหมายเองจากข้อความ/การ์ดที่อ้างถึง"
        ),
        slots=(),
        handler="undo_entry",
        confirm=False,  # 冲销可经「恢复」找回,非不可逆;定位不明由确定性执行侧反问
        writes=True,
        gate="m3",
    ),
    ToolSpec(
        name="edit_entry",
        bucket="B",
        title_th="แก้ไขรายการที่บันทึกแล้ว",
        desc_th=(
            "แก้ไขรายการที่บันทึกไปแล้ว เช่น 'แก้รายการล่าสุดเป็น 80' 'เปลี่ยนร้านเป็น Tops' "
            "ใส่เฉพาะช่องที่ผู้ใช้ต้องการแก้"
        ),
        slots=(
            # 新金额必须在用户原话(钱路接地);改错的确认/风险三档由 line_correct 确定性执行。
            SlotSpec(
                "amount",
                required=False,
                source="user_text",
                desc_th="ยอดใหม่ (ต้องอยู่ในข้อความผู้ใช้)",
                desc_zh="新金额(必须出现在原话·防编造)",
            ),
            SlotSpec(
                "vendor_name",
                required=False,
                source="user_text",
                desc_th="ชื่อร้านใหม่ ถ้าจะแก้ร้าน",
                desc_zh="新卖家名(用户原话提到才采纳)",
            ),
            SlotSpec(
                "date",
                required=False,
                source="model_freeform",
                desc_th="วันที่ใหม่ YYYY-MM-DD (แปลงจากคำพูดเช่น เมื่อวาน ได้)",
                desc_zh="新日期(允许相对词换算·与旧路同口径·格式闸在 line_correct)",
            ),
            SlotSpec(
                "note",
                required=False,
                source="model_freeform",
                desc_th="หมวดหมู่/รายละเอียดใหม่ ถ้าจะแก้หมวด",
                desc_zh="新科目线索(仅当只改科目时)",
            ),
        ),
        handler="edit_entry",
        confirm=False,  # 风险确认(是/否)由 line_correct 的确定性三档自行把关
        writes=True,
        gate="m3",
    ),
    ToolSpec(
        name="push_to_erp",
        bucket="B",
        title_th="ส่งเอกสารเข้า ERP",
        desc_th=(
            "ส่งเอกสาร/บิลที่สแกนแล้วเข้า ERP (เช่น 'ส่งใบ 7-11 เข้า ERP') — เครื่องมือนี้แค่เตรียม"
            "การ์ดยืนยัน ระบบจะส่งจริงก็ต่อเมื่อผู้ใช้กดยืนยันบนการ์ดเท่านั้น"
        ),
        slots=(
            SlotSpec(
                "doc_keyword",
                required=False,
                source="model_freeform",
                desc_th="คำค้นระบุใบ เช่น ชื่อร้านหรือเลขใบเสร็จ (ไม่ระบุ = ใบล่าสุด)",
                desc_zh="定位单据的关键词(店名/单号·缺省=最近一张)",
            ),
            SlotSpec(
                "endpoint_name",
                required=False,
                source="user_text",
                desc_th="ชื่อปลายทาง ERP ถ้าผู้ใช้ระบุ",
                desc_zh="端点名(用户原话点名才采纳·缺省=默认端点)",
            ),
        ),
        handler="push_to_erp",
        confirm=True,  # 不可逆:工具只备料,真推送在用户点确认按钮之后(push_confirm)
        writes=True,
        gate="push",
    ),
    ToolSpec(
        name="plan_incoming_doc",
        bucket="B",
        title_th="กำหนดว่าจะทำอะไรกับเอกสารที่กำลังจะส่งมา",
        desc_th=(
            "ผู้ใช้บอกล่วงหน้าว่าเอกสาร/รูปใบต่อไปจะให้ทำอะไร — เก็บเป็นแผนไว้ พอรูปมาถึงระบบทำตามทันที "
            "ตัวอย่าง: 'ใบต่อไปส่งเข้า ERP ไม่ต้องบันทึก' → goals:[\"push\"] · "
            "'รูปหน้าบันทึกเข้าชุด X' → goals:[\"record\"] · "
            "'รูปหน้าไม่ต้องทำอะไร/แค่ดูให้' → goals:[\"nothing\"] · "
            '\'บันทึกด้วยส่ง ERP ด้วย\' → goals:["record","push"]'
        ),
        slots=(
            # goals 是封闭枚举(record/push/archive_only/nothing 组合),端点/套账名必须
            # 出自用户原话并在执行器对真实资产核验——查无此名如实退回,绝不猜目标。
            SlotSpec(
                "goals",
                required=True,
                source="model_freeform",
                desc_th="สิ่งที่จะทำ (เลือกจาก: record / push / archive_only / nothing · เลือกได้หลายอัน)",
                desc_zh="目的组合(枚举 record/push/archive_only/nothing·执行器再验)",
            ),
            SlotSpec(
                "endpoint_name",
                required=False,
                source="user_text",
                desc_th="ชื่อปลายทาง ERP ถ้าผู้ใช้ระบุ",
                desc_zh="端点名(用户原话点名才采纳)",
            ),
            SlotSpec(
                "workspace_name",
                required=False,
                source="user_text",
                desc_th="ชื่อชุดบัญชีที่จะบันทึกเข้า ถ้าผู้ใช้ระบุ",
                desc_zh="套账名(用户原话点名才采纳)",
            ),
        ),
        handler="plan_incoming_doc",
        confirm=False,  # 存的是"下一张图怎么处理"的计划,不可逆动作(推送)届时仍走确认卡
        writes=True,
        gate="image",
    ),
    ToolSpec(
        name="list_workspaces",
        bucket="B",
        title_th="ดูรายชื่อชุดบัญชี/บริษัท",
        desc_th="ดูว่ามีชุดบัญชี (บริษัท/ผู้ติดต่อ) อะไรบ้าง และตอนนี้กำลังใช้ชุดไหนอยู่",
        slots=(),
        handler="list_workspaces",
        confirm=False,
    ),
    ToolSpec(
        name="switch_workspace",
        bucket="B",
        title_th="สลับชุดบัญชี/บริษัท",
        desc_th="สลับไปทำงานกับชุดบัญชี/บริษัทอื่นตามชื่อ (เช่น 'สลับไปสยามวัสดุ') รายการที่บันทึกหลังจากนั้นจะเข้าชุดนี้",
        slots=(
            SlotSpec(
                "name",
                required=True,
                source="user_text",
                desc_th="ชื่อชุดบัญชี/บริษัทที่จะสลับไป",
                desc_zh="要切到的套账/公司名(取用户原话)",
            ),
        ),
        handler="switch_workspace",
        confirm=False,
    ),
)

# 大脑只能从这里选(O(1) 查表)。
TOOLS_BY_NAME = {t.name: t for t in TOOLS}

# 工具 → agent_registry.json 的功能区(routes 文件名 · 不含 .py)。
REGISTRY_AREA: dict[str, str] = {
    "list_history": "report_routes",
    "history_summary": "report_routes",
    "balance": "billing_credits_routes",
    "usage_this_month": "billing_records_routes",
    "list_notifications": "notification_routes",
    "push_status": "erp_listing_routes",
    "rd_lookup": "rd_routes",
    "my_plan": "me_routes",
    "record_expense": "purchase_intake_routes",
    "undo_entry": "purchase_routes",
    "edit_entry": "purchase_routes",
    "push_to_erp": "erp_push_log_routes",
    "plan_incoming_doc": "purchase_intake_routes",
    "list_workspaces": "workspace_routes",
    "switch_workspace": "workspace_routes",
}

_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "docs" / "agent" / "agent_registry.json"


def load_registry() -> dict[str, str]:
    """读 agent_registry.json(功能区 → 档)。A 档登记值为 {bucket, agent} 结构 → 归一成桶。"""
    data = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    return {
        k: (v.get("bucket") if isinstance(v, dict) else v)
        for k, v in data.items()
        if not k.startswith("_")
    }
