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
from services.expense import line_classify, line_identity
from services.line_binding import (
    line_bind_i18n,
    line_card_actions,
    line_client,
    line_expense,
    line_imagemap,
    line_intake,
    line_proof,
    line_reply,
    line_rich_menu,
    line_unbind,
)

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


def _reply_card_or_text(
    reply_token: str,
    card_key: str,
    text_msg: dict,
    *,
    lang: str,
    line_user_id: str,
    quote_token: str = "",
    tenant_id=None,
) -> None:
    """有设计图卡就发图卡(Zihao 定:只做泰语图卡,不发文字版);无图卡才回落 text_msg。

    lang 仅用于回落文字(card_key 未交付图卡时)。
    """
    if line_imagemap.has_card(card_key):
        line_reply.reply_messages_context(
            reply_token,
            [line_imagemap.card_message(card_key)],
            line_user_id=line_user_id,
            tenant_id=tenant_id,
        )
        return
    line_reply.reply_messages_context(
        reply_token,
        [text_msg],
        quote_token=quote_token,
        line_user_id=line_user_id,
        tenant_id=tenant_id,
    )


async def _handle_line_event(ev: dict):
    """单个 LINE 事件处理"""
    ev_type = ev.get("type")
    src = ev.get("source") or {}
    line_user_id = src.get("userId")
    reply_token = ev.get("replyToken")

    # follow:用户加 Bot 好友 → 发欢迎卡(泰语图卡 A1 / 其他语言文字版)。
    # ⚠️ 若 LINE 后台仍开着「加好友自动问候 Greeting」会双发,需在后台关掉(见交接说明)。
    if ev_type == "follow":
        if reply_token:
            lang = _ev_lang(ev)
            _reply_card_or_text(
                reply_token,
                "welcome",
                line_bind_i18n.follow_welcome_msg(lang),
                lang=lang,
                line_user_id=line_user_id,
            )
        return

    # unfollow:用户删 Bot 好友 → 清理绑定,避免残留(无法回复,LINE 限制)
    if ev_type == "unfollow":
        removed = db.unbind_line_by_line_user_id(line_user_id) if line_user_id else False
        logger.info(f"[line] 用户 {line_user_id} 删除了 Bot 好友 · 解绑={removed}")
        return

    # postback:数据卡按钮(撤销/确认)→ 做账安全带落地(docs/smart-intake/15 §4)
    if ev_type == "postback":
        if not reply_token or not line_user_id:
            return
        bound = db.get_user_by_line_user_id(line_user_id)
        if not bound:
            return
        line_reply.begin_loading(line_user_id)
        lang = bound.get("preferred_lang") or _ev_lang(ev)
        data = (ev.get("postback") or {}).get("data", "")
        # Rich Menu 区(rm_*)→ 路由到现有汇总/明细/PDF/能力说明;非菜单 postback 交卡片动作分发。
        if line_rich_menu.handle_postback(bound, reply_token, data, lang, line_user_id):
            return
        line_card_actions.handle_postback(bound, reply_token, data, lang)
        return

    # message
    if ev_type == "message":
        msg = ev.get("message") or {}
        msg_type = msg.get("type")

        # 文字消息:判断是否绑定码
        if msg_type == "text":
            text = (msg.get("text") or "").strip()
            # v118.25.4 · 把 ev 传过去 · 让 _handle_line_text 能拿到用户语言
            # 引用底座(P1A):quotedMessageId = 用户长按 reply 的那条消息 id → 精确定位业务单。
            await _handle_line_text(
                line_user_id,
                reply_token,
                text,
                ev,
                quote_token=msg.get("quoteToken"),
                quoted_message_id=msg.get("quotedMessageId"),
            )
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
                    line_reply.begin_loading(line_user_id)
                    _reply_card_or_text(
                        reply_token,
                        "image_not_bound",
                        line_bind_i18n.image_not_bound_msg(lang),
                        lang=lang,
                        line_user_id=line_user_id,
                        quote_token=msg.get("quoteToken"),
                    )
                return

            # v118.25.4 · 已绑定用户 · 优先用 Pearnly 网站偏好语言 · 兜底用 LINE 语言(不再写死 zh)
            lang = bound_user.get("preferred_lang") or _ev_lang(ev)

            # 收到票据即用 replyToken 回处理中 ack(P1E-1·有上下文):说明正在读取金额/日期/卖家/VAT/明细。
            # 结果卡稍后异步 push;此处 replyToken 仅这一次用,不影响后续。
            if reply_token:
                line_reply.reply_text_context(
                    reply_token,
                    line_client.t_line(lang, "line_processing_receipt"),
                    quote_token=msg.get("quoteToken"),
                    line_user_id=line_user_id,
                    tenant_id=bound_user.get("tenant_id"),
                )

            # 多图排队(#4):每张图启一个后台任务,但 per-user FIFO 锁让它们一张张串行处理、
            # 一张卡发完再下一张、不乱序(转圈移到轮到该图时才发 · 见 process_line_image_serial)。
            # _handle_line_image_ocr/串行包装已抽到 services/ocr/line_image_ocr.py(无循环 import)。
            from services.ocr.line_image_ocr import process_line_image_serial

            asyncio.create_task(
                process_line_image_serial(
                    bound_user=bound_user,
                    line_user_id=line_user_id,
                    message_id=message_id,
                    filename=filename,
                    lang=lang,
                    quote_token=msg.get("quoteToken"),
                )
            )
            return

        # 其他类型消息
        if reply_token:
            # v118.25.4 · 已绑定取用户偏好 · 未绑定用规范化 LINE 语言(不再 zh fallback)
            bound_user = db.get_user_by_line_user_id(line_user_id) if line_user_id else None
            lang = (bound_user.get("preferred_lang") if bound_user else None) or _ev_lang(ev)
            line_reply.begin_loading(line_user_id)
            _reply_card_or_text(
                reply_token,
                "unsupported",
                {"type": "text", "text": line_client.t_line(lang, "unsupported")},
                lang=lang,
                line_user_id=line_user_id,
                quote_token=msg.get("quoteToken"),
                tenant_id=(bound_user.get("tenant_id") if bound_user else None),
            )
        return


async def _handle_line_text(
    line_user_id: str,
    reply_token: str,
    text: str,
    ev: dict,
    quote_token: str = None,
    quoted_message_id: str = None,
):
    """处理 LINE 文字消息(v118.25.4 · ev 用于 fallback 拿 LINE 用户语言)"""
    if not reply_token or not line_user_id:
        return

    # 处理开始前转圈(P1C·best-effort):文本任意路径(绑定/记账/查账/闲聊)都先让用户看到正在处理。
    line_reply.begin_loading(line_user_id)

    # v118.25.4 · 在最开头算出 ev_lang 备用 · 所有未确定身份的 fallback 都用它
    ev_lang = _ev_lang(ev)

    # 6 位数字 → 尝试当作绑定码
    if len(text) == 6 and text.isdigit():
        user_id = db.consume_line_binding_code(text)
        if not user_id:
            # v118.25.4 · 绑定码无效 · 还不知道是哪个 Pearnly 用户 · 用 LINE 语言
            _reply_card_or_text(
                reply_token,
                "bind_invalid",
                line_bind_i18n.bind_invalid_msg(ev_lang),
                lang=ev_lang,
                line_user_id=line_user_id,
                quote_token=quote_token,
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
            _reply_card_or_text(
                reply_token,
                "bind_conflict",
                line_bind_i18n.bind_conflict_msg(lang),
                lang=lang,
                line_user_id=line_user_id,
                quote_token=quote_token,
            )
            return

        # 绑定成功 → A5 成功卡 + A12 新手轮播(一次发)。
        line_reply.reply_messages_context(
            reply_token,
            line_imagemap.welcome_messages(),
            line_user_id=line_user_id,
            tenant_id=(user.get("tenant_id") if user else None),
        )
        return

    # 非绑定码 · 判断是否已绑定
    bound_user = db.get_user_by_line_user_id(line_user_id)
    if not bound_user:
        # 未绑定也让用户先看「能做什么」(A2 能力卡 · 公开信息)→ 再引导连接。
        if line_classify.intro_intent(text) == "capability":
            _reply_card_or_text(
                reply_token,
                "capability",
                {"type": "text", "text": line_client.t_line(ev_lang, "line_intro_capability")},
                lang=ev_lang,
                line_user_id=line_user_id,
                quote_token=quote_token,
            )
            return
        # v118.25.4 · 未绑定 · 用 LINE 用户语言(之前写死 zh · 是已知简化 bug · 现在修)
        _reply_card_or_text(
            reply_token,
            "need_bind",
            line_bind_i18n.need_bind_msg(ev_lang),
            lang=ev_lang,
            line_user_id=line_user_id,
            quote_token=quote_token,
        )
    else:
        # 理解层第一步(line-language-follow-p0):先把语言判清楚,再进任何执行(记账/查账/闲聊)。
        # 明说「说中文 / speak English」→ 锁定偏好 + 用新语言确认;否则按这条消息实际打的字跟随,
        # 再回落账号偏好 / LINE 事件语言。治「中文求说中文却泰语顶回」+「同会话语言漂移」。
        from services.expense import line_lang

        switched = line_lang.detect_lang_switch(text)
        if switched:
            db.update_user_preferred_lang(bound_user.get("id"), switched)
            line_reply.reply_text_context(
                reply_token,
                line_lang.switch_ack(switched),
                quote_token=quote_token,
                line_user_id=line_user_id,
                tenant_id=bound_user.get("tenant_id"),
            )
            return
        lang = line_lang.resolve_reply_lang(text, bound_user.get("preferred_lang"), ev_lang)
        tid = bound_user.get("tenant_id")
        # 主动解绑命令(破坏性·先于业务):明确「解绑/unbind/ยกเลิกการเชื่อมต่อ」→ 出确认卡(非直解)。
        if line_unbind.detect_unbind(text):
            line_unbind.route(bound_user, reply_token, line_user_id, quote_token=quote_token)
            return
        # 取链接命令(ขอ link drive / ขอ sheet)→ 引导网页取 Drive/Sheet 链接(接阶段二外流)。
        cmd = line_intake.parse_link_command(text)
        if cmd:
            line_reply.reply_text_context(
                reply_token,
                line_intake.link_reply(cmd, lang, web_url=_WEB_INTEGRATIONS_URL),
                quote_token=quote_token,
                line_user_id=line_user_id,
                tenant_id=tid,
            )
            return
        # 本月凭证 PDF 命令(C-1):0 笔回提示·有笔即回「生成中」+异步打包推下载卡。
        proof_cmd = line_proof.parse_proof_command(text)
        if proof_cmd and line_proof.start(bound_user, reply_token, line_user_id, lang, proof_cmd):
            return
        # P2D 身份层/模型泄露防护(跑在 L2 大脑前):身份/模型/系统提示/API key/越权问题(且不含业务
        # 指令)→ Pearnly 产品身份层确定性四语回复,不进业务 LLM、不暴露底层供应商/系统信息。含业务
        # 指令(如「你是不是 GPT,咖啡 65」)则放行,记账正常进行。
        guard_reply = line_identity.guard(text, lang)
        if guard_reply:
            line_reply.reply_text_context(
                reply_token,
                guard_reply,
                quote_token=quote_token,
                line_user_id=line_user_id,
                tenant_id=tid,
            )
            return
        # ★ 强锚定(Slice 3 · Anchored Action):本轮引用了一张卡 → 整句只围绕它,在记账/大脑/语气层
        # 之前拦截(永不另记一笔/操作别的单);无引用完全不变。
        from services.expense import line_anchored

        if line_anchored.maybe_dispatch(
            bound_user,
            reply_token,
            line_user_id,
            text,
            lang,
            quoted_message_id,
            quote_token=quote_token,
        ):
            return
        # 文本路 · 置信驱动入账(docs/smart-intake/15):记账意图→解析→高置信直接入账+数据卡,
        # 其余草稿请确认;闲聊/查账/问答→智能回复。回执引用原句(quoteToken)。
        if line_expense.handle_expense_text(
            bound_user,
            reply_token,
            line_user_id,
            text,
            lang,
            quote_token=quote_token,
            quoted_message_id=quoted_message_id,
        ):
            return
        # 兜底(P0):认不出 → 能力说明(P1E-1·专业引导,不再 demo 提示)。
        line_reply.reply_text_context(
            reply_token,
            line_client.t_line(lang, "line_intro_capability"),
            quote_token=quote_token,
            line_user_id=line_user_id,
            tenant_id=tid,
        )


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
