# -*- coding: utf-8 -*-
"""库存调整 · 内部领用与报损(ปรับปรุงสินค้า)· STTRN.POSOPR='6' 载荷组装。

契约源:docs/integrations/express-push/45-doctype-write-contract.md(真账套镜像 193 张
OU/ZZ 单逐条复核)。桥端照本模块的 docstring 消费。

**这里不产 lines(复式分录)**——存货侧科目要走 ISACC[('S', STMAS[STKCOD].ACCCOD)].ACCNUM01
逐商品解出,对方侧科目默认取 ISRUN[该前缀].ACCNUM01,两者都只有目标账套知道。更要紧的是
**这单该不该有凭证也由账套决定**:`ISINFO.ISPERPETUA=='Y'`(永续盘存)才建 GL,'N' 的账套
(目标生产账套 6902ASC 正是 'N')只写库存三表 —— 云端替它建分录就是凭空造账。

🛑 方向由单头 POSOPR 定,不看金额符号(45 号契约 X1,本轮最重要的一条纠错):OU/ZZ 出库行
的 TRNVAL **存正数**,193/193 张真单是 `Dr 对方科目(费用) / Cr 存货科目`。按"NET>0 → 借存货"
写会 100% 写反成凭空造存货。所以载荷里的 qty/amount 一律为正,方向由 posopr 表达。

载荷契约(**键名以桥端 `writepath/doc_stock_adjust.py` 实际读取的为准**,机械对镜见
services/erp/express_push/bridge_contract.py):
  direction      "stock_adjust"(云端桥门面按它分派)
  doc_type       "stock_adjust"(桥端 write_jobs 的路由键 · 显式给,不靠 direction 兜底)
  doctype        "OU"(ISRUN DOCTYP='OU' 族 · 具体单别看 isrun_prefix)
  subtype        "internal_issue"(v1 唯一受理的子类 · JU/TK 数量调整 8、CA 成本调整 5、
                 RL 调拨 4 一律 escalate:生产账套零样本,无从对标)
  account_set    账套名
  doc_date       公历 ISO 调整日(→ STTRN.DOCDAT,行同值)
  isrun_prefix   该账套 ISRUN DOCTYP='OU' 下的某个 PREFIX(ZZ 报损 / XS / PM …)。各账套自建,
                 69SINCER 有 22 个、69ASIAMI 26 个,**不能硬编码**;桥端再校一次存在性
  loccod         仓库码 C(4) · 可空(桥端回落 ISINFO.MAINLOC,全库实测均 '01')
  remark         → STTRN.REMARK C(50),同时进 STCRD.STKDES(调整单的 STKDES 是摘要不是品名)
  offset_account 对方科目(→ STTRN.ACCNUMDR,借方)· 可空则桥端取 ISRUN[前缀].ACCNUM01;
                 两处都空 → 桥端拒写不猜(ACCNUMCR 对 POSOPR='6' 恒留空)
  lines[]        [{stock_code, qty, unit, tfactor, unit_price, amount, source_lot}]
                 qty/tfactor/unit_price 字符串保四位小数(B(8,4)),amount 保两位(钱)。
                 qty 恒正(录入单位);桥端落 TRNQTY=qty、XTRNQTY=qty×TFACTOR ——
                 **库存余额靠 XTRNQTY 移动**,TFACTOR 实测到 12/50/100,按 TRNQTY 加减差几十倍
                 source_lot → MLOTNUM · 可空则桥端按账套 COSMTD 选批;选不出 escalate。
                 减少行的 MLOTNUM 必须指向真实来源批,写错不报错、几个月后成本全歪(P0-3)
  userid / depcod
  prior_docnum   重推防重单(沿用现役闸)
  source         留痕 {ref, note}

单价必填(契约里 STMAS 均价兜底口径不在 v1):报损/领用金额直接进费用科目,会计在录入台
点"推送"前必须看得见金额;"推完才知道多少钱"对这类单不可接受。

POSOPR/NET 不下发:POSOPR 由 subtype 定死(桥端对 internal_issue 恒写 '6'),NET 由桥端
按每行 XTRNQTY × 单位成本自己算(|NET|>0.005 且账套永续时才建 GLJNL/GLJNLIT 恒 2 行)。
两个都是桥端说了算的值,云端跟着发一份只会在两边算法出现分歧时把错数写进 STTRN.TRNVAL,
而且它俩本就不在桥端载荷白名单里 —— 发了整单当场 bad_payload。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from services.erp.express_push.common import ExpressMapResult, fail, finalize_payload
from services.erp.express_push.doctypes import base

DIRECTION = "stock_adjust"
DOCTYPE = "OU"

SUBTYPE_INTERNAL_ISSUE = "internal_issue"
# 留字段不留实现:载荷带这几个子类一律 escalate(生产 2569 三套 0 张样本,无从对标)。
_UNSUPPORTED_SUBTYPES = ("quantity", "cost", "relocate")

_MAX_STOCK_CODE = 20  # STMAS.STKCOD C(20)
_MAX_LOCCOD = 4  # STTRN.LOCCOD C(4)
_MAX_REMARK = 50  # STTRN.REMARK C(50)
_MAX_ACCNUM = 15  # STTRN.ACCNUMDR C(15)
_MAX_PREFIX = 2  # ISRUN.PREFIX C(2)
_MAX_LOT = 24  # STCRD.MLOTNUM C(24)
_MAX_UNIT = 2  # STCRD.TQUCOD C(2)
_MAX_USERID = 8


def build_stock_adjust_payload(req: Dict[str, Any], *, config: Dict[str, Any]) -> ExpressMapResult:
    """录入台表单 → 库存调整单载荷。子类不受理 / 数量金额不正 → ok=False + reason。"""
    account_set = str((config or {}).get("account_set") or "").strip()
    if not account_set:
        return fail("no_account_set")
    req = req or {}

    subtype = str(req.get("subtype") or SUBTYPE_INTERNAL_ISSUE).strip().lower()
    if subtype in _UNSUPPORTED_SUBTYPES:
        return fail("stock_adjust_subtype_unsupported")
    if subtype != SUBTYPE_INTERNAL_ISSUE:
        return fail("bad_stock_adjust_subtype")

    doc_date = base.iso_docdate(req.get("doc_date"))
    if not doc_date:
        return fail("bad_or_missing_date")

    prefix = str(req.get("isrun_prefix") or "").strip().upper()
    if not prefix or base.width_error("isrun_prefix", prefix, _MAX_PREFIX):
        return fail("no_isrun_prefix")

    loccod = str(req.get("loccod") or "").strip().upper()
    if loccod and base.width_error("loccod", loccod, _MAX_LOCCOD):
        return fail("loccod_too_long")
    offset_account = str(req.get("offset_account") or "").strip()
    if offset_account and base.width_error("offset_account", offset_account, _MAX_ACCNUM):
        return fail("offset_account_too_long")

    remark = base.cp874_trim(req.get("remark"), _MAX_REMARK)
    if not remark:
        # STKDES 也抄它:摘要空 = 会计几个月后看报表认不出这批货去哪了。
        return fail("no_remark")

    norm_lines, bad = _normalize_lines(base.clean_rows(req.get("lines") or req.get("items")))
    if bad:
        return fail(bad)

    payload: Dict[str, Any] = {
        "direction": DIRECTION,
        "doc_type": DIRECTION,
        "doctype": DOCTYPE,
        "subtype": SUBTYPE_INTERNAL_ISSUE,
        "account_set": account_set,
        "doc_date": doc_date,
        "isrun_prefix": prefix,
        "loccod": loccod,
        "remark": remark,
        "offset_account": offset_account,
        "lines": norm_lines,
        "userid": base.cp874_trim(req.get("userid"), _MAX_USERID),
        "depcod": str(req.get("depcod") or "").strip(),
        "source": {"ref": str(req.get("ref") or ""), "note": str(req.get("note") or "")},
    }
    prior = str(req.get("prior_docnum") or "").strip()
    if prior:
        payload["prior_docnum"] = prior

    if check_payload(payload):
        return fail("stock_adjust_amounts_not_closed")
    return ExpressMapResult(True, finalize_payload(payload), "ok")


def _normalize_lines(rows: List[Dict[str, Any]]) -> tuple:
    if not rows:
        return [], "no_items"
    out: List[Dict[str, str]] = []
    for row in rows:
        code = str(row.get("stock_code") or "").strip()
        if not code or base.width_error("stock_code", code, _MAX_STOCK_CODE):
            return [], "bad_stock_code"
        # 先落位再判正负:四位以下的数量(0.00004)落位后就是 0,当场退回而不是推一张
        # 数量为零的调整单进去。出库类 POSOPR(4/6/7/9)一律存正数,只有 '8' 存负数 ——
        # 给内部领用写负数,Express 会把它当"负出库=入库"办(P1-2)。
        qty = base.money(row.get("qty"))
        qty = base.quantize_qty(qty) if qty is not None else None
        if qty is None or qty <= base.ZERO:
            return [], "bad_item_qty"
        price = base.money(row.get("unit_price"))
        price = base.quantize_qty(price) if price is not None else None
        if price is None or price <= base.ZERO:
            # 单价 0 = 成本没解出来。推一张金额 0 的报损单等于费用少记,退回让会计填。
            return [], "bad_item_unit_price"
        lot = str(row.get("source_lot") or "").strip()
        if lot and base.width_error("source_lot", lot, _MAX_LOT):
            return [], "bad_source_lot"
        line = {
            "stock_code": code,
            "qty": base.qty_str(qty),
            "unit": str(row.get("unit") or "").strip()[:_MAX_UNIT],
            "unit_price": base.qty_str(price),
            "amount": base.money_str(qty * price),
        }
        factor = base.money(row.get("tfactor"))
        if factor is not None:
            factor = base.quantize_qty(factor)
            if factor <= base.ZERO:
                return [], "bad_item_tfactor"
            line["tfactor"] = base.qty_str(factor)
        if lot:
            line["source_lot"] = lot
        out.append(line)
    return out, ""


_REQUIRED = (
    "account_set",
    "doc_date",
    "isrun_prefix",
    "remark",
    "lines",
    "subtype",
)


def check_payload(payload: Dict[str, Any]) -> Optional[str]:
    """写路总闸(桥门面 build_write_payload 调用)· 返回错误文案或 None。"""
    err = base.required_error(payload, _REQUIRED)
    if err:
        return err
    err = base.docdate_error(payload, "doc_date")
    if err:
        return err
    if payload.get("subtype") != SUBTYPE_INTERNAL_ISSUE:
        # subtype 就是方向:桥端只对 internal_issue 写 POSOPR='6'(出库),别的子类它转人工。
        # 被改成别的值 = 分录方向整个翻面,必须当场拒(45 号契约 X1)。
        return f"subtype v1 只受理 {SUBTYPE_INTERNAL_ISSUE}: {payload.get('subtype')!r}"
    err = base.width_error("isrun_prefix", payload.get("isrun_prefix"), _MAX_PREFIX)
    if err:
        return err

    lines = payload.get("lines")
    err = base.rows_error(lines, "lines")
    if err:
        return err
    for i, row in enumerate(lines):
        if not str(row.get("stock_code") or "").strip():
            return f"lines[{i}] 缺 stock_code"
        qty = base.money(row.get("qty"))
        price = base.money(row.get("unit_price"))
        amount = base.money(row.get("amount"))
        if qty is None or qty <= base.ZERO:
            return f"lines[{i}].qty 须为正数: {row.get('qty')!r}"
        if price is None or price <= base.ZERO:
            return f"lines[{i}].unit_price 须为正数: {row.get('unit_price')!r}"
        if not base.same(amount, qty * price):
            return f"lines[{i}].amount({amount}) != qty×unit_price({qty} × {price})"
    return None
