# -*- coding: utf-8 -*-
"""M1-B2 · 客户建档收严:泰文注册名必填校验(闸 pearnly_ai_m1)。

背景(L2-验收.md 2026-07-09 真语料坐实):税号被 OCR 读花时,workspace_clients.name
(泰文注册名)是分拣方向判定(sort._direction_by_name)唯一的名称锚兜底。本次真跑因
bootstrap 档案只填了英文代号,名称锚空转了一整跑,29,263.28 ฿进项税靠人工裁决才补回。

字段选型:workspace_clients 只有单一 name 列,没有独立 official_name/thai_name 列
(见 alembic/versions/005_workspace_clients.py + services/workspace/store.py
ensure_workspace_tables)——不新增列(硬约束:schema 不动),故"泰文注册名"判定落在
同一 name 字段上:校验其含至少一个泰文 Unicode 字符(U+0E00–U+0E7F 泰文区段)。

闸 pearnly_ai_m1 关时,本模块函数不会被路由调用——建档/编辑现状逐字节不变。
"""

from __future__ import annotations

import re
from typing import Optional

_THAI_RANGE = re.compile(r"[฀-๿]")

ERR_THAI_NAME_REQUIRED = "workspace.thai_name_required"
ERR_THAI_NAME_LOCKED = "workspace.thai_name_locked"

_MESSAGES: dict[str, dict[str, str]] = {
    ERR_THAI_NAME_REQUIRED: {
        "zh": "请填写泰文注册名(税号读错时用它兜底认账套)",
        "en": "Please enter the Thai registered name (used as a fallback when the tax ID is misread)",
        "th": "กรุณากรอกชื่อจดทะเบียนภาษาไทย (ใช้เป็นตัวสำรองเมื่ออ่านเลขผู้เสียภาษีผิด)",
        "ja": "タイ語の登録名を入力してください(税番号の読み取りミス時の代替として使用します)",
    },
    ERR_THAI_NAME_LOCKED: {
        "zh": "已登记的泰文注册名不能清空,可以改成另一个泰文名",
        "en": "The registered Thai name cannot be cleared; you may change it to a different Thai name",
        "th": "ลบชื่อจดทะเบียนภาษาไทยที่บันทึกไว้ไม่ได้ สามารถเปลี่ยนเป็นชื่อภาษาไทยอื่นได้",
        "ja": "登録済みのタイ語名を空にすることはできません。別のタイ語名に変更してください",
    },
}


def has_thai_registered_name(name: Optional[str]) -> bool:
    """name 是否含泰文注册名(至少一个泰文 Unicode 字符)。"""
    return bool(name) and bool(_THAI_RANGE.search(name))


def error_payload(code: str) -> dict:
    """建 HTTPException(422).detail 用的结构化错误:{code, message: 四语字典}。

    code 供前端逻辑分支用(is-error-X 判断);message 已就地可读,W1 补填引导页
    不需要再接 i18n-data.js 就能直接渲染。
    """
    return {"code": code, "message": _MESSAGES[code]}
