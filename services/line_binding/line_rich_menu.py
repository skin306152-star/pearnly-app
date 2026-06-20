# -*- coding: utf-8 -*-
"""LINE Rich Menu(底部固定菜单)· 6 区接线全复用现有功能(不新写业务)。

布局 3 列 × 2 行(2500×1686 插画底图):
  ① ถ่ายบิล(相机)  ② สรุปเดือนนี้(rm_summary)  ③ รวมหลักฐาน PDF(rm_proof)
  ④ รายการล่าสุด(rm_detail) ⑤ วิธีใช้(rm_help)     ⑥ เว็บไซต์(uri)
cameraAction/uriAction 由 LINE 客户端直接处理;rm_* postback 回后端路由到现有汇总/明细/PDF/能力说明。
setup_default_menu() 上线时手动跑一次(prod channel token):幂等删旧同名 → 建 → 传图 → 设默认。
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from typing import Optional

from services.line_binding import line_client

logger = logging.getLogger(__name__)

MENU_NAME = "pearnly-main-v1"
_IMAGE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "static",
    "brand",
    "line-richmenu-pearnly-illustrated-bg-v6-2500x1686.jpg",
)
_W, _H = 2500, 1686
# 三列精确覆盖 2500(中列 +1 补齐·无缝无重叠),两行各 843 覆盖 1686。
_COLS = ((0, 833), (833, 834), (1667, 833))
_ROWS = ((0, 843), (843, 843))
_RM_ACTIONS = {"rm_summary", "rm_proof", "rm_detail", "rm_help"}


def _area(col: int, row: int, action: dict) -> dict:
    x, w = _COLS[col]
    y, h = _ROWS[row]
    return {"bounds": {"x": x, "y": y, "width": w, "height": h}, "action": action}


def build_payload() -> dict:
    """6 区 Rich Menu 配置(纯·喂 createRichMenu)。postback displayText 让点按回显友好文字。"""
    return {
        "size": {"width": _W, "height": _H},
        "selected": True,
        "name": MENU_NAME,
        "chatBarText": "เมนู Pearnly",
        "areas": [
            _area(0, 0, {"type": "camera", "label": "ถ่ายบิล"}),
            _area(
                1, 0, {"type": "postback", "data": "a=rm_summary", "displayText": "สรุปเดือนนี้"}
            ),
            _area(
                2, 0, {"type": "postback", "data": "a=rm_proof", "displayText": "รวมหลักฐาน PDF"}
            ),
            _area(0, 1, {"type": "postback", "data": "a=rm_detail", "displayText": "รายการล่าสุด"}),
            _area(1, 1, {"type": "postback", "data": "a=rm_help", "displayText": "วิธีใช้"}),
            _area(2, 1, {"type": "uri", "label": "เว็บไซต์", "uri": "https://pearnly.com"}),
        ],
    }


def _list_menus() -> list:
    token = line_client._get_channel_token()
    if not token:
        return []
    req = urllib.request.Request(
        "https://api.line.me/v2/bot/richmenu/list",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8")).get("richmenus", [])
    except Exception as e:  # noqa: BLE001
        logger.error("LINE listRichMenu 失败: %s", e)
        return []


def _delete_menu(rich_menu_id: str) -> bool:
    token = line_client._get_channel_token()
    if not token or not rich_menu_id:
        return False
    req = urllib.request.Request(
        f"https://api.line.me/v2/bot/richmenu/{rich_menu_id}",
        headers={"Authorization": f"Bearer {token}"},
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:  # noqa: BLE001
        logger.error("LINE deleteRichMenu 失败: %s", e)
        return False


def _upload_image(rich_menu_id: str, image: bytes, content_type="image/png") -> bool:
    token = line_client._get_channel_token()
    if not token or not rich_menu_id or not image:
        return False
    req = urllib.request.Request(
        f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content",
        data=image,
        headers={"Content-Type": content_type, "Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status == 200
    except Exception as e:  # noqa: BLE001
        logger.error("LINE uploadRichMenuImage 失败: %s", e)
        return False


def _set_default(rich_menu_id: str) -> bool:
    token = line_client._get_channel_token()
    if not token or not rich_menu_id:
        return False
    req = urllib.request.Request(
        f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}",
        headers={"Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:  # noqa: BLE001
        logger.error("LINE setDefaultRichMenu 失败: %s", e)
        return False


def setup_default_menu(image_path: str = None) -> Optional[str]:
    """上线一次性:幂等删旧同名 → createRichMenu(6 区)→ uploadRichMenuImage → setDefault(全用户生效)。

    返回新 richMenuId;任一步失败 → None(不影响现有运行)。需 prod channel token。"""
    path = image_path or _IMAGE_PATH
    try:
        with open(path, "rb") as f:
            image = f.read()
    except OSError as e:
        logger.error("Rich Menu 背景图读取失败: %s", e)
        return None
    for m in _list_menus():  # 幂等:删旧同名,不重复堆叠
        if m.get("name") == MENU_NAME:
            _delete_menu(m.get("richMenuId"))
    rid = line_client.create_rich_menu(build_payload())
    if not rid:
        return None
    mime = "image/jpeg" if path.lower().endswith((".jpg", ".jpeg")) else "image/png"
    if not _upload_image(rid, image, mime):
        return None
    if not _set_default(rid):
        return None
    logger.info("Rich Menu 上线成功: %s", rid)
    return rid


def handle_postback(
    bound_user: dict, reply_token: str, data: str, lang: str, line_user_id: str
) -> bool:
    """rm_* postback → 路由到现有功能(汇总/PDF/明细/能力说明)。非 rm_* → False(交回卡片动作分发)。"""
    from urllib.parse import parse_qsl

    action = dict(parse_qsl(data or "")).get("a", "")
    if action not in _RM_ACTIONS:
        return False
    tid = str(bound_user["tenant_id"]) if bound_user.get("tenant_id") else None
    if not tid:
        return True  # 已识别为菜单动作但无租户 → 吞掉,不漏给卡片分发
    from services.line_binding import line_expense_qa, line_proof, line_reply

    if action in ("rm_summary", "rm_detail"):  # 仅这两路需 ws(proof/help 自取或不需)
        from core import db
        from core.workspace_context import default_workspace_id

        with db.get_cursor_rls(tid) as cur:
            ws = default_workspace_id(cur, tid)
        if action == "rm_summary":
            line_expense_qa.reply_summary(reply_token, lang, tid, ws, line_user_id=line_user_id)
        else:
            line_expense_qa.reply_detail(reply_token, lang, tid, ws, line_user_id)
    elif action == "rm_proof":
        cmd = line_proof.parse_proof_command("ขอ pdf เดือนนี้")  # 等同发「ขอ PDF เดือนนี้」
        if cmd:
            line_proof.start(bound_user, reply_token, line_user_id, lang, cmd)
    elif action == "rm_help":
        line_reply.reply_text_context(
            reply_token,
            line_client.t_line(lang, "line_intro_capability"),
            line_user_id=line_user_id,
            tenant_id=tid,
        )
    return True
