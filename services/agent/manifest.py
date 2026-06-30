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
        desc_th="สรุปว่ามีเอกสารกี่รายการ แยกตามสถานะ สำเร็จ/รอตรวจ/ไม่ผ่าน",
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
        desc_th="ดูจำนวนหน้าที่สแกน/ใช้งานไปแล้วในเดือนนี้",
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
}

_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "docs" / "agent" / "agent_registry.json"


def load_registry() -> dict[str, str]:
    """读 agent_registry.json(功能区 → 档)。供交叉核对测试与防漏闸用。"""
    data = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}
