# -*- coding: utf-8 -*-
"""LINE 收件配对 → 起对账异步 job(RECON-3-LINE-PLAN 触发底座 · 三档 · 2026-07-03)。

用户说"做银行对账/收入对账/核查销项税报告"→ 开收件检查点(line_pending_actions·
TTL 15min)→ 按档收文件对(顺序+文件名记号归 role)→ 余额预检 → store.enqueue
(job 走现有 embedded worker,与网页同一条产线)→ 完成由 worker 通知钩回推
(line_notify)。收件模式下文件绕过费用 OCR(零识别扣费,对账扣费在 worker 与
网页同口径)。闸 agent_recon_intake 默认关 fail-closed。
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import uuid

from core import db

logger = logging.getLogger("mr-pilot")

TOOL = "recon_intake"
_TTL_MINUTES = 15

# 三档收件配置:roles=(第一件, 第二件)顺序即无记号时的归属;asks_account 只有 bank;
# open_go=第二 role 数量开放(tax 发票批可多张),齐了也不自动跑,等用户回"开始"。
_KIND_CFG = {
    "bank": {"job_type": "bank", "roles": ("stmt", "gl"), "asks_account": True, "open_go": False},
    "income": {
        "job_type": "glvat",
        "roles": ("gl", "vat"),
        "asks_account": False,
        "open_go": False,
    },
    "tax": {
        "job_type": "salesvat",
        "roles": ("invoice", "report"),
        "asks_account": False,
        "open_go": True,
    },
}

# role 归属:扩展名两边都不可靠(GL 常是 PDF,对账单也有 Excel·真件夹实证)——
# 文件名记号优先纠偏,其余按顺序收(开场文案按档定死顺序)。
_ROLE_TOKEN_RE = {
    "gl": re.compile(r"gl|ledger|总账|總帳|แยกประเภท", re.IGNORECASE),
    "stmt": re.compile(r"statement|stmt|สเตทเมนต์|เดินบัญชี|对账单", re.IGNORECASE),
    "vat": re.compile(r"ภ\.?พ\.?\s*30|vat|ภาษีขาย|销项|報告|报告|report", re.IGNORECASE),
    "invoice": re.compile(r"invoice|ใบกำกับ|发票|インボイス", re.IGNORECASE),
    "report": re.compile(r"ภ\.?พ\.?\s*30|ภาษีขาย|销项|報告|报告|report", re.IGNORECASE),
}


def _cfg(action) -> dict:
    return _KIND_CFG.get(str(action.get("kind") or "bank"), _KIND_CFG["bank"])


def _role_for(action, filename) -> str:
    name = str(filename or "")
    r1, r2 = _cfg(action)["roles"]
    # 记号纠偏:第二 role 记号优先(报告/GL 类名字更有辨识度),再看第一 role 记号。
    if _ROLE_TOKEN_RE[r2].search(name):
        return r2
    if _ROLE_TOKEN_RE[r1].search(name):
        return r1
    if not action.get(r1):
        return r1
    if not action.get(r2):
        return r2
    return r1  # 都齐还发 → 当补充第一 role(多页流水/多张发票最常见)


# 科目号:整句就是编码(可带"科目/บัญชี/GL"前缀)才收——含编码的普通聊天
# (如"看看那张 7-11 的单据")绝不许被吞(对抗用例抓过)。
_ACCOUNT_RE = re.compile(
    r"(?:บัญชี|เลขบัญชี|科目号?|acct\.?|account|gl)?\s*[:：]?\s*(\d[\d\-\.]{1,14})\s*",
    re.IGNORECASE,
)
_MAX_ACCOUNT_TEXT_LEN = 30
# 文件齐后不想指定科目号 → 回"开始"直接跑(产品口径:parse_gl 的 account_code 允许空=全量)。
_GO_WORDS = frozenset({"开始", "開始", "跑吧", "เริ่ม", "เริ่มเลย", "start", "go", "run"})

_OPEN = {
    "bank": {
        "th": (
            "ได้เลยค่ะ ส่งมาตามลำดับนะคะ: ① สเตทเมนต์ธนาคารก่อน ② แล้วค่อยไฟล์ GL · "
            "จากนั้นพิมพ์เลขบัญชี GL (เช่น 1010) · พิมพ์ 'ยกเลิก' เพื่อยกเลิกได้ (ภายใน 15 นาที)"
        ),
        "zh": "好,按顺序发我两样:①先发银行对账单 ②再发 GL 总账文件·然后告诉我 GL 科目号(比如 1010)。回「取消」可放弃(15 分钟内有效)。",
        "en": (
            "Sure — send them in order: ① the bank statement first ② then the GL file, "
            "then type the GL account code (e.g. 1010). Type 'cancel' to abort (valid 15 min)."
        ),
        "ja": "了解です。順番に:①先に銀行明細 ②次に GL ファイルを送り、GL 科目コード(例 1010)を入力してください。「キャンセル」で中止できます(15分以内)。",
    },
    "income": {
        "th": (
            "ได้เลยค่ะ ส่งมาตามลำดับนะคะ: ① ไฟล์ GL ก่อน ② แล้วค่อยรายงานภาษีขาย (ภ.พ.30) · "
            "ครบแล้วระบบกระทบให้เลย · พิมพ์ 'ยกเลิก' เพื่อยกเลิกได้ (ภายใน 15 นาที)"
        ),
        "zh": "好,按顺序发我两样:①先发 GL 总账文件 ②再发销项税报告(ภ.พ.30)·收齐就自动开跑。回「取消」可放弃(15 分钟内有效)。",
        "en": (
            "Sure — send them in order: ① the GL file first ② then the sales-VAT report; "
            "it runs automatically once both arrive. Type 'cancel' to abort (valid 15 min)."
        ),
        "ja": "了解です。順番に:①先に GL ファイル ②次に売上VAT報告書を送ってください。揃い次第自動で実行します。「キャンセル」で中止できます(15分以内)。",
    },
    "tax": {
        "th": (
            "ได้เลยค่ะ ส่งใบกำกับขายมาได้เลย (หลายใบได้) แล้วส่งรายงานภาษีขาย (ภ.พ.30) · "
            "ส่งครบแล้วพิมพ์ 'เริ่ม' · พิมพ์ 'ยกเลิก' เพื่อยกเลิกได้ (ภายใน 15 นาที)"
        ),
        "zh": "好,把销项发票发给我(可多张),再发销项税报告(ภ.พ.30)·都发完回「开始」。回「取消」可放弃(15 分钟内有效)。",
        "en": (
            "Sure — send the sales invoices (multiple OK), then the sales-VAT report. "
            "When everything's sent, type 'start'. Type 'cancel' to abort (valid 15 min)."
        ),
        "ja": "了解です。売上インボイス(複数可)と売上VAT報告書を送り、送り終えたら「開始」と入力してください。「キャンセル」で中止できます(15分以内)。",
    },
}
_ROLE_NAME = {
    "stmt": {"th": "สเตทเมนต์ธนาคาร", "zh": "银行对账单", "en": "bank statement", "ja": "銀行明細"},
    "gl": {"th": "ไฟล์ GL", "zh": "GL 总账文件", "en": "GL file", "ja": "GL ファイル"},
    "vat": {
        "th": "รายงานภาษีขาย",
        "zh": "销项税报告",
        "en": "sales-VAT report",
        "ja": "売上VAT報告書",
    },
    "invoice": {
        "th": "ใบกำกับขาย",
        "zh": "销项发票",
        "en": "sales invoice",
        "ja": "売上インボイス",
    },
    "report": {
        "th": "รายงานภาษีขาย",
        "zh": "销项税报告",
        "en": "sales-VAT report",
        "ja": "売上VAT報告書",
    },
    "account": {
        "th": "เลขบัญชี GL",
        "zh": "GL 科目号",
        "en": "GL account code",
        "ja": "GL 科目コード",
    },
}
_GOT = {
    "th": "รับ{role}แล้วค่ะ ยังขาด: {missing}",
    "zh": "收到{role},还差:{missing}",
    "en": "Got the {role}. Still missing: {missing}",
    "ja": "{role}を受け取りました。残り:{missing}",
}
_FILES_READY = {
    "th": "ไฟล์ครบแล้วค่ะ พิมพ์เลขบัญชี GL (เช่น 1010) หรือพิมพ์ 'เริ่ม' เพื่อกระทบทั้งหมดเลย",
    "zh": "文件齐了——回 GL 科目号(如 1010),或回「开始」不指定直接跑。",
    "en": "Files complete — type the GL account code (e.g. 1010), or type 'start' to run without one.",
    "ja": "ファイルが揃いました。GL 科目コード(例 1010)を入力するか、「開始」で指定なしで実行します。",
}
_TAX_READY = {
    "th": "รับรายงานแล้วค่ะ มีใบกำกับอีกก็ส่งต่อได้เลย ครบแล้วพิมพ์ 'เริ่ม' นะคะ",
    "zh": "报告收到了——还有发票就继续发,发完回「开始」。",
    "en": "Report received — keep sending invoices if there are more, then type 'start'.",
    "ja": "報告書を受け取りました。インボイスが他にあれば続けて送り、終わったら「開始」と入力してください。",
}
_GOT_ACCOUNT = {
    "th": "รับเลขบัญชี {account} แล้วค่ะ ยังขาด: {missing}",
    "zh": "记下科目号 {account},还差:{missing}",
    "en": "Noted account {account}. Still missing: {missing}",
    "ja": "科目 {account} を記録しました。残り:{missing}",
}
_STARTED = {
    "th": "⏳ เริ่มกระทบยอดแล้วค่ะ (บัญชี {account}) เสร็จแล้วจะแจ้งทันที · ระหว่างนี้ถามอย่างอื่นได้เลย",
    "zh": "⏳ 对账跑起来了(科目 {account}),好了我马上告诉你·期间可以随时问别的。",
    "en": "⏳ Reconciliation started (account {account}) — I'll ping you when it's done.",
    "ja": "⏳ 照合を開始しました(科目 {account})。完了したらお知らせします。",
}
_STARTED_PLAIN = {
    "th": "⏳ เริ่มกระทบยอดแล้วค่ะ เสร็จแล้วจะแจ้งทันที · ระหว่างนี้ถามอย่างอื่นได้เลย",
    "zh": "⏳ 对账跑起来了,好了我马上告诉你·期间可以随时问别的。",
    "en": "⏳ Reconciliation started — I'll ping you when it's done.",
    "ja": "⏳ 照合を開始しました。完了したらお知らせします。",
}
_NO_BALANCE = {
    "th": "ยอดเงินคงเหลือไม่พอสำหรับกระทบยอดค่ะ เติมเงินบนเว็บก่อนนะคะ (ไฟล์ที่ส่งมายังไม่คิดเงิน)",
    "zh": "余额不足,暂时跑不了对账,请先到网页充值(刚发的文件没有扣费)。",
    "en": "Insufficient balance for reconciliation — please top up on the web first (no charge for the files sent).",
    "ja": "残高不足のため照合できません。ウェブでチャージしてください(送信済みファイルは課金されていません)。",
}
_FAILED_START = {
    "th": "สร้างงานกระทบยอดไม่สำเร็จค่ะ ลองใหม่หรือทำบนเว็บก่อนนะคะ",
    "zh": "对账任务没建起来,请稍后再试或先在网页跑。",
    "en": "Couldn't create the reconciliation job — try again or run it on the web.",
    "ja": "照合ジョブを作成できませんでした。後で再試行するかウェブでお試しください。",
}
_CANCELLED = {
    "th": "ยกเลิกแล้วค่ะ ไฟล์ที่ส่งมาถูกทิ้งแล้ว ไม่คิดเงินนะคะ",
    "zh": "已取消,收到的文件已丢弃,没有扣费。",
    "en": "Cancelled — the received files were discarded, nothing charged.",
    "ja": "キャンセルしました。受信ファイルは破棄済み、課金はありません。",
}


def _t(table: dict, lang: str) -> str:
    return table.get(lang, table["en"])


def _notify(line_user_id, tid, text, quote_token=None) -> None:
    from services.line_binding import line_reply

    line_reply.push_text_context(line_user_id, text, quote_token=quote_token or "", tenant_id=tid)


def _missing_names(action, lang) -> str:
    cfg = _cfg(action)
    miss = [_t(_ROLE_NAME[r], lang) for r in cfg["roles"] if not action.get(r)]
    if cfg["asks_account"] and not action.get("gl_account"):
        miss.append(_t(_ROLE_NAME["account"], lang))
    return " + ".join(miss)


def _files_ready(action) -> bool:
    return all(action.get(r) for r in _cfg(action)["roles"])


def _ready(action) -> bool:
    """自动起跑条件:文件齐 + 科目条件;tax 数量开放永不自动(等"开始")。"""
    if _cfg(action)["open_go"]:
        return False
    return _files_ready(action) and _account_ok(action)


def _account_ok(action) -> bool:
    return (not _cfg(action)["asks_account"]) or bool(action.get("gl_account"))


def _stage_dir(action) -> str:
    from services.recon_jobs import worker

    return worker.stage_dir_for(str(action.get("job_id") or ""))


def _cleanup(action) -> None:
    try:
        if action.get("job_id"):
            shutil.rmtree(_stage_dir(action), ignore_errors=True)
    except Exception:
        logger.warning("[recon_intake] stage cleanup failed", exc_info=True)


def start(user, tid, line_user_id, lang, *, kind="bank", gl_account=None) -> None:
    """开收件:预生成 job_id(暂存目录=最终 job 目录,凑齐即入队零搬运);
    旧收件(若有)连目录一起废掉——新意图为准。"""
    from services.line_binding import line_pending_actions

    old = line_pending_actions.read_action(tid, line_user_id)
    if old and old.get("tool") == TOOL:
        _cleanup(old)
    account = None
    m = _ACCOUNT_RE.search(str(gl_account or ""))
    if m:
        account = m.group(1)
    kind = str(kind or "bank").strip().lower()
    if kind not in _KIND_CFG:
        kind = "bank"
    r1, r2 = _KIND_CFG[kind]["roles"]
    action = {
        "tool": TOOL,
        "kind": kind,
        "job_id": str(uuid.uuid4()),
        r1: 0,
        r2: 0,
        "files": [],
        "gl_account": account,
        "lang": lang,
    }
    line_pending_actions.set_action(tid, line_user_id, action, ttl_minutes=_TTL_MINUTES)
    _notify(line_user_id, tid, _t(_OPEN[kind], lang))


def handle_file(user, tid, line_user_id, lang, file_bytes, filename, quote_token):
    """收件模式下的文件:归 role 落进 job 暂存目录(不进费用 OCR,零识别扣费)。
    返回 True=已收;None=无活跃收件(走正常图片管线)。同步重活——调用方 to_thread。"""
    from services.line_binding import line_pending_actions

    action = line_pending_actions.read_action(tid, line_user_id)
    if not action or action.get("tool") != TOOL:
        return None
    role = _role_for(action, filename)
    stage = _stage_dir(action)
    os.makedirs(stage, exist_ok=True)
    base = os.path.basename(filename or f"{role}.bin")
    path = os.path.join(stage, f"{role}_{int(action.get(role) or 0)}_{base}")
    with open(path, "wb") as f:
        f.write(file_bytes)
    action[role] = int(action.get(role) or 0) + 1
    action["files"] = list(action.get("files") or []) + [
        {"path": path, "filename": base, "role": role}
    ]
    if _ready(action):
        return _launch(user, tid, line_user_id, lang, action)
    line_pending_actions.set_action(tid, line_user_id, action, ttl_minutes=_TTL_MINUTES)
    if _files_ready(action):
        # bank=只差科目号(可选,回编码或开始);tax=数量开放(继续发或回开始)
        table = _FILES_READY if _cfg(action)["asks_account"] else _TAX_READY
        _notify(line_user_id, tid, _t(table, lang), quote_token)
    else:
        _notify(
            line_user_id,
            tid,
            _t(_GOT, lang).format(
                role=_t(_ROLE_NAME[role], lang), missing=_missing_names(action, lang)
            ),
            quote_token,
        )
    return True


def try_text(user, text, lang, tid, line_user_id) -> bool:
    """收件模式下的文本:短消息里的编码记号 → 科目号。别的话一律不吃(交正常轮,
    检查点保留——用户中途问别的不打断收件)。

    挂在每条文本必经处 → 零成本预过滤(长度/词形)和闸检查都排在 DB 读之前:
    普通聊天、闸关时零查询(/simplify 效率雷 2026-07-03)。"""
    try:
        t = str(text or "").strip()
        if len(t) > _MAX_ACCOUNT_TEXT_LEN:
            return False
        is_go = t.lower() in _GO_WORDS
        if not is_go and not _ACCOUNT_RE.fullmatch(t):
            return False
        from core import feature_flags

        if not feature_flags.agent_recon_intake_enabled_for(str((user or {}).get("id") or "")):
            return False
        from services.line_binding import line_pending_actions

        action = line_pending_actions.read_action(tid, line_user_id)
        if not action or action.get("tool") != TOOL:
            return False
        if is_go and _files_ready(action):
            # bank 的"开始"=不指定科目(空=全量);income/tax 的"开始"=收件完毕起跑
            if _cfg(action)["asks_account"] and not action.get("gl_account"):
                action["gl_account"] = ""
            return bool(_launch(user, tid, line_user_id, lang, action))
        # 编码只有 bank 档收(income/tax 无科目号概念,数字消息交正常轮)
        if not _cfg(action)["asks_account"] or action.get("gl_account"):
            return False
        m = _ACCOUNT_RE.fullmatch(t)
        if not m:
            return False
        action["gl_account"] = m.group(1)
        if _ready(action):
            return bool(_launch(user, tid, line_user_id, lang, action))
        line_pending_actions.set_action(tid, line_user_id, action, ttl_minutes=_TTL_MINUTES)
        _notify(
            line_user_id,
            tid,
            _t(_GOT_ACCOUNT, lang).format(
                account=action["gl_account"], missing=_missing_names(action, lang)
            ),
        )
        return True
    except Exception:
        logger.warning("[recon_intake] try_text failed; normal turn", exc_info=True)
        return False


def _launch(user, tid, line_user_id, lang, action) -> bool:
    """凑齐即跑:余额预检 → enqueue(与网页 submit 同 params 口径 + notify 回推目标)。"""
    from services.line_binding import line_pending_actions
    from services.recon_jobs import store as jobs_store

    line_pending_actions.take_action(tid, line_user_id)  # 消费检查点(单发单用)
    uid = str(user["id"])
    try:
        bill = db.get_billing_status_combined(uid, tid)
    except Exception:
        bill = {"allowed": True, "is_exempt": False}  # 余额闸基建抖动容错放行(与热路径一致)
    if not bill.get("allowed") and not bill.get("is_exempt"):
        _cleanup(action)
        _notify(line_user_id, tid, _t(_NO_BALANCE, lang))
        return True
    from core import workspace_context as wc

    cfg = _cfg(action)
    ws = wc.default_workspace_for_write(tid)
    params = {
        "user_id": uid,
        "tenant_id": tid,
        "workspace_client_id": ws,
        "is_exempt": bool(bill.get("is_exempt", False)),
        "lang": lang,
        "notify": {"line_user_id": line_user_id, "lang": lang},
    }
    if cfg["job_type"] == "bank":
        params["gl_account"] = action.get("gl_account") or ""
    elif cfg["job_type"] == "glvat":
        params["revenue_prefix"] = "4"  # 收入科目前缀,与网页 submit 默认一致
    input_ref = [
        {"path": f["path"], "filename": f["filename"], "role": f["role"]}
        for f in action.get("files") or []
    ]
    rid = jobs_store.enqueue(
        cfg["job_type"],
        uid,
        tid,
        params,
        input_ref,
        job_id=str(action["job_id"]),
        workspace_client_id=ws,
    )
    if not rid:
        _cleanup(action)
        _notify(line_user_id, tid, _t(_FAILED_START, lang))
        return True
    if cfg["asks_account"]:
        _notify(
            line_user_id, tid, _t(_STARTED, lang).format(account=action.get("gl_account") or "-")
        )
    else:
        _notify(line_user_id, tid, _t(_STARTED_PLAIN, lang))
    _note(line_user_id, tid, f"对账收件齐({action.get('kind')}),job={str(rid)[:8]} 已入队")
    return True


def cancel(user, tid, line_user_id, lang, action) -> None:
    _cleanup(action or {})
    _notify(line_user_id, tid, _t(_CANCELLED, lang))
    _note(line_user_id, tid, "对账收件:用户取消")


def _note(line_user_id, tid, bot_text) -> None:
    from services.line_binding import line_chat_memory

    line_chat_memory.note(line_user_id=line_user_id, tenant_id=tid, role="bot", content=bot_text)
