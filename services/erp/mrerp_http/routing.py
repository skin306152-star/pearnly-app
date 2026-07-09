# -*- coding: utf-8 -*-
"""任意单据 → 方向(销/采)→ MR.ERP doc_type。

复用 Express 侧确定性方向判定(services/erp/express_push/direction · 税号锚点 · 不靠 LLM):
套账主体税号 == 卖方 → 销项;== 买方 → 采购;两边都对不上/都命中 → ambiguous(None,留人工)。
方向再按付款状态细分成具体导入模块(见 modules.MODULES):
  销项:已付/现金 → sales_cash;否则 → sales_credit
  采购:judge_direction(services/purchase/intake · 与 Pearnly 自身单据同口径)判 expense →
       purchase_expense(selmenu 453 · 费用档);判 purchase_invoice → purchase(selmenu 67 · 货品)

只做纯映射;own_tax_id 由调用方从套账主体解析后传入。doc_type=None 时调用方不自动推(留人工)。
"""

from __future__ import annotations

import logging

from typing import Any, Dict, List, Optional

from services.erp.express_push.common import payment_verdict_for
from services.erp.express_push.direction import resolve_direction
from services.erp.express_push.doc_sanity import check_document
from services.erp.mrerp_adapter_models import FailedRow, ImportResult
from services.erp.mrerp_http.modules import get_module
from services.purchase.field_clean import clean_tax_id

logger = logging.getLogger("mr-pilot")


def _fields(flat: Dict[str, Any]) -> Dict[str, Any]:
    f = (flat or {}).get("fields")
    return f if isinstance(f, dict) else {}


def choose_doc_type(
    flat: Dict[str, Any],
    history: Dict[str, Any],
    *,
    own_tax_id: Any,
    mappings: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """套账主体税号 × 票面买卖方 → sales_credit / sales_cash / purchase(_expense) / None。

    mappings 可选(_bank_index · F6 银行佐证喂进销项 payment_verdict);未传 = 旧调用点零改动。
    """
    direction = resolve_direction(flat, history, own_tax_id=own_tax_id)
    fields = _fields(flat)

    if direction == "sales":
        paid, src = payment_verdict_for(flat, fields, mappings, direction="sales")
        doc = "sales_cash" if paid else "sales_credit"
        logger.info("[mrerp-route] doc=%s payment_src=%s", doc, src or "config_default")
        return doc

    # 采购方向货/费分流:人工裁决(posting_item_type_manual · F5 复核屏)优先于自动判据——
    # 会计裁决,不是习惯裁决:有完整税票 = 可抵进项,票面法定证据不许被自动判据/档案习惯压过。
    # 供应商过账档案(supplier_posting_profiles)的 default_item_type 同理在此不自动消费,
    # 只留给工单线预填;唯用户在复核屏显式点过(manual)才算数,精度高于 judge_direction 猜测。
    manual_item = str(fields.get("posting_item_type_manual") or "").strip().lower()
    if manual_item in ("expense", "goods"):
        is_expense = manual_item == "expense"
        item_src = "manual"
    else:
        # 采购锚点已定 或 判不出方向(下方兜底)都要用同一个 judge_direction 结果,算一次复用。
        from services.purchase.intake import judge_direction

        kind, _ = judge_direction(fields)
        is_expense = kind == "expense"
        item_src = f"judge_direction={kind}"

    if direction == "purchase":
        doc = "purchase_expense" if is_expense else "purchase"
        logger.info("[mrerp-route] doc=%s reason=anchor+%s", doc, item_src)
        return doc

    # 税号锚点判不出(零售小票常态:票面无买方身份)→ 跟 Pearnly 自身单据判定走:
    # judge_direction=expense 且买方身份完全缺失 = 本子里记的是费用支出 → ERP 同向
    # 落采购费用档。此前掉端点默认销项 → 销项闸要求挂客户 → 恒 ERR_NO_CLIENT(真机语料
    # SISTER MAKEUP 2026-07-02)。票面读到了买方税号(即便是别家的)不走此兜底,
    # 仍留 None ——那是匹配闸(confirmed_account_set_mismatch)的辖区,不赌方向。
    buyer = clean_tax_id(fields.get("buyer_tax") or fields.get("buyer_tax_id"))
    if is_expense and not buyer:
        logger.info("[mrerp-route] doc=purchase_expense reason=fallback+%s", item_src)
        return "purchase_expense"
    return None


# 单据防呆码 → 四语友好文案(前缀匹配 · currency_not_thb:usd 带后缀也命中)· 全转人工。
# MR.ERP 本地(mrerp_business_friendly 已近 500 行 · 不塞该大目录)· 与 Express 类别渲染并存。
_DOC_SANITY_FRIENDLY: Dict[str, Dict[str, str]] = {
    "currency_not_thb": {
        "th": "เอกสารเป็นสกุลเงินต่างประเทศ (ไม่ใช่บาท) — ตรวจสอบด้วยตนเอง ไม่บันทึกอัตโนมัติ",
        "en": "Foreign-currency document (not THB) — manual review; not auto-posted",
        "zh": "外币单据(非泰铢)· 转人工复核 · 不自动过账",
        "ja": "外貨建て伝票(タイバーツ以外)· 手動確認 · 自動計上しない",
    },
    "seller_buyer_same_tax": {
        "th": "เลขผู้เสียภาษีผู้ขายกับผู้ซื้อเป็นเลขเดียวกัน — เอกสารผิดปกติ ตรวจสอบด้วยตนเอง",
        "en": "Seller and buyer share the same tax ID — abnormal document; manual review",
        "zh": "买卖方税号相同 · 票面异常(自己卖给自己)· 转人工复核",
        "ja": "売り手と買い手の納税者番号が同一 · 伝票異常 · 手動確認",
    },
    "credit_note": {
        "th": "ใบลดหนี้/คืนสินค้า — ต้องกลับรายการ ไม่บันทึกเป็นบิลปกติ",
        "en": "Credit note / return — must be a reversal, not a normal invoice",
        "zh": "贷项/退货单 · 应走负向冲销 · 转人工",
        "ja": "クレジットノート/返品 · 逆仕訳が必要 · 手動確認",
    },
    "deposit_receipt": {
        "th": "ใบรับเงินมัดจำ/ประกัน — ค่าใช้จ่ายยังไม่เกิด ตรวจสอบด้วยตนเอง",
        "en": "Deposit/guarantee receipt — expense not yet incurred; manual review",
        "zh": "押金/定金收据 · 费用尚未发生 · 转人工",
        "ja": "手付金/保証金の受領書 · 費用未発生 · 手動確認",
    },
    "date_implausible": {
        "th": "วันที่เอกสารผิดปกติ (เก่ากว่าปี 2000) — เครื่อง POS อาจไม่ได้ตั้งเวลา ตรวจสอบด้วยตนเอง",
        "en": "Implausible document date (before 2000) — POS clock likely unset; manual review",
        "zh": "单据日期异常(早于 2000 年)· POS 时钟疑未设置 · 转人工复核",
        "ja": "伝票日付が異常(2000年以前)· POS 時計未設定の可能性 · 手動確認",
    },
    "date_future": {
        "th": "วันที่เอกสารเป็นอนาคต — ตรวจสอบด้วยตนเอง",
        "en": "Document date is in the future — please review",
        "zh": "单据日期为未来 · 可疑复核 · 转人工",
        "ja": "伝票日付が未来 · 要確認 · 手動確認",
    },
    "date_reissued": {
        "th": "เอกสารออกใบแทน/ย้อนหลัง — ตรวจสอบด้วยตนเอง",
        "en": "Re-issued/back-dated document — please review",
        "zh": "补开/倒签单据 · 可疑复核 · 转人工",
        "ja": "再発行/遡及日付の伝票 · 要確認 · 手動確認",
    },
    "tax_id_invalid": {
        "th": "เลขประจำตัวผู้เสียภาษีของคู่ค้าไม่ครบ 13 หลัก — ตรวจสอบ",
        "en": "Counterparty tax ID is not 13 digits — please check",
        "zh": "对手方税号非 13 位 · 转人工核对",
        "ja": "取引先の納税者番号が13桁でない · 要確認",
    },
}


_PURCHASE_DOC_TYPES = ("purchase", "purchase_expense")


def _doc_sanity_reason(history: Dict[str, Any], doc_type: str) -> Optional[str]:
    """单据防呆(外币/贷项/押金/未来日期/坏税号)· 复用 Express doc_sanity · 命中返 reason。"""
    fields = history.get("fields") if isinstance(history.get("fields"), dict) else {}
    direction = "purchase" if doc_type in _PURCHASE_DOC_TYPES else "sales"
    return check_document(fields, history, direction)


def _sanity_fail_row(history: Dict[str, Any], reason: str) -> FailedRow:
    from services.erp import mrerp_xlsx_generator as _gen

    friendly = next(
        (tr for pfx, tr in _DOC_SANITY_FRIENDLY.items() if reason.startswith(pfx)), None
    )
    return FailedRow(
        invoice_no=_gen.derive_mrerp_invoice_no(history),
        reasons=[reason],
        reasons_friendly=[friendly] if friendly else [],
        original=history,
    )


MODULE_UNAVAILABLE_CODE = "ERR_MRERP_MODULE_UNAVAILABLE"


def _module_unavailable_fail_row(history: Dict[str, Any]) -> FailedRow:
    """端点未真机验证(verified=False)静态判掉的行 → 转人工 · 四语文案见 mrerp_business_friendly。"""
    from services.erp import mrerp_xlsx_generator as _gen
    from services.erp.mrerp_business_friendly import translate_reasons

    reasons = [MODULE_UNAVAILABLE_CODE]
    return FailedRow(
        invoice_no=_gen.derive_mrerp_invoice_no(history),
        reasons=reasons,
        reasons_friendly=translate_reasons(reasons),
        original=history,
    )


def _walkin_to_cash(history: Dict[str, Any], default_doc: str, mappings: Dict[str, Any]) -> bool:
    """无买方散客销售 → 现金销售单(ขายเงินสด · 账正:钱入现金,不在 เงินสด 客户下虚挂应收)。

    仅当 ① 默认端点是销项 ② 开关开(默认 · mappings['_mrerp_walkin_sales_cash']=False 可关)
    ③ 无买方身份(无 client_id 且票面无买方税号)。现金收款科目由 sales_cash 生成器解析(默认
    1111-01,可经 _mrerp_receipt_account_cash 覆盖);套账无该科目时 account_gate 会干净挡下,不乱推。
    """
    if not default_doc.startswith("sales"):
        return False
    if not (isinstance(mappings, dict) and mappings.get("_mrerp_walkin_sales_cash", True)):
        return False
    if history.get("client_id"):
        return False
    fields = _fields(history)
    return not clean_tax_id(fields.get("buyer_tax") or fields.get("buyer_tax_id"))


def route_and_upload(adapter, histories: List[Dict[str, Any]], mappings: Dict[str, Any]):
    """按每张单据的方向路由 doc_type 再推送 · 合并为一个 ImportResult(同一会话内复用登录)。

    推送前先跑**单据防呆**(外币/贷项/押金/未来日期/坏税号 → 转人工·复用 Express doc_sanity),
    命中即落 failed 不推不建。其余**只把【确认为采购】的票切到采购/费用模块**——销项 / 判不出方向
    一律保持默认 doc_type(sales_credit),零倒退;别家的票由匹配闸(_filter_by_account_set)另挡。
    """
    if not histories:
        return ImportResult(total=0)
    total = len(histories)
    own = mappings.get("_own_tax_id") if isinstance(mappings, dict) else None
    default_doc = adapter.module.doc_type
    sanity_failed: List[FailedRow] = []
    groups: Dict[str, List[Dict[str, Any]]] = {}  # dict 保序 → 无需单独 order 列表
    for h in histories:
        chosen = choose_doc_type(h, h, own_tax_id=own, mappings=mappings)
        if chosen in _PURCHASE_DOC_TYPES:
            dt = chosen  # 采购(货品/67)或采购费用(453)分别切到各自模块
        elif _walkin_to_cash(h, default_doc, mappings):
            dt = "sales_cash"  # 散客现金销售 → ขายเงินสด(账正)
        else:
            dt = default_doc  # 销项/判不出 → 默认(sales_credit)· 零倒退
        reason = _doc_sanity_reason(h, dt)
        if reason:
            sanity_failed.append(_sanity_fail_row(h, reason))
            continue
        groups.setdefault(dt, []).append(h)

    # 方向可排查:push 日志 request_body 不记 doc_type,出问题只能反证(真机排查踩过)。
    logger.info(
        "[mrerp-route] groups=%s sanity_failed=%d",
        {
            k: [str(h.get("invoice_number") or h.get("id") or "?")[:24] for h in v]
            for k, v in groups.items()
        },
        len(sanity_failed),
    )
    if not groups:  # 全被防呆挡下
        res = ImportResult(total=total)
        res.failed = sanity_failed
        return res

    # 无防呆命中 且 全部同向=默认 → 走原路(零行为变化 · 单次 upload)。
    if not sanity_failed and list(groups) == [default_doc]:
        return adapter.upload_invoice_batch(histories, mappings)

    merged = ImportResult(total=total)
    saved = adapter.module
    try:
        for dt in groups:
            m = get_module(dt)
            # 端点未真机验证(master_* 等 verified=False)→ 静态前置判掉,只转这一组人工,
            # 别拖累混批里已打通的组。条件与 adapter 的 verified 闸(upload 前 raise)同源;
            # 这里不 catch MRERPBusinessError——那也是已验证组真服务器拒收的载体,吞了会错标。
            if not m.verified or m.selmenu is None:
                logger.warning(
                    "[mrerp-route] doc=%s module unavailable · %d row(s) held for manual review",
                    dt,
                    len(groups[dt]),
                )
                merged.failed.extend(_module_unavailable_fail_row(h) for h in groups[dt])
                continue
            adapter.module = m
            r = adapter.upload_invoice_batch(groups[dt], mappings)
            merged.success.extend(r.success)
            merged.failed.extend(r.failed)
            merged.elapsed_ms += r.elapsed_ms or 0
            merged.xlsx_size_bytes += r.xlsx_size_bytes or 0
    finally:
        adapter.module = saved
    merged.failed.extend(sanity_failed)
    return merged


# 匹配闸失败码 · 四语文案在 mrerp_business_friendly(_fail_row 经 translate_reasons 取)。
ACCOUNT_SET_MISMATCH_CODE = "ERR_ACCOUNT_SET_MISMATCH"


def confirmed_account_set_mismatch(
    flat: Dict[str, Any], history: Dict[str, Any], *, own_tax_id: Any, expected_direction: str
) -> bool:
    """能【确认】这张票不属于本套账吗?防"把别家的票推错套账"的安全闸。

    只在【确认不符】时返 True(挡下),读不到税号=无法确认→False(不挡·交上游已判的方向)。
    确认不符 = ① 方向刚好相反(如采购票走销项)· 或 ② 票面读到了买卖方税号但都不是套账主体。
    own_tax_id 空(套账税号未解析)→ 无锚点无法判 → False(不挡)。
    """
    if not own_tax_id:
        return False
    direction = resolve_direction(flat, history, own_tax_id=own_tax_id)
    if direction == expected_direction:
        return False  # 确认属于本套账
    if direction:
        return True  # 方向相反(采购票走销项等)→ 确认不符
    # direction=None(ambiguous):仅当票面确实读到买卖方税号、却都不是套账主体,才算确认别家的票
    own = clean_tax_id(own_tax_id)
    fields = _fields(flat)
    read = [
        t
        for t in (
            clean_tax_id(fields.get("seller_tax") or fields.get("seller_tax_id")),
            clean_tax_id(fields.get("buyer_tax") or fields.get("buyer_tax_id")),
        )
        if t
    ]
    return bool(read) and own not in read
