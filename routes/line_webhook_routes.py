"""
line_webhook_routes.py · LINE Bot Messaging API webhook(REFACTOR-B1)

从 app.py L3263-3502 抽出 · 0 业务逻辑改:
    POST /api/line/webhook   LINE Bot follow / unfollow / text / image|file 事件分发

包含:
    - _normalize_line_lang  LINE 语言代码 → 4 语 (zh/en/th/ja)
    - _ev_lang(ev)          从 event 安全拿语言并规范化
    - _handle_line_event    单事件路由(follow 不回 · 欢迎语走 OA Greeting / unfollow / message)
    - _handle_line_text     绑定码消费 / 引导提示
    - line_webhook 入口路由(签名校验 → 事件分发)

LINE 图片/文件 → OCR 路径(`_handle_line_image_ocr`)已抽到 services/ocr/line_image_ocr.py
(REFACTOR-WB-app · 2026-06-01)。`_handle_line_event` 内 import 调到 · 无循环 import。

E2E 闸:spec 14(LINE binding)间接覆盖签名校验前的拒绝路径。
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Request

from core import db
from services.line_binding import line_client, line_intake, line_postback

logger = logging.getLogger(__name__)

# 取链接命令引导去网页(集成中心连 Google 后取 Drive/Sheet 链接)。
_WEB_INTEGRATIONS_URL = "https://pearnly.com/home#integrations"

router = APIRouter()


# v118.25.4 · LINE 用户语言规范化(把 LINE 给的多种语言代码映射到我们支持的 4 语)
def _normalize_line_lang(raw_lang: str) -> str:
    """
    LINE 平台给的语言代码可能是 zh-Hant / zh-CN / zh-TW / en-US / ja-JP 等
    我们只支持 4 语:zh / en / th / ja · 主市场泰国
    完全无信息时 fallback 到 th(不是 zh)
    """
    if not raw_lang:
        return "th"
    rl = str(raw_lang).lower().replace("_", "-")
    if rl.startswith("zh"):
        return "zh"
    if rl.startswith("en"):
        return "en"
    if rl.startswith("ja"):
        return "ja"
    if rl.startswith("th"):
        return "th"
    return "th"  # 主市场 fallback


def _ev_lang(ev: dict) -> str:
    """从 LINE event 安全拿语言并规范化"""
    try:
        raw = line_client.pick_lang_from_line_event(ev) or ""
    except Exception:
        raw = ""
    return _normalize_line_lang(raw)


async def _handle_line_event(ev: dict):
    """单个 LINE 事件处理"""
    ev_type = ev.get("type")
    src = ev.get("source") or {}
    line_user_id = src.get("userId")
    reply_token = ev.get("replyToken")

    # follow:用户加 Bot 好友 · 欢迎语由 LINE OA Greeting 卡片负责(避免与机器人重复)· 机器人不回
    if ev_type == "follow":
        return

    # unfollow:用户删 Bot
    if ev_type == "unfollow":
        logger.info(f"[line] 用户 {line_user_id} 删除了 Bot 好友")
        return

    # postback:Flex 卡按钮([确认入采购]/[记为费用])→ 接 intake 分流
    if ev_type == "postback":
        data = (ev.get("postback") or {}).get("data", "")
        await _handle_line_postback(line_user_id, reply_token, data, ev)
        return

    # message
    if ev_type == "message":
        msg = ev.get("message") or {}
        msg_type = msg.get("type")

        # 文字消息:判断是否绑定码
        if msg_type == "text":
            text = (msg.get("text") or "").strip()
            # v118.25.4 · 把 ev 传过去 · 让 _handle_line_text 能拿到用户语言
            await _handle_line_text(line_user_id, reply_token, text, ev)
            return

        # 图片 / 文件消息:统一走 OCR 入口(支持 PDF / 图片 / Excel / CSV / Word / TXT)
        if msg_type in ("image", "file"):
            message_id = msg.get("id")
            filename = msg.get("fileName") if msg_type == "file" else f"line_{message_id}.jpg"
            # 检查是否绑定
            bound_user = db.get_user_by_line_user_id(line_user_id) if line_user_id else None
            if not bound_user:
                if reply_token:
                    # v118.25.4 · 用规范化后的 LINE 用户语言
                    lang = _ev_lang(ev)
                    line_client.reply_text(
                        reply_token,
                        line_client.t_line(lang, "image_not_bound"),
                    )
                return

            # v118.25.4 · 已绑定用户 · 优先用 Pearnly 网站偏好语言 · 兜底用 LINE 语言(不再写死 zh)
            lang = bound_user.get("preferred_lang") or _ev_lang(ev)

            # 立即 reply 告知"识别中"(replyToken 一分钟有效 · 必须快)
            if reply_token:
                line_client.reply_text(
                    reply_token,
                    line_client.t_ocr(lang, "processing"),
                )

            # 启后台任务跑 OCR + push 结果
            # _handle_line_image_ocr 已抽到 services/ocr/line_image_ocr.py
            # (REFACTOR-WB-app · 2026-06-01)· 不再经 app.py · 无循环 import。
            from services.ocr.line_image_ocr import _handle_line_image_ocr

            asyncio.create_task(
                _handle_line_image_ocr(
                    bound_user=bound_user,
                    line_user_id=line_user_id,
                    message_id=message_id,
                    filename=filename,
                    lang=lang,
                )
            )
            return

        # 其他类型消息
        if reply_token:
            # v118.25.4 · 已绑定取用户偏好 · 未绑定用规范化 LINE 语言(不再 zh fallback)
            bound_user = db.get_user_by_line_user_id(line_user_id) if line_user_id else None
            lang = (bound_user.get("preferred_lang") if bound_user else None) or _ev_lang(ev)
            line_client.reply_text(
                reply_token,
                line_client.t_line(lang, "unsupported"),
            )
        return


async def _handle_line_text(line_user_id: str, reply_token: str, text: str, ev: dict):
    """处理 LINE 文字消息(v118.25.4 · ev 用于 fallback 拿 LINE 用户语言)"""
    if not reply_token or not line_user_id:
        return

    # v118.25.4 · 在最开头算出 ev_lang 备用 · 所有未确定身份的 fallback 都用它
    ev_lang = _ev_lang(ev)

    # 6 位数字 → 尝试当作绑定码
    if len(text) == 6 and text.isdigit():
        user_id = db.consume_line_binding_code(text)
        if not user_id:
            # v118.25.4 · 绑定码无效 · 还不知道是哪个 Pearnly 用户 · 用 LINE 语言
            line_client.reply_text(
                reply_token,
                line_client.t_line(ev_lang, "bind_invalid"),
            )
            return

        # 查 mrpilot 用户(为拿 preferred_lang)
        # v118.25.4 · 已确定身份 · 优先用网站偏好 · 兜底用 LINE 语言
        user = db.find_user_by_id(user_id)
        lang = (user.get("preferred_lang") if user else None) or ev_lang

        # 获取 LINE 用户昵称 / 头像
        profile = line_client.get_user_profile(line_user_id) or {}
        display_name = profile.get("displayName")
        picture_url = profile.get("pictureUrl")

        ok = db.create_or_update_line_binding(
            user_id=user_id,
            line_user_id=line_user_id,
            display_name=display_name,
            picture_url=picture_url,
        )
        if not ok:
            line_client.reply_text(
                reply_token,
                line_client.t_line(lang, "bind_conflict"),
            )
            return

        username = user.get("username") if user else ""
        line_client.reply_text(
            reply_token,
            line_client.t_line(
                lang,
                "bind_success",
                username=username,
                display_name=display_name or (line_user_id[:8] + "…"),
            ),
        )
        return

    # 非绑定码 · 判断是否已绑定
    bound_user = db.get_user_by_line_user_id(line_user_id)
    if not bound_user:
        # v118.25.4 · 未绑定 · 用 LINE 用户语言(之前写死 zh · 是已知简化 bug · 现在修)
        line_client.reply_text(
            reply_token,
            line_client.t_line(ev_lang, "need_bind"),
        )
    else:
        # v118.25.4 · 已绑定 · 优先用户偏好 · 兜底 LINE 语言
        lang = bound_user.get("preferred_lang") or ev_lang
        # 取链接命令(ขอ link drive / ขอ sheet)→ 引导网页取 Drive/Sheet 链接(接阶段二外流)。
        cmd = line_intake.parse_link_command(text)
        if cmd:
            line_client.reply_text(
                reply_token, line_intake.link_reply(cmd, lang, web_url=_WEB_INTEGRATIONS_URL)
            )
            return
        # F10 · 商户(非 firm)+ 开 expense + 文本含金额 → 记一笔费用并回执;否则回功能提示(现状不变)。
        recorded = _maybe_record_line_expense(bound_user, text, lang)
        if recorded:
            line_client.reply_text(reply_token, recorded)
            return
        username = bound_user.get("username") or ""
        line_client.reply_text(
            reply_token,
            line_client.t_line(lang, "already_bound_hint", username=username),
        )


async def _handle_line_postback(line_user_id: str, reply_token: str, data: str, ev: dict):
    """Flex 卡按钮回调 → intake 分流(confirm=入采购 / redirect=指定方向)。

    doc_id = 待归类 intake_item id(LINE_FLEX_INTAKE 开时由 OCR 落)。查 item 的套账 →
    resolve_inbox 建草稿单。item 不存在/未开 staging → 友好回执,不报错。
    """
    if not reply_token or not line_user_id:
        return
    parsed = line_postback.parse(data)
    action = parsed.get("action")
    if not action:
        return
    bound = db.get_user_by_line_user_id(line_user_id)
    if not bound:
        return
    lang = bound.get("preferred_lang") or _ev_lang(ev)
    tid = str(bound["tenant_id"]) if bound.get("tenant_id") else None
    item_id = parsed.get("doc_id")
    inbox_action = (
        "purchase"
        if action == line_postback.ACTION_CONFIRM
        else (parsed.get("direction") or "expense")
    )
    if inbox_action not in ("purchase", "expense"):
        inbox_action = "expense"
    try:
        from services.purchase import intake as intake_svc
        from services.purchase import settings as settings_svc

        with db.get_cursor_rls(tid, commit=True) as cur:
            cur.execute(
                "SELECT workspace_client_id FROM intake_items "
                "WHERE id = %s AND tenant_id = %s AND status = 'pending'",
                (item_id, tid),
            )
            r = cur.fetchone()
            if not r:
                line_client.reply_text(reply_token, line_client.t_line(lang, "unsupported"))
                return
            ws = r["workspace_client_id"]
            cfg = settings_svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
            intake_svc.resolve_inbox(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                item_id=item_id,
                action=inbox_action,
                created_by=str(bound["id"]),
                settings=cfg,
            )
        line_client.reply_text(reply_token, line_intake.ack_reply(inbox_action, lang))
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[line postback] resolve failed: {e}")
        line_client.reply_text(reply_token, line_client.t_line(lang, "unsupported"))


def _maybe_record_line_expense(bound_user: dict, text: str, lang: str):
    """商户(business_type 非 firm/未选)+ 开 expense + 文本含金额 → 记一笔 posted 费用,返回回执文案。
    事务所(firm/null)/ 未开 expense / 无默认套账 / 无金额 / 任何异常 → None(LINE 主路径 + 事务所底线一字不破坏)。"""
    try:
        tid = bound_user.get("tenant_id")
        if not tid:
            return None
        from core.workspace_context import default_workspace_id
        from services.purchase import intake as intake_svc

        with db.get_cursor_rls(str(tid), commit=True) as cur:
            if not intake_svc.line_expense_gate_open(cur, tenant_id=str(tid)):
                return None
            ws = default_workspace_id(cur, str(tid))
            if ws is None:
                return None
            created_by = str(bound_user["id"]) if bound_user.get("id") else None
            res = intake_svc.record_line_expense(
                cur,
                tenant_id=str(tid),
                workspace_client_id=ws,
                text=text,
                created_by=created_by,
            )
        if not res:
            return None
        return line_client.t_line(
            lang, "expense_recorded", desc=res["description"], amount=res["amount"]
        )
    except Exception:
        logger.exception("[line] expense record failed; fall back to hint")
        return None


@router.post("/api/line/webhook")
async def line_webhook(request: Request):
    """
    LINE Messaging API webhook 入口。
    处理的事件:
      - follow:用户加 Bot 好友 · 回欢迎语 + 教绑定
      - unfollow:用户删 Bot · 记录不处理(LINE 不允许回复)
      - message.text:文字 · 若是 6 位数字 → 尝试绑定码消费
      - message.image:T1 轮 3 实现 OCR · 本轮提示「即将上线」
      - 其他 type:忽略
    """
    body = await request.body()
    signature = request.headers.get("x-line-signature", "")

    # 签名校验(仅在 Secret 已配置时强制)
    if not line_client.verify_signature(body, signature):
        logger.warning("[line_webhook] 签名校验失败")
        # 返回 200 避免 LINE 认为 webhook 挂掉 · 但不处理事件
        return {"status": "ignored"}

    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as e:
        logger.error(f"[line_webhook] JSON 解析失败: {e}")
        return {"status": "bad_json"}

    events = payload.get("events") or []
    for ev in events:
        try:
            await _handle_line_event(ev)
        except Exception as e:
            logger.error(f"[line_webhook] 事件处理异常: {e}")

    return {"status": "ok"}
