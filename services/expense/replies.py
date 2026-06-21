# -*- coding: utf-8 -*-
"""LINE 智能回复(治复读 · docs/smart-intake/15 §5)。

感谢/求助各有一池回复,按 hash(text) 轮选 —— 同一句确定、不同句换说法,不三句一个模子。
greeting/thanks 走 L1 关键词检测(零成本);问候与跑题文案已收口到 line_i18n(line_greeting /
line_unknown_intent · P1E-1),由 reply_pool 直取,不再走本文件的池。纯函数,可单测。
"""

from __future__ import annotations

from typing import Optional

from services.expense import line_classify, line_guards

_GREETING_WORDS = (
    "你好",
    "您好",
    "在吗",
    "hi",
    "hello",
    "hey",
    "สวัสดี",
    "หวัดดี",
    "こんにちは",
    "もしもし",
)
_THANKS_WORDS = (
    "谢谢",
    "多谢",
    "感谢",
    "thank",
    "thx",
    "ขอบคุณ",
    "ขอบใจ",
    "ありがと",
    "サンキュー",
)

_POOLS = {
    "thanks": {
        "zh": ["不客气😊 还有票就继续发", "应该的~ 随时记账查账", "👍 随时为你记一笔"],
        "th": [
            "ยินดีค่ะ😊 มีใบเสร็จส่งมาได้เรื่อยๆ",
            "ด้วยความยินดีค่ะ~ บันทึกได้ตลอด",
            "👍 พร้อมบันทึกให้เสมอ",
        ],
        "en": [
            "You're welcome 😊 Send more anytime",
            "Anytime~ happy to track it",
            "👍 Always here to log it",
        ],
        "ja": [
            "どういたしまして😊 続けてどうぞ",
            "いつでもどうぞ~ 記帳します",
            "👍 いつでも記録します",
        ],
    },
    "support": {
        "zh": [
            "记账/查账我直接帮你🙌 其他事(开通/计费/对接)请到 pearnly.com 联系我们,会有人跟进",
            "需要人工?记账查账这里就能办;账号/计费类问题到 pearnly.com 留言,团队会回你",
        ],
        "th": [
            "เรื่องบันทึก/ดูค่าใช้จ่ายทำให้ได้เลย🙌 เรื่องบัญชี/ค่าบริการ ทักที่ pearnly.com เดี๋ยวมีทีมดูแล",
            "ต้องการเจ้าหน้าที่? บันทึก/ดูยอดทำที่นี่ได้ ส่วนเรื่องบัญชี/บิล ฝากข้อความที่ pearnly.com",
        ],
        "en": [
            "I handle logging & lookups right here 🙌 For account/billing, reach us at pearnly.com and the team will follow up",
            "Need a human? Expenses I do here; for account/billing leave a note at pearnly.com",
        ],
        "ja": [
            "記帳・照会はここで対応します🙌 アカウント/請求は pearnly.com からご連絡ください、担当が対応します",
            "オペレーター希望ですか?経費はここで、アカウント/請求は pearnly.com へどうぞ",
        ],
    },
    # 只发裸数字(「1」「65」)无物品/卖家:不入账,问一句记啥(治「1→记 1 THB 垃圾条目」)。
    "amount_no_item": {
        "th": [
            "ได้รับตัวเลขมาค่ะ😊 ถ้าจะบันทึกค่าใช้จ่าย บอกหน่อยได้ไหมคะว่าซื้ออะไร เช่น 'กาแฟ 65'",
            "เห็นแค่ตัวเลขค่ะ~ อยากบันทึกพิมพ์แบบนี้ได้เลยนะคะ เช่น 'ค่าน้ำ 50'",
        ],
        "zh": [
            "收到一个数字😊 想记一笔的话告诉我买了啥呀,比如「咖啡 65」",
            "只看到数字哦~ 记一笔可以这样发,例如「水费 50」",
        ],
        "en": [
            "Got a number 😊 To log it, tell me what it was for — like 'coffee 65'",
            "I only see a number~ to record, try e.g. 'water bill 50'",
        ],
        "ja": [
            "数字だけ届きました😊 記録するなら何に使ったか教えてください、例:「コーヒー 65」",
            "数字だけですね~ 記録は例えば「水道代 50」と送ってください",
        ],
    },
    # 语气层(P3A)没发挥时的回落话术:轮选治复读,仍带「记一笔/查账」钩子(reply_pool 注入)。
    "out_of_scope": {
        "th": [
            "อยู่เป็นเพื่อนเลยค่ะ😊 ว่างๆ ส่งค่าใช้จ่ายหรือใบเสร็จมาให้ดูแลได้นะคะ",
            "ฟังอยู่ค่ะ~ พร้อมช่วยบันทึกค่าใช้จ่ายหรือดูยอดเดือนนี้ให้เสมอนะคะ",
            "Pearnly อยู่ตรงนี้เสมอค่ะ😊 อยากบันทึกรายการหรือส่งรูปใบเสร็จ บอกได้เลยค่ะ",
        ],
        "zh": [
            "我在呢😊 想记账或发票据照片随时找我~",
            "陪你聊两句~ 要记一笔或看看这月花了多少,我都在",
            "Pearnly 一直在😊 发笔费用或票据给我都行",
        ],
        "en": [
            "I'm right here 😊 send an expense or a receipt whenever you like~",
            "I'm listening~ ready to log an expense or show this month's spending anytime",
            "Pearnly's always here 😊 just send an expense or a receipt photo",
        ],
        "ja": [
            "そばにいますよ😊 経費や領収書、いつでも送ってくださいね",
            "聞いてますよ~ 記録も今月の確認もいつでもどうぞ",
            "Pearnlyはいつでもここに😊 経費や領収書を送ってください",
        ],
    },
    "unknown": {
        "th": [
            "ขอโทษค่ะ ไม่แน่ใจว่าหมายถึงอะไร😅 อยากบันทึกค่าใช้จ่าย ดูบัญชี หรือส่งใบเสร็จดีคะ",
            "ยังไม่ค่อยเข้าใจประโยคนี้ค่ะ~ พิมพ์เช่น 'กาแฟ 65' เพื่อบันทึก หรือถาม 'เดือนนี้ใช้เท่าไหร่' ได้นะคะ",
            "บอกอีกนิดได้ไหมคะ จะได้ช่วยถูก😊 บันทึก/ดูบัญชี/อ่านใบเสร็จ ทำได้หมดค่ะ",
        ],
        "zh": [
            "我好像没太get到😅 你是想记一笔、查账,还是发张票据给我看看?",
            "嗯…这句我没太懂~ 可以直接说『咖啡 65』记一笔,或问『这月花了多少』",
            "再说清楚点我就能帮上啦😊 记账/查账/识别票据都行",
        ],
        "en": [
            "I didn't quite catch that 😅 Record an expense, check your books, or send a receipt?",
            "Hmm, not sure I got that~ type 'coffee 65' to log it, or ask 'how much this month?'",
            "Tell me a little more and I'll help 😊 I can record, look up, or read receipts.",
        ],
        "ja": [
            "うまく聞き取れませんでした😅 経費の記録、帳簿確認、領収書、どれにしますか?",
            "ちょっと分からなかったです~ 「コーヒー 65」で記録、「今月いくら?」で照会できます",
            "もう少し教えてもらえれば対応できます😊 記録・照会・領収書 OKです",
        ],
    },
    "fraud_refuse": {
        "th": [
            "ขอโทษค่ะ Pearnly ช่วยทำเอกสารปลอมหรือปรับตัวเลขให้ไม่ตรงความจริงไม่ได้นะคะ 🙏 "
            "เราบันทึกตามจริงเพื่อให้บัญชีถูกต้องและยื่นภาษีได้อย่างสบายใจค่ะ"
        ],
        "zh": [
            "抱歉,Pearnly 不能帮忙做假票据或把数字改成不实的哦 🙏 我们只如实记账,让账目正确、报税安心。"
        ],
        "en": [
            "Sorry, Pearnly can't help create fake documents or alter figures to be untrue 🙏 "
            "We only record truthfully so your books stay correct and tax filing stays worry-free."
        ],
        "ja": [
            "申し訳ありませんが、偽の書類作成や数字の改ざんはお手伝いできません🙏 正しい帳簿と安心の申告のため、ありのまま記録します。"
        ],
    },
    "fx_foreign": {
        "th": [
            "ตอนนี้ Pearnly บันทึกเป็นเงินบาท (THB) ค่ะ 🙂 ถ้าจ่ายเป็นสกุลอื่น บอกยอดเป็นบาทได้ไหมคะ เช่น 'ค่าโฆษณา 1800'"
        ],
        "zh": [
            "目前 Pearnly 按泰铢(THB)记账哦🙂 如果是外币付的,告诉我折合多少泰铢就行,比如「广告费 1800」"
        ],
        "en": [
            "Pearnly records in Thai Baht (THB) for now 🙂 If you paid in another currency, just tell me the THB amount, e.g. 'ad fee 1800'"
        ],
        "ja": [
            "今はタイバーツ(THB)で記録します🙂 外貨で払った場合は、バーツ換算額を教えてください。例:「広告費 1800」"
        ],
    },
    "deposit_clarify": {
        "th": [
            "นี่ดูเหมือนเงินมัดจำ/เงินประกันค่ะ ซึ่งไม่ใช่ค่าใช้จ่ายปกติ 🙂 ถ้าจะบันทึกเป็นรายจ่าย พิมพ์เป็นรายการชัดๆ เช่น 'ค่าเช่าล่วงหน้า 1000' ได้เลยค่ะ"
        ],
        "zh": [
            "这看起来是押金/保证金哦,不算普通费用🙂 如果要记成支出,直接发清楚的条目就行,比如「预付租金 1000」"
        ],
        "en": [
            "This looks like a deposit/security, not a regular expense 🙂 To record it as spending, send a clear item like 'prepaid rent 1000'"
        ],
        "ja": [
            "これは保証金/手付金のようで、通常の経費ではありません🙂 費用として記録するなら、例:「前払家賃 1000」と明確に送ってください"
        ],
    },
    # 引导框架(P2「听懂+对症引导」):没记账时按识别出的类别给贴身示例(确定性·非大脑临场编)。
    "guide_vehicle": {
        "th": [
            "ดูเหมือนเป็นเลขทะเบียน/เลขรถ ไม่ใช่จำนวนเงินค่ะ 🙂 ถ้าจะบันทึกค่าใช้จ่ายเกี่ยวกับรถ พิมพ์เช่น 'ค่าน้ำมัน 500' หรือ 'ค่าต่อทะเบียน 1000' ได้เลยค่ะ"
        ],
        "zh": [
            "这看起来是车牌/车辆编号,不是金额哦🙂 要记车相关支出,可以发「油费 500」或「续牌费 1000」"
        ],
        "en": [
            "That looks like a plate/vehicle number, not an amount 🙂 For vehicle costs, try 'fuel 500' or 'registration 1000'"
        ],
        "ja": [
            "ナンバープレート/車両番号のようで、金額ではありません🙂 車関連の費用なら、例:「ガソリン代 500」「車検代 1000」"
        ],
    },
    "guide_phone": {
        "th": [
            "ดูเหมือนเป็นเบอร์โทร ไม่ใช่จำนวนเงินค่ะ 🙂 ถ้าจะบันทึกค่าโทรศัพท์ พิมพ์เช่น 'ค่าโทรศัพท์ 300' ได้เลยค่ะ"
        ],
        "zh": ["这看起来是电话号码,不是金额哦🙂 要记话费,可以发「话费 300」"],
        "en": [
            "That looks like a phone number, not an amount 🙂 For a phone bill, try 'phone bill 300'"
        ],
        "ja": ["電話番号のようで、金額ではありません🙂 電話代なら、例:「電話代 300」"],
    },
    "guide_numnotmoney": {
        "th": [
            "ตัวเลขนี้ดูเหมือนเวลา/จำนวน/อายุ ไม่ใช่จำนวนเงินค่ะ 🙂 ถ้าจะบันทึกค่าใช้จ่าย พิมพ์เป็น 'รายการ + จำนวนเงิน' เช่น 'กาแฟ 65' ได้เลยค่ะ"
        ],
        "zh": [
            "这个数字看起来是时间/数量/年龄,不是金额哦🙂 要记账请发「项目 + 金额」,比如「咖啡 65」"
        ],
        "en": [
            "That number looks like a time/quantity/age, not an amount 🙂 To record, send 'item + price', e.g. 'coffee 65'"
        ],
        "ja": [
            "この数字は時刻/数量/年齢のようで、金額ではありません🙂 記録は「項目+金額」で、例:「コーヒー 65」"
        ],
    },
    "guide_store": {
        "th": [
            "เลขนี้ดูเหมือนชื่อ/สาขาร้าน ไม่ใช่ราคาค่ะ 🙂 ถ้าซื้ออะไรมา บอกของกับราคาได้เลยนะคะ เช่น 'กาแฟ 50'"
        ],
        "zh": [
            "这个数字看起来是店名/门店编号,不是价格哦🙂 买了啥告诉我东西和价钱就行,比如「咖啡 50」"
        ],
        "en": [
            "That number looks like a store name/branch, not a price 🙂 If you bought something, tell me what and how much, e.g. 'coffee 50'"
        ],
        "ja": [
            "これは店名/店舗番号のようで、価格ではありません🙂 何か買ったら、品名と金額を、例:「コーヒー 50」"
        ],
    },
}

# 引导分类:没记账时按"为什么不是金额"归类 → 贴身引导池(pick 在 unknown/out_of_scope 时路由)。
_GUIDE_VEHICLE = ("ทะเบียน", "ป้ายทะเบียน", "เลขรถ", "มอเตอร์ไซค์", "车牌", "车辆", "牌照")
_GUIDE_PHONE = ("เบอร์", "โทรหา", "เบอร์โทร", "phone number", "电话号", "号码")
_GUIDE_NUM = (
    "เวลา",
    "โมง",
    "นาที",
    "ชั่วโมง",
    "อายุ",
    "คน",
    "ห้อง",
    "ชั้น",
    "时间",
    "分钟",
    "小时",
    "年龄",
    "岁",
    "房",
    "层",
)
_GUIDE_STORE = ("711", "7-11", "7-eleven", "เซเว่น")


def guided_kind(text: str) -> Optional[str]:
    """没记账时按类别给贴身引导(确定性):车牌/电话/时间数量/店号 → guide_*;无明确类别 → None。"""
    low = (text or "").lower()
    if not any(c.isdigit() for c in low):  # 无数字 = 纯闲聊 → 不属引导类(走通用 unknown)
        return None
    if any(w in low for w in _GUIDE_VEHICLE):
        return "guide_vehicle"
    if any(w in low for w in _GUIDE_PHONE):
        return "guide_phone"
    if any(w in low for w in _GUIDE_STORE):
        return "guide_store"
    if any(w in low for w in _GUIDE_NUM):
        return "guide_numnotmoney"
    return None


def detect_smalltalk(text: str) -> Optional[str]:
    """L1 关键词判 thanks / greeting / 引导意图(capability·start·upload·零成本);都不是 → None。

    引导意图复用 line_classify.intro_intent,与问候同走 reply_pool(各取 line_i18n 收口文案 + 引导)。
    """
    low = (text or "").strip().lower()
    if not low:
        return None
    if line_guards.is_fraud_request(text):  # 合规红线:伪造票据/逃税 → 拒绝(先于一切·绝不记账)
        return "fraud_refuse"
    if line_guards.is_fx(text):  # 外币 → 不静默当 THB 记·问 THB 金额
        return "fx_foreign"
    if line_guards.is_deposit(text):  # 押金/定金 → 非普通费用·澄清不静默入账
        return "deposit_clarify"
    if any(w in low for w in _THANKS_WORDS):
        return "thanks"
    if any(w in low for w in _GREETING_WORDS):
        return "greeting"
    if line_classify.is_time_query(low):
        return "time_query"
    if line_classify.is_date_query(low):
        return "date_query"
    return line_classify.intro_intent(low) or None


def pick(kind: str, text: str, lang: str) -> str:
    """从 kind 池按 hash(text) 轮选一条(确定但不复读)。kind 未知 → support。

    通用兜底(unknown/out_of_scope)先试按类别给贴身引导(guide_*),命中则替换 kind。
    """
    if kind in ("unknown", "out_of_scope"):
        kind = guided_kind(text) or kind
    pool = _POOLS.get(kind) or _POOLS["support"]
    by_lang = pool.get((lang or "zh").lower()) or pool["zh"]
    idx = sum(ord(c) for c in (text or "x")) % len(by_lang)
    return by_lang[idx]
