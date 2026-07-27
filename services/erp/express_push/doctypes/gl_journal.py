# -*- coding: utf-8 -*-
"""手工总账凭证 Manual GL Voucher(บันทึกรายการบัญชี)· GLJNL.SRCJNL='GL  ' 载荷组装。

契约源:docs/integrations/express-push/45-doctype-write-contract.md(真账套镜像 3284 张
手工凭证 / 16981 行逐条复核)。桥端照本模块的 docstring 消费。

四类里唯一**云端能把分录算完**的:手工凭证本身就是 GL,科目由会计在录入台逐行选,不需要
去目标账套查 ARMAS/APMAS/ISRUN 推科目。所以这里产 `lines`,且借贷用 **Decimal 严格相等**
零容差 —— 镜像 3284 张真凭证 0 违反,放容差只会放过录入笔误。

它也是唯一「只写 2 张表」的单据(GLJNL + GLJNLIT [+ ISVAT]),APTRN/ARTRN/APBAL/ARBAL/
STTRN/ISRUN 一张不碰 —— 这正是桥端最强的反向闸。

载荷契约(**键名以桥端 `writepath/doc_journal.py` 实际读取的为准**,机械对镜见
services/erp/express_push/bridge_contract.py):
  direction      "gl_journal"(云端桥门面按它分派)
  doc_type       "gl_journal"(桥端 write_jobs 的路由键 · 显式给,不靠 direction 兜底)
  doctype        "GL"(= GLJNL.SRCJNL 常量标记 · 手工凭证唯一判别式,推单据时该列必须留空)
  account_set    账套名
  voucher_date   公历 ISO 凭证日(→ GLJNL.VOUDAT,且逐行 GLJNLIT.VOUDAT 同值)
  journal_code   选哪本账 = ISRUN[DOCTYP='GL'].**DOCCOD**('00' 一般/'01' 付款/'02' 收款/
                 '03' 销售/'04' 采购/'05'+ 各账套自建)。⚠️ 读 DOCCOD 不读 JNLTYP —— GL 行的
                 JNLTYP 列是空的(45 号契约 X7)。必须是目标账套 ISRUN 里真实存在的值,桥端再校一次
  voucher_no     可选 · 不给则桥端按 ISRUN[GL,DOCCOD].PREFIX + 佛历YYMM + 序号生成。
                 凭证号没有机器计数器可抢锁,唯一性由写入方保证:桥端只在**活行**里查重
                 (软删行的号仍算"用过",但拿它判"已存在"会误拒 —— 6902ASC 有 3753 个复用号)
  description    → GLJNL.DESCRP · C(50) 按 cp874 字节截断(泰文词间空格建议 NBSP 0xA0)
  total_amount   Σ 借方(= Σ 贷方)· 给复核台/推送日志显示金额用,桥端不据此落库
  lines[]        [{account, side(D/C), amount, depcod, jobcod}] · ≥2 行 ·
                 amount 恒正(方向只由 side→TRNTYP 表达,负数进 Express 会被当反方向记)
  vat            可选(带税凭证 · 6902ASC 16.6% 才写):{vat_rec('P'|'S'), vat_period(公历
                 ISO · 桥端取它的年月落 ISVAT.VATPRD 月首), ref_no, base_amount, vat_amount,
                 tax_id, prename, depcod}。ISVAT 的 VATTYP/RECTYP/LATE/SELF_ADDED 一律留空
                 —— 那正是它与单据产生的 VAT 行的区分点

**行级只发桥端真的会落盘的那几列**:GLJNLIT.DESCRP 由桥端统一抄单头摘要(doc_common
`write_journal` 逐腿写 `descrp[:50]`),行级 phase/coscod 桥端的 `Leg` 里根本没有位置。
发了不报错,是会计在录入台逐行敲的摘要与维度**静默蒸发** —— 比报错难查,所以不发。
真要做行级摘要,得先在桥端 `Leg` 上开列并发桥新版,不是云端多塞一个键。
  userid         → GLJNL.CREBY/USERID · C(8)
  source         留痕 {ref, note}

桥端还要做而云端做不到的三道闸(科目/账本合法性只有目标账套知道):
  A11 journal_code ∈ ISRUN[DOCTYP='GL'].DOCCOD
  A13 每个 acc 在 GLACC 里且 ACCTYP='0' ∧ STATUS='A' ∧ 不是任何账户的 PARENT
  A14 (ACCNUM, DEPCOD, JOBCOD) ∈ GLBAL 主键集
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from services.erp.express_push.common import ExpressMapResult, fail, finalize_payload
from services.erp.express_push.doctypes import base

DIRECTION = "gl_journal"
DOCTYPE = "GL"

VAT_RECS = ("P", "S")  # 进项 / 销项

_MIN_LINES = 2
_MAX_VOUCHER = 12  # GLJNL.VOUCHER C(12)
_MAX_JOURNAL_CODE = 2  # ISRUN.DOCCOD C(2)
_MAX_DESCRP = 50  # GLJNL.DESCRP / GLJNLIT.DESCRP C(50)
_MAX_ACCNUM = 15  # GLJNLIT.ACCNUM C(15)
_MAX_USERID = 8
_MAX_REFNUM = 15  # ISVAT.REFNUM

# 桥端 `doc_common.Leg` 认得的行级维度(手工凭证 16975/16981 全空 —— 给上就带,
# 不给不发空键)。桥端拿 (account, depcod, jobcod) 撞 GLBAL 主键集做 A14,少发一个
# 就成了"验一把钥匙、开另一把锁"。
_LINE_DIMS = (("depcod", 4), ("jobcod", 6))


def build_journal_payload(req: Dict[str, Any], *, config: Dict[str, Any]) -> ExpressMapResult:
    """录入台表单 → 手工凭证载荷。借贷不平 / 科目形状不对 → ok=False + reason。"""
    account_set = str((config or {}).get("account_set") or "").strip()
    if not account_set:
        return fail("no_account_set")
    req = req or {}

    voucher_date = base.iso_docdate(req.get("voucher_date"))
    if not voucher_date:
        return fail("bad_or_missing_date")

    journal_code = str(req.get("journal_code") or "").strip().upper()
    if not journal_code or not journal_code.isalnum():
        return fail("no_journal_code")
    if base.width_error("journal_code", journal_code, _MAX_JOURNAL_CODE):
        return fail("journal_code_too_long")

    voucher_no = str(req.get("voucher_no") or "").strip()
    if voucher_no and base.width_error("voucher_no", voucher_no, _MAX_VOUCHER):
        return fail("voucher_no_too_long")

    description = base.cp874_trim(req.get("description"), _MAX_DESCRP)
    if not description:
        # 真数据 3284/3284 头行 DESCRP 非空:凭证摘要是会计事后唯一能认出这张单的线索。
        return fail("no_description")

    norm_lines, bad = _normalize_lines(base.clean_rows(req.get("lines")))
    if bad:
        return fail(bad)

    vat, bad = _normalize_vat(req.get("vat"))
    if bad:
        return fail(bad)

    payload: Dict[str, Any] = {
        "direction": DIRECTION,
        "doc_type": DIRECTION,
        "doctype": DOCTYPE,
        "account_set": account_set,
        "voucher_date": voucher_date,
        "journal_code": journal_code,
        "description": description,
        "total_amount": base.money_str(_debit_total(norm_lines)),
        "lines": norm_lines,
        "userid": base.cp874_trim(req.get("userid"), _MAX_USERID),
        "source": {"ref": str(req.get("ref") or ""), "note": str(req.get("note") or "")},
    }
    if voucher_no:
        payload["voucher_no"] = voucher_no
    if vat:
        payload["vat"] = vat

    if check_payload(payload):
        return fail("journal_entry_not_balanced")
    return ExpressMapResult(True, finalize_payload(payload), "ok")


def _normalize_lines(rows: List[Dict[str, Any]]) -> tuple:
    err = base.lines_error(rows, min_lines=_MIN_LINES, positive=True)
    if err:
        return [], "bad_journal_lines"
    out: List[Dict[str, str]] = []
    for row in rows:
        account = str(row.get(base.ACCOUNT_KEY) or "").strip()
        if base.width_error(base.ACCOUNT_KEY, account, _MAX_ACCNUM):
            return [], "account_code_too_long"
        line: Dict[str, str] = {
            base.ACCOUNT_KEY: account,
            "side": row.get("side"),
            "amount": base.money_str(base.money(row.get("amount"))),
        }
        for key, width in _LINE_DIMS:
            value = str(row.get(key) or "").strip()
            if value:
                if base.width_error(key, value, width):
                    return [], f"bad_line_{key}"
                line[key] = value
        out.append(line)
    return out, ""


def _normalize_vat(raw: Any) -> tuple:
    if raw is None or raw == {}:
        return None, ""
    if not isinstance(raw, dict):
        return None, "bad_vat_block"
    vat_rec = str(raw.get("vat_rec") or "").strip().upper()
    if vat_rec not in VAT_RECS:
        return None, "bad_vat_rec"
    # 税期发公历 ISO,不发佛历 YYMM01:桥端 `_write_isvat` 拿 `iso_date(vat.vat_period)`
    # 取年月落 VATPRD 月首,佛历串在那儿解不出 → 静默回落成凭证日期,一张补记进上月的
    # 带税凭证会被算进本月税表,而两边都不报错。
    vat_period = base.iso_docdate(raw.get("vat_period") or raw.get("vat_date"))
    if not vat_period:
        return None, "bad_vat_period"
    taxable = base.money(raw.get("base_amount"))
    amount = base.money(raw.get("vat_amount"))
    if taxable is None or amount is None or taxable <= base.ZERO or amount < base.ZERO:
        return None, "bad_vat_amount"
    return {
        "vat_rec": vat_rec,
        "vat_period": vat_period,
        "ref_no": base.cp874_trim(raw.get("ref_no"), _MAX_REFNUM),
        "base_amount": base.money_str(taxable),
        "vat_amount": base.money_str(amount),
        "tax_id": str(raw.get("tax_id") or "").strip()[:13],
        "prename": base.cp874_trim(raw.get("prename"), 12),
        "depcod": str(raw.get("depcod") or "").strip()[:4],
    }, ""


def _debit_total(lines: List[Dict[str, str]]) -> Decimal:
    return base.sum_rows([ln for ln in lines if ln.get("side") == base.SIDE_DEBIT])


_REQUIRED = ("account_set", "voucher_date", "journal_code", "description", "total_amount", "lines")


def check_payload(payload: Dict[str, Any]) -> Optional[str]:
    """写路总闸(桥门面 build_write_payload 调用)· 返回错误文案或 None。"""
    err = base.required_error(payload, _REQUIRED) or base.money_fields_error(
        payload, ("total_amount",)
    )
    if err:
        return err
    err = base.docdate_error(payload, "voucher_date")
    if err:
        return err
    code = str(payload.get("journal_code") or "")
    if not code.isalnum() or base.cp874_len(code) > _MAX_JOURNAL_CODE:
        return f"journal_code 形状非法(ISRUN DOCCOD): {code!r}"
    voucher_no = str(payload.get("voucher_no") or "")
    if voucher_no:
        err = base.width_error("voucher_no", voucher_no, _MAX_VOUCHER)
        if err:
            return err
    # 严格零容差:手工凭证的钱是会计一行行敲的,不是 double 读回来的。
    err = base.lines_error(payload.get("lines"), min_lines=_MIN_LINES, positive=True)
    if err:
        return err
    total = base.money(payload["total_amount"])
    if not base.same(total, _debit_total(payload["lines"])):
        return f"total_amount({total}) != Σ借方({_debit_total(payload['lines'])})"
    return _check_vat(payload.get("vat"))


def _check_vat(raw: Any) -> Optional[str]:
    if not raw:
        return None
    if not isinstance(raw, dict):
        return "vat 须为对象"
    if str(raw.get("vat_rec") or "") not in VAT_RECS:
        return f"vat.vat_rec 须为 {VAT_RECS}: {raw.get('vat_rec')!r}"
    err = base.docdate_error(raw, "vat_period")
    if err:
        return err
    if base.money(raw.get("base_amount")) is None or base.money(raw.get("vat_amount")) is None:
        return "vat 金额解析不了"
    return None
