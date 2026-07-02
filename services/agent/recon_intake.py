# -*- coding: utf-8 -*-
"""LINE 收件配对 → 起银行对账异步 job(RECON-3-LINE-PLAN 方案一触发底座 · 2026-07-03)。

用户说"做银行对账"→ 开收件检查点(line_pending_actions·TTL 15min)→ 发对账单
(pdf/图)+ GL 文件(表格类)各≥1 + 报科目号 → 余额预检 → store.enqueue(job 走
现有 embedded worker,与网页同一条产线)→ 完成由 worker 通知钩回推(line_notify)。
收件模式下文件绕过费用 OCR(零识别扣费,对账扣费在 worker 与网页同口径)。
income/tax 触发复用本底座二期。闸 agent_recon_intake 默认关 fail-closed。
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
# GL 侧=表格类扩展名(与 OCR table path 同清单);其余(pdf/图)按对账单收。
_GL_EXTS = {".xlsx", ".xls", ".xlsm", ".csv", ".tsv"}
# 科目号:整句就是编码(可带"科目/บัญชี/GL"前缀)才收——含编码的普通聊天
# (如"看看那张 7-11 的单据")绝不许被吞(对抗用例抓过)。
_ACCOUNT_RE = re.compile(
    r"(?:บัญชี|เลขบัญชี|科目号?|acct\.?|account|gl)?\s*[:：]?\s*(\d[\d\-\.]{1,14})\s*",
    re.IGNORECASE,
)
_MAX_ACCOUNT_TEXT_LEN = 30

_OPEN = {
    "th": (
        "ได้เลยค่ะ ส่งมา 2 อย่างนะคะ: ① สเตทเมนต์ธนาคาร (PDF/รูป) ② ไฟล์ GL (Excel/CSV) · "
        "แล้วพิมพ์เลขบัญชี GL ที่จะกระทบ (เช่น 1010) · พิมพ์ 'ยกเลิก' เพื่อยกเลิกได้ (ภายใน 15 นาที)"
    ),
    "zh": "好,发我两样:①银行对账单(PDF/图片)②GL 总账文件(Excel/CSV)·再告诉我 GL 科目号(比如 1010)。回「取消」可放弃(15 分钟内有效)。",
    "en": (
        "Sure — send me two things: ① the bank statement (PDF/photo) ② the GL file (Excel/CSV), "
        "then type the GL account code (e.g. 1010). Type 'cancel' to abort (valid 15 min)."
    ),
    "ja": "了解です。①銀行明細(PDF/画像)②GL ファイル(Excel/CSV)を送り、GL 科目コード(例 1010)を入力してください。「キャンセル」で中止できます(15分以内)。",
}
_ROLE_NAME = {
    "stmt": {"th": "สเตทเมนต์ธนาคาร", "zh": "银行对账单", "en": "bank statement", "ja": "銀行明細"},
    "gl": {"th": "ไฟล์ GL", "zh": "GL 总账文件", "en": "GL file", "ja": "GL ファイル"},
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
    miss = []
    if not action.get("stmt"):
        miss.append(_t(_ROLE_NAME["stmt"], lang))
    if not action.get("gl"):
        miss.append(_t(_ROLE_NAME["gl"], lang))
    if not action.get("gl_account"):
        miss.append(_t(_ROLE_NAME["account"], lang))
    return " + ".join(miss)


def _ready(action) -> bool:
    return bool(action.get("stmt") and action.get("gl") and action.get("gl_account"))


def _stage_dir(action) -> str:
    from services.recon_jobs import worker

    return worker.stage_dir_for(str(action.get("job_id") or ""))


def _cleanup(action) -> None:
    try:
        if action.get("job_id"):
            shutil.rmtree(_stage_dir(action), ignore_errors=True)
    except Exception:
        logger.warning("[recon_intake] stage cleanup failed", exc_info=True)


def start(user, tid, line_user_id, lang, *, gl_account=None) -> None:
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
    action = {
        "tool": TOOL,
        "kind": "bank",
        "job_id": str(uuid.uuid4()),
        "stmt": 0,
        "gl": 0,
        "files": [],
        "gl_account": account,
        "lang": lang,
    }
    line_pending_actions.set_action(tid, line_user_id, action, ttl_minutes=_TTL_MINUTES)
    _notify(line_user_id, tid, _t(_OPEN, lang))


def handle_file(user, tid, line_user_id, lang, file_bytes, filename, quote_token):
    """收件模式下的文件:按扩展名归 role 落进 job 暂存目录(不进费用 OCR,零识别扣费)。
    返回 True=已收;None=无活跃收件(走正常图片管线)。同步重活——调用方 to_thread。"""
    from services.line_binding import line_pending_actions

    action = line_pending_actions.read_action(tid, line_user_id)
    if not action or action.get("tool") != TOOL:
        return None
    ext = os.path.splitext(filename or "")[1].lower()
    role = "gl" if ext in _GL_EXTS else "stmt"
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
    检查点保留——用户中途问别的不打断收件)。"""
    try:
        from services.line_binding import line_pending_actions

        action = line_pending_actions.read_action(tid, line_user_id)
        if not action or action.get("tool") != TOOL or action.get("gl_account"):
            return False
        t = str(text or "").strip()
        if len(t) > _MAX_ACCOUNT_TEXT_LEN:
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

    ws = wc.default_workspace_for_write(tid)
    params = {
        "user_id": uid,
        "tenant_id": tid,
        "workspace_client_id": ws,
        "is_exempt": bool(bill.get("is_exempt", False)),
        "lang": lang,
        "gl_account": action.get("gl_account") or "",
        "notify": {"line_user_id": line_user_id, "lang": lang},
    }
    input_ref = [
        {"path": f["path"], "filename": f["filename"], "role": f["role"]}
        for f in action.get("files") or []
    ]
    rid = jobs_store.enqueue(
        "bank", uid, tid, params, input_ref, job_id=str(action["job_id"]), workspace_client_id=ws
    )
    if not rid:
        _cleanup(action)
        _notify(line_user_id, tid, _t(_FAILED_START, lang))
        return True
    _notify(line_user_id, tid, _t(_STARTED, lang).format(account=action.get("gl_account") or "-"))
    _note(line_user_id, tid, f"银行对账收件齐,job={str(rid)[:8]} 已入队")
    return True


def cancel(user, tid, line_user_id, lang, action) -> None:
    _cleanup(action or {})
    _notify(line_user_id, tid, _t(_CANCELLED, lang))
    _note(line_user_id, tid, "银行对账收件:用户取消")


def _note(line_user_id, tid, bot_text) -> None:
    from services.line_binding import line_chat_memory

    line_chat_memory.note(line_user_id=line_user_id, tenant_id=tid, role="bot", content=bot_text)
