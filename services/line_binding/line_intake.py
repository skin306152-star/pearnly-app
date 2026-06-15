# -*- coding: utf-8 -*-
"""LINE 进项整合 glue(取链接命令 / Rich Menu · 阶段三)。

把纯构建接成可用:取链接命令回复文案、Rich Menu 配置。统一智能通道下图/文均直落采购,
不再出 Flex 确认卡(Zihao 2026-06-15 拍板),故 glue 只剩取链接与菜单。
"""

from __future__ import annotations

from services.line_binding import line_commands

# 取链接命令回复(命中但暂无链接时引导去网页连 Google/导出)。
_LINK_REPLY = {
    "zh": "在网页「集成中心」连接 Google 后,这里可一键取回 Drive/Sheet 链接:{url}",
    "th": "เชื่อม Google ที่หน้าเว็บ「ศูนย์เชื่อมต่อ」ก่อน แล้วขอลิงก์ Drive/Sheet ได้ที่นี่: {url}",
    "en": "Connect Google in the web Integrations page, then get your Drive/Sheet link here: {url}",
    "ja": "Web「連携センター」でGoogleを接続後、Drive/Sheetリンクをここで取得できます: {url}",
}


def parse_link_command(text: str):
    """文字 → 取链接命令(drive_link/sheet_link/None)· 透传 line_commands。"""
    return line_commands.parse_link_command(text)


def link_reply(cmd: str, lang: str, *, web_url: str) -> str:
    """取链接命令 → 回复文案(引导网页取链接·真链接由网页/导出给)。"""
    tmpl = _LINK_REPLY.get((lang or "zh").lower(), _LINK_REPLY["zh"])
    return tmpl.format(url=web_url)


# Rich Menu 6 格(2500×843 · 3 列 2 行)· 入口:拍票/取Drive/取Sheet/费用汇总/打开网页/帮助。
_RM_CELLS = [
    {"key": "shoot", "action": {"type": "message", "text": "拍进项票"}},
    {"key": "drive", "action": {"type": "message", "text": "ขอ link drive"}},
    {"key": "sheet", "action": {"type": "message", "text": "ขอ google sheet"}},
    {"key": "expense", "action": {"type": "message", "text": "เมนู"}},
    {"key": "web", "action": {"type": "uri", "uri": ""}},  # 运行时填 LIFF/网页 URL
    {"key": "help", "action": {"type": "message", "text": "help"}},
]


def rich_menu_payload(*, name: str = "pearnly-main", web_url: str = "") -> dict:
    """Rich Menu 配置 dict(纯·喂 LINE createRichMenu)。6 格各映射一命令/URI。"""
    cw, ch = 833, 421
    areas = []
    for i, cell in enumerate(_RM_CELLS):
        col, rown = i % 3, i // 3
        action = dict(cell["action"])
        if action.get("type") == "uri":
            action["uri"] = web_url or "https://pearnly.com/home"
        areas.append(
            {
                "bounds": {"x": col * cw, "y": rown * ch, "width": cw, "height": ch},
                "action": action,
            }
        )
    return {
        "size": {"width": 2500, "height": 843},
        "selected": True,
        "name": name,
        "chatBarText": "Pearnly",
        "areas": areas,
    }
