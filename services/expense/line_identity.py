# -*- coding: utf-8 -*-
"""LINE 身份层与模型泄露防护 pre-router(P2D · 确定性 · 跑在 L2 大脑之前)。

用户问「你是谁 / 什么模型 / 是不是 GPT/Claude/Gemini / system prompt / API key / ignore
instructions」时,不进业务 LLM 自由回答 —— 统一走 Pearnly 产品身份层(确定性四语模板·泰语优先),
绝不向用户侧输出 Gemini/Claude/GPT/OpenAI/Anthropic/system prompt/internal prompt/API key 等
内部实现信息。问「是不是 AI / 真人」不撒谎:答「Pearnly 智能会计助手」。

同一句若还带业务指令(「你是不是 GPT,咖啡 65」)→ 不拦,放行让记账流程正常处理(身份忽略):
guard 命中分类后,若 looks_like_expense(有金额)即返回 None,业务照常入 handle_expense_text。

模板自带(line_i18n 已满 500);capability 复用既有 line_intro_capability,口径统一。
"""

from __future__ import annotations

import re

# 检测顺序:越权/密钥/系统提示 > 模型 > 能力 > 身份(「are you GPT」归 model 而非 identity)。
_CATEGORY_ORDER = ("injection", "apikey", "system", "model", "capability", "identity")

_KEYWORDS = {
    "injection": (
        "ignore previous",
        "ignore all previous",
        "ignore the above",
        "ignore your instruction",
        "ignore instruction",
        "disregard previous",
        "disregard instruction",
        "forget your instruction",
        "forget previous",
        "override your instruction",
        "jailbreak",
        "developer mode",
        "pretend you are",
        "忽略之前",
        "忽略以上",
        "忽略上面",
        "无视之前",
        "无视以上",
        "忘记之前",
        "忽略你的指令",
        "ละเว้นคำสั่ง",
        "เพิกเฉยคำสั่ง",
        "ลืมคำสั่งก่อน",
    ),
    "apikey": (
        # 「apikey」「api key」由 _APIKEY_RE 先行命中(detect 内先查正则),此处不再列。
        "secret key",
        "access token",
        "密钥",
        "秘钥",
        "金钥",
        "金鑰",
        "เอพีไอคีย์",
    ),
    "system": (
        "system prompt",
        "system message",
        "internal prompt",
        "internal instruction",
        "your prompt",
        "your instructions",
        "show prompt",
        "reveal prompt",
        "提示词",
        "系统提示",
        "系统指令",
        "内部指令",
        "你的提示词",
        "你的指令",
        "คำสั่งระบบ",
        "พรอมต์ระบบ",
    ),
    "model": (
        "what model",
        "which model",
        "what llm",
        "what ai model",
        "base model",
        "underlying model",
        "gpt",
        "chatgpt",
        "claude",
        "gemini",
        "openai",
        "anthropic",
        "deepseek",
        "llama",
        "什么模型",
        "哪个模型",
        "什么大模型",
        "底层模型",
        "用的啥模型",
        "用什么模型",
        "ใช้โมเดล",
        "โมเดลอะไร",
        "โมเดลไหน",
    ),
    "capability": (
        "what can you do",
        "what do you do",
        "how can you help",
        "你能做什么",
        "你会做什么",
        "你能帮我做什么",
        "你有什么功能",
        "有什么功能",
        "ทำอะไรได้บ้าง",
        "ช่วยอะไรได้บ้าง",
        "คุณทำอะไรได้",
    ),
    "identity": (
        "who are you",
        "who r u",
        "what are you",
        "are you a bot",
        "are you a robot",
        "are you human",
        "are you a person",
        "are you real",
        "are you ai",
        "are you an ai",
        "你是谁",
        "你是什么",
        "你是不是ai",
        "你是不是人工智能",
        "你是不是机器人",
        "你是机器人吗",
        "你是真人吗",
        "你是人吗",
        "คุณคือใคร",
        "คุณเป็นใคร",
        "เป็นคนไหม",
        "เป็นคนจริงไหม",
        "เป็นบอท",
        "เป็นหุ่นยนต์",
        "เป็น ai",
    ),
}

# API key 还要抓「api ... key」(中间可有分隔/词)。
_APIKEY_RE = re.compile(r"api[\s_\-]*key", re.IGNORECASE)

# 确定性四语模板(泰语优先 · 不暴露任何底层供应商/系统信息)。capability 见 reply()。
_TEMPLATES = {
    "th": {
        "identity": "สวัสดีค่ะ ฉันคือ Pearnly ผู้ช่วยบัญชีอัจฉริยะค่ะ ช่วยบันทึกค่าใช้จ่าย อ่านใบเสร็จ และดูบัญชีให้คุณได้ พิมพ์รายการหรือส่งรูปใบเสร็จมาได้เลยค่ะ",
        "model": "ฉันคือผู้ช่วยบัญชี Pearnly ค่ะ ขอไม่เปิดเผยรายละเอียดเทคโนโลยีเบื้องหลัง แต่ช่วยบันทึกค่าใช้จ่ายและจัดการบัญชีให้คุณได้เต็มที่ค่ะ",
        "system": "ขออภัยค่ะ ไม่สามารถเปิดเผยการตั้งค่าภายในได้ แต่ Pearnly ช่วยคุณบันทึกค่าใช้จ่าย อ่านใบเสร็จ และดูบัญชีได้ค่ะ",
        "apikey": "ขออภัยค่ะ Pearnly เปิดเผยข้อมูลภายในของระบบไม่ได้ค่ะ หากต้องการบันทึกค่าใช้จ่ายหรือดูบัญชี บอกได้เลยค่ะ",
        "injection": "ฉันทำงานในฐานะผู้ช่วยบัญชี Pearnly เท่านั้นค่ะ ช่วยบันทึกค่าใช้จ่าย อ่านใบเสร็จ และดูบัญชีให้คุณได้เลยค่ะ",
    },
    "en": {
        "identity": "Hi, I'm Pearnly, your smart accounting assistant. I can record expenses, read receipts and look up your books. Just type an expense or send a receipt photo.",
        "model": "I'm the Pearnly accounting assistant. I can't share details about the technology behind me, but I'm here to help with your expenses and bookkeeping.",
        "system": "Sorry, I can't reveal internal settings. But Pearnly can help you record expenses, read receipts and review your books.",
        "apikey": "Sorry, Pearnly can't share any internal system information. I can help with expenses or bookkeeping anytime.",
        "injection": "I only work as the Pearnly accounting assistant. I can help you record expenses, read receipts and review your books.",
    },
    "zh": {
        "identity": "你好,我是 Pearnly 智能会计助手,可以帮你记账、识别票据、查账。直接发一笔费用或票据照片给我就行。",
        "model": "我是 Pearnly 会计助手。底层技术细节不便透露,但记账、票据、查账都能帮你。",
        "system": "抱歉,我不能透露内部设置。不过 Pearnly 能帮你记账、识别票据、查账。",
        "apikey": "抱歉,Pearnly 无法提供任何系统内部信息。需要记账或查账可以直接告诉我。",
        "injection": "我只作为 Pearnly 会计助手工作。可以帮你记账、识别票据、查账。",
    },
    "ja": {
        "identity": "こんにちは。Pearnly のスマート会計アシスタントです。経費の記録、領収書の読み取り、帳簿の確認ができます。経費を入力するか領収書の写真を送ってください。",
        "model": "Pearnly の会計アシスタントです。内部の技術についてはお伝えできませんが、経費や帳簿のお手伝いは全力でいたします。",
        "system": "申し訳ありませんが、Pearnly は内部設定を開示できません。経費記録・領収書読み取り・帳簿確認はお手伝いできます。",
        "apikey": "申し訳ありませんが、Pearnly はシステム内部の情報を提供できません。経費や帳簿のことはいつでもどうぞ。",
        "injection": "私は Pearnly の会計アシスタントとしてのみ動作します。経費記録・領収書・帳簿のお手伝いができます。",
    },
}


def detect(text) -> str | None:
    """命中身份/安全类 → 返回分类(injection/apikey/system/model/capability/identity);否则 None。"""
    t = str(text or "").lower()
    if not t.strip():
        return None
    if _APIKEY_RE.search(t):
        return "apikey"
    for cat in _CATEGORY_ORDER:
        if any(kw in t for kw in _KEYWORDS[cat]):
            return cat
    return None


def reply(category: str, lang: str) -> str:
    """分类 + 语言 → 确定性 Pearnly 文案。capability 复用既有能力说明,口径统一。"""
    lang = lang if lang in _TEMPLATES else "th"
    if category == "capability":
        from services.line_binding import line_client

        return line_client.t_line(lang, "line_intro_capability")
    return _TEMPLATES[lang].get(category) or _TEMPLATES[lang]["identity"]


def guard(text, lang: str) -> str | None:
    """pre-router:命中身份/安全类【且不含业务指令】→ 返回确定性模板;否则 None(放行业务流程)。

    同句含业务(looks_like_expense·有金额,如「你是不是 GPT,咖啡 65」)→ 返回 None,记账正常进行,
    身份问题忽略(不拦业务)。
    """
    cat = detect(text)
    if not cat:
        return None
    from services.expense import line_quick_entry as qe

    if qe.looks_like_expense(text):
        return None
    return reply(cat, lang)
