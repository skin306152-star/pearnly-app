# -*- coding: utf-8 -*-
"""Agent 文案的 LINE 渲染层(WP5)—— key(+slots)占位串 → 4 语真文案。

为什么不直接读 `static/i18n-data.js`:那是浏览器侧 i18n,LINE 运行时(Python)不加载它;
而 LINE 文案历来走 Python 模板(见 line_i18n.py)。本模块是 agent.* 在 Python 侧的渲染源,
键与 i18n-data.js 的 agent.* 保持一致(test_agent_i18n 机械守门,防前后端漂),网页 Agent 入口
(M5)再共用同一套键。

值同源说明:28 个键与 i18n-data.js 逐字一致;`ok.history / ok.history_summary /
ok.usage_this_month` 三个 M1 真会渲染的键按当前数据层能力诚实改写——丢掉 M1 取不到的「月度
合计฿/单据数/分类」槽位(否则空槽渲染成「合计 ฿」误导),M2 数据层补齐后两侧一并回填富版。

渲染容错:缺槽位 → 留空(绝不把 `{slot}` 或 error_code 吐给用户);占位串里值含分隔符已在
copy_map 侧消毒。lang 非 4 语之一 → 落 th(主市场)。
"""

from __future__ import annotations

DEFAULT_LANG = "th"

# agent.* 4 语模板。键集合与 static/i18n-data.js 一致(test 守门)。
_T: dict[str, dict[str, str]] = {
    # ── 反问(ask) ──
    "agent.ask.which_doc": {
        "zh": "哪一张?发我单号或店名",
        "en": "Which document? Send the invoice no. or shop name",
        "th": "ใบไหนคะ ลองพิมพ์เลขใบเสร็จหรือชื่อร้านให้หน่อย",
        "ja": "どの伝票ですか?領収書番号か店名を送ってください",
    },
    "agent.ask.amount": {
        "zh": "金额多少?",
        "en": "What is the amount?",
        "th": "จำนวนเงินเท่าไหร่คะ",
        "ja": "金額はいくらですか?",
    },
    "agent.ask.endpoint": {
        "zh": "推到哪个端点?(有 {endpoints})",
        "en": "Which ERP endpoint? ({endpoints})",
        "th": "จะส่งเข้าระบบไหนคะ (มี {endpoints})",
        "ja": "どの ERP に送りますか?({endpoints})",
    },
    "agent.ask.period": {
        "zh": "哪个区间?如本月/六月",
        "en": "Which period? e.g. this month",
        "th": "ช่วงไหนคะ เช่น เดือนนี้ หรือ มิถุนายน",
        "ja": "どの期間ですか?例:今月、6月",
    },
    "agent.ask.keyword": {
        "zh": "找什么关键词?如店名/单号",
        "en": "Search for what? e.g. shop name or invoice no.",
        "th": "หาคำว่าอะไรคะ เช่น ชื่อร้านหรือเลขใบเสร็จ",
        "ja": "何を検索しますか?例:店名や領収書番号",
    },
    "agent.ask.status": {
        "zh": "看哪个状态?已确认/待处理/失败",
        "en": "Which status? confirmed / pending / failed",
        "th": "ดูสถานะไหนคะ: ยืนยันแล้ว / รอดำเนินการ / ล้มเหลว",
        "ja": "どのステータスですか?確認済み / 保留中 / 失敗",
    },
    # ── 确认(confirm · B 档 · M3 才会触发) ──
    "agent.confirm.push": {
        "zh": '将把 {invoice_no}({amount}฿)推进 {endpoint}·回"确认"执行',
        "en": 'Will push {invoice_no} ({amount} THB) to {endpoint} · reply "OK" to proceed',
        "th": 'จะส่งใบ {invoice_no} ({amount} บาท) เข้า {endpoint} · พิมพ์ "ยืนยัน" เพื่อดำเนินการ',
        "ja": "{invoice_no}({amount} バーツ)を {endpoint} に送信します · 「OK」と返信で実行",
    },
    "agent.confirm.record": {
        "zh": '将记一笔 {amount}฿({vendor})·回"确认"',
        "en": 'Will record an expense of {amount} THB ({vendor}) · reply "OK"',
        "th": 'จะบันทึกค่าใช้จ่าย {amount} บาท ({vendor}) · พิมพ์ "ยืนยัน"',
        "ja": "{amount} バーツ({vendor})の経費を記録します · 「OK」と返信",
    },
    "agent.confirm.recon": {
        "zh": '将对账 {filename}·回"确认"',
        "en": 'Will reconcile {filename} · reply "OK"',
        "th": 'จะกระทบยอดไฟล์ {filename} · พิมพ์ "ยืนยัน"',
        "ja": "{filename} を照合します · 「OK」と返信",
    },
    "agent.confirm.cancelled": {
        "zh": "已取消",
        "en": "Cancelled.",
        "th": "ยกเลิกแล้วค่ะ",
        "ja": "キャンセルしました",
    },
    # ── 成功回执(ok) ──
    # ★ M1 诚实改写:history/summary 计数是保留期窗口(非严格本月),去掉取不到的合计฿/分类。
    "agent.ok.history": {
        "zh": "识别记录 {count} 张",
        "en": "Found {count} documents",
        "th": "พบเอกสาร {count} รายการ",
        "ja": "{count} 件の記録があります",
    },
    "agent.ok.history_summary": {
        "zh": "汇总:共 {count} 张 · {by_status}",
        "en": "Summary: {count} total · {by_status}",
        "th": "สรุป: ทั้งหมด {count} รายการ · {by_status}",
        "ja": "まとめ:合計 {count} 件 · {by_status}",
    },
    "agent.ok.balance": {
        "zh": "余额 {balance}฿·本月已用 {pages} 页",
        "en": "Credit balance {balance} THB · {pages} pages used this month",
        "th": "เครดิตคงเหลือ {balance} บาท · ใช้ไปเดือนนี้ {pages} หน้า",
        "ja": "クレジット残高 {balance} バーツ · 今月の利用 {pages} ページ",
    },
    "agent.ok.usage_this_month": {
        "zh": "本月已用 {pages} 页",
        "en": "{pages} pages used this month",
        "th": "เดือนนี้ใช้ไป {pages} หน้า",
        "ja": "今月の利用 {pages} ページ",
    },
    "agent.ok.notifications": {
        "zh": "有 {count} 条通知{top_list}",
        "en": "{count} notifications{top_list}",
        "th": "มีแจ้งเตือน {count} รายการ{top_list}",
        "ja": "通知が {count} 件{top_list}",
    },
    # M3 才上线(B 档),键先在场保前后端同源 + 防漏闸:
    "agent.ok.push": {
        "zh": "✅ 已推进 {endpoint}·单号 {bill_no}",
        "en": "✅ Pushed to {endpoint} · doc no. {bill_no}",
        "th": "✅ ส่งเข้า {endpoint} แล้ว · เลขเอกสาร {bill_no}",
        "ja": "✅ {endpoint} へ送信しました · 伝票番号 {bill_no}",
    },
    "agent.ok.push_dup": {
        "zh": "这张已推过 {endpoint}(单号 {bill_no})·不重复推送",
        "en": "This document was already pushed to {endpoint} (no. {bill_no}) · not pushing again",
        "th": "ใบนี้ส่งเข้า {endpoint} ไปแล้ว (เลข {bill_no}) ไม่ส่งซ้ำ",
        "ja": "この伝票は {endpoint} へ送信済みです(番号 {bill_no})· 重複送信しません",
    },
    "agent.ok.recon": {
        "zh": "对账完成·一致 {matched} 笔,不一致 {unmatched}",
        "en": "Reconciliation done · {matched} matched, {unmatched} unmatched",
        "th": "กระทบยอดเสร็จ · ตรงกัน {matched} รายการ ไม่ตรง {unmatched}",
        "ja": "照合完了 · 一致 {matched} 件、不一致 {unmatched} 件",
    },
    # ── 超范围引导(oos) ──
    "agent.oos.app_only": {
        "zh": "这个在 App 里做更方便:{app_link}",
        "en": "This is easier in the app — open {app_link}",
        "th": "เรื่องนี้ทำในแอปจะสะดวกกว่า เปิดที่ {app_link} ได้เลย",
        "ja": "これはアプリの方が便利です。{app_link} を開いてください",
    },
    "agent.oos.security": {
        "zh": "账号/密码相关请到 App,保安全",
        "en": "For account or password matters, please use the app to keep things secure",
        "th": "เรื่องบัญชี/รหัสผ่าน ต้องทำในแอปเพื่อความปลอดภัย",
        "ja": "アカウントやパスワードに関する操作は、安全のためアプリで行ってください",
    },
    "agent.oos.capability": {
        "zh": "我能帮:查识别历史、查余额、推 ERP、对账·说一句试试",
        "en": "I can help with: scan history, credit balance, pushing to ERP, and reconciliation — just type it",
        "th": "ช่วยได้เรื่อง: ดูประวัติสแกน, เช็คยอดเครดิต, ส่งเข้า ERP, กระทบยอด · พิมพ์มาได้เลยค่ะ",
        "ja": "お手伝いできること:スキャン履歴、クレジット残高、ERP への送信、照合 · お気軽にどうぞ",
    },
    # ── 失败(failure)·error_code → 人话 ──
    "agent.failure.insufficient_balance": {
        "zh": "余额不足(剩 {balance}฿)·充值:{topup_link}",
        "en": "Not enough credit ({balance} THB left) · top up at {topup_link}",
        "th": "เครดิตไม่พอ (เหลือ {balance} บาท) · เติมเงินที่ {topup_link}",
        "ja": "クレジットが不足しています(残り {balance} バーツ)· {topup_link} でチャージしてください",
    },
    "agent.failure.no_endpoint": {
        "zh": "还没配 ERP 端点·先去 App 配",
        "en": "No ERP endpoint set up yet · please set one in the app first",
        "th": "ยังไม่ได้ตั้งค่าปลายทาง ERP · ตั้งในแอปก่อนนะคะ",
        "ja": "ERP の送信先がまだ設定されていません · 先にアプリで設定してください",
    },
    "agent.failure.forbidden": {
        "zh": "你暂无此权限·找公司管理员",
        "en": "You do not have access to this · please contact your company admin",
        "th": "สิทธิ์ของคุณยังเข้าถึงเมนูนี้ไม่ได้ · ติดต่อแอดมินของบริษัท",
        "ja": "この操作の権限がありません · 会社の管理者にお問い合わせください",
    },
    "agent.failure.history_not_found": {
        "zh": "找不到那张·重发单号",
        "en": "Cannot find that document · please send the invoice no. again",
        "th": "หาเอกสารใบนั้นไม่เจอ · ลองส่งเลขใบเสร็จอีกครั้ง",
        "ja": "その伝票が見つかりません · 領収書番号をもう一度送ってください",
    },
    "agent.failure.no_tenant": {
        "zh": "还没绑定公司账套·先到 App 开",
        "en": "No company account linked yet · please open the app first",
        "th": "ยังไม่ได้ผูกบัญชีบริษัท · เปิดในแอปก่อนนะ",
        "ja": "会社の帳簿がまだ紐付けられていません · 先にアプリで開いてください",
    },
    "agent.failure.query_failed": {
        "zh": "查询失败,稍后再试",
        "en": "Could not fetch the data · please try again",
        "th": "ดึงข้อมูลไม่สำเร็จ ลองใหม่อีกครั้งนะคะ",
        "ja": "データの取得に失敗しました · もう一度お試しください",
    },
    "agent.failure.not_available_yet": {
        "zh": "这个还不能在对话里做·到 App 操作:{app_link}",
        "en": "This is not available in chat yet · do it in the app: {app_link}",
        "th": "ฟังก์ชันนี้ยังทำผ่านแชทไม่ได้ ทำในแอปได้เลย {app_link}",
        "ja": "これはまだチャットでは利用できません · アプリで操作してください:{app_link}",
    },
    "agent.failure.unknown": {
        "zh": "系统临时问题,稍后再试",
        "en": "Temporary system issue · please try again shortly",
        "th": "ระบบมีปัญหาชั่วคราว ลองใหม่อีกครั้งนะคะ",
        "ja": "システムに一時的な問題が発生しました · 後ほどもう一度お試しください",
    },
    "agent.failure._default": {
        "zh": "系统临时问题,稍后再试",
        "en": "Temporary system issue · please try again shortly",
        "th": "ระบบมีปัญหาชั่วคราว ลองใหม่อีกครั้งนะคะ",
        "ja": "システムに一時的な問題が発生しました · 後ほどもう一度お試しください",
    },
    # ── 闲聊(chat) ──
    "agent.chat.greeting": {
        "zh": "你好,有什么记账的事我能帮忙?",
        "en": "Hi! How can I help with your accounting today?",
        "th": "สวัสดีค่ะ มีอะไรให้ช่วยเรื่องบัญชีไหมคะ",
        "ja": "こんにちは!会計のことで何かお手伝いできますか?",
    },
}


class _SafeDict(dict):
    """str.format_map 兜底:缺槽位 → 空串(不抛 KeyError、不把 {slot} 吐给用户)。"""

    def __missing__(self, key: str) -> str:
        return ""


def _parse(line: str) -> tuple[str, dict[str, str]]:
    """`key|k=v;k2=v2` → (key, slots)。无 `|` 即纯 key。"""
    key, sep, payload = line.partition("|")
    slots: dict[str, str] = {}
    if sep:
        for part in payload.split(";"):
            if not part:
                continue
            name, _, value = part.partition("=")
            slots[name] = value
    return key, slots


def render(line: str, lang: str) -> str:
    """copy_map 占位串 → 用户文案。未登记 key / 渲染异常 → 回退原串(永不抛)。"""
    key, slots = _parse(line or "")
    tmpl = _T.get(key, {}).get(lang) or _T.get(key, {}).get(DEFAULT_LANG)
    if not tmpl:
        return key
    try:
        return tmpl.format_map(_SafeDict(slots))
    except Exception:
        return tmpl


def keys() -> set[str]:
    """已登记的 agent.* key 集合(供前后端同源 contract 测试)。"""
    return set(_T)
