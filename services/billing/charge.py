# -*- coding: utf-8 -*-
"""
services/billing/charge.py · OCR 扣费(REFACTOR-B2)

铁律 #26 高敏:钱写入路径 — `tenant_credits.balance_thb` UPDATE + `credit_transactions`
INSERT + `monthly_page_usage` UPSERT。spec 11(充值审核闭环)+ spec 16(OCR 真扣费)兜底。

3 函数 + 1 私有常量(_Dec):
- charge_ocr(user_id, tenant_id, kind, units, history_id?, description?)
    OCR 完成后扣费 · 单原子事务 SELECT FOR UPDATE · 豁免账号 ok=True charged=0 ·
    pdf 走分档定价 + 累加 monthly_page_usage / excel 走字符定价(纯计算)。
- _excel_char_count_estimate(file_bytes, filename)
    估算 Excel/CSV/Word 文件字符数(扣费 units)· xlsx via openpyxl / csv via decode /
    docx via python-docx · 异常降级粗估。
- charge_ocr_async(...)
    fire-and-forget 包装 · asyncio.to_thread 路径 · 失败仅 log。

范式(ADR-007):import db + 运行时 `db.get_cursor()` + db.is_user_billing_exempt /
db._bkk_year_month / db.estimate_pdf_cost_thb / db.estimate_excel_cost_thb(均已 re-export
到 db 命名空间 · 不绕过 re-export 防漂移)。
"""

from __future__ import annotations

import logging
from decimal import Decimal as _Dec

logger = logging.getLogger(__name__)

SATANG_PER_THB = 100


def thb_to_satang(thb) -> int:
    """泰铢 → 萨当(分)· 四舍五入取整。计费写入前归一用。"""
    return int(round(float(thb) * SATANG_PER_THB))


def satang_to_thb(satang) -> _Dec:
    """萨当(分)→ 泰铢 Decimal。扣费金额从 satang 计价转回 THB 时用。"""
    return _Dec(int(satang)) / _Dec(SATANG_PER_THB)


def _debit_balance(cur, tenant_id, cost: _Dec) -> _Dec:
    """从 `tenant_credits.balance_thb` 原子扣减 cost,返回扣后余额。

    SELECT ... FOR UPDATE 防并发(行不存在先建 0)→ 扣减(可到负 · 用量已发生)→ UPDATE。
    调用方须在 `db.get_cursor(commit=True)` 事务内,并自行写 `credit_transactions`。
    """
    cur.execute(
        "SELECT balance_thb FROM tenant_credits WHERE tenant_id = %s::uuid FOR UPDATE",
        (str(tenant_id),),
    )
    row = cur.fetchone()
    if not row:
        cur.execute(
            "INSERT INTO tenant_credits (tenant_id, balance_thb) "
            "VALUES (%s::uuid, 0) RETURNING balance_thb",
            (str(tenant_id),),
        )
        row = cur.fetchone()
    new_bal = _Dec(str(row["balance_thb"])) - cost
    cur.execute(
        "UPDATE tenant_credits SET balance_thb = %s, updated_at = NOW() "
        "WHERE tenant_id = %s::uuid",
        (str(new_bal), str(tenant_id)),
    )
    return new_bal


# ⚠️ 循环 import 处理:
# db.py 文件尾 `from services.billing.charge import charge_ocr` 在自己模块体内 ·
# 若本模块顶部 `import db` · 单独跑 services.billing.charge 时:
#   charge.py → import db → db.py 跑到尾 → from services.billing.charge import → 此时
#   charge 模块 partial(尚未跑到 def · 因为还卡在顶部 `import db`)→ ImportError。
# 把 `import db` 放在所有 def 之后 → 加载顺序变为:
#   charge.py → 跑 def(注册函数 · 不实际调 db)→ `import db` → db.py 跑到尾 →
#   from services.billing.charge import → charge 已有 charge_ocr 等 def → 成功。
# 函数体里 `db.get_cursor() / db.is_user_billing_exempt` 都是 runtime 调,与 import
# 顺序无关。


def _charge_with_subscription(
    user_id, tenant_id, kind, units, quota_pages, history_id, description
) -> dict | None:
    """有有效订阅时扣费:先抵套餐额度(免费)· 超额按 over_rate 从余额扣 · 每次写一条流水。

    返 None = 订阅被并发失效(调用方回落按量计费);其余返结果 dict(含错误)。
    """
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id), commit=True) as cur:
            res = db.consume_subscription_quota(cur, tenant_id, quota_pages)
            if res is None:
                return None
            billable, over_rate = res
            cost = db.overage_cost(billable, over_rate)
            if cost > 0:
                new_bal = _debit_balance(cur, tenant_id, cost)
            else:
                # 套餐内(免费):不动余额 · 只读回当前值入账,避免对 tenant_credits 的无谓写锁(热路径)。
                cur.execute(
                    "SELECT COALESCE(balance_thb, 0) AS b FROM tenant_credits "
                    "WHERE tenant_id = %s::uuid",
                    (str(tenant_id),),
                )
                _r = cur.fetchone()
                new_bal = _Dec(str(_r["b"])) if _r else _Dec("0")
            if billable > 0:
                desc = description or (
                    f"套餐外扫描(超额 {billable} 张) {kind} units={units} hid={history_id or ''}"
                )
            else:
                desc = description or (
                    f"套餐内扫描({quota_pages} 张) {kind} units={units} hid={history_id or ''}"
                )
            cur.execute(
                "INSERT INTO credit_transactions "
                "(tenant_id, user_id, type, amount_thb, pages, balance_after, description) "
                "VALUES (%s::uuid, %s::uuid, 'usage', %s, %s, %s, %s) RETURNING id",
                (
                    str(tenant_id),
                    str(user_id) if user_id else None,
                    str(-cost),
                    int(quota_pages),
                    str(new_bal),
                    desc,
                ),
            )
            tx_id = cur.fetchone()["id"]
        logger.info(
            f"[charge_ocr] SUB tenant={str(tenant_id)[:8]} kind={kind} units={units} "
            f"quota_pages={quota_pages} billable={billable} cost=฿{cost} bal_after=฿{new_bal}"
        )
        return {
            "ok": True,
            "charged_thb": float(cost),
            "balance_after": float(new_bal),
            "kind": kind,
            "units": units,
            "transaction_id": tx_id,
            "subscription": True,
            "quota_pages": int(quota_pages),
            "billable_pages": int(billable),
        }
    except Exception as e:
        logger.error(f"[charge_ocr] SUB FAIL tenant={tenant_id} kind={kind} units={units}: {e}")
        return {"ok": False, "error": str(e)[:200]}


def charge_ocr(
    user_id, tenant_id, kind: str, units: int, history_id: str = None, description: str = ""
) -> dict:
    """OCR 完成后扣费 · v0.21 由调用端用 asyncio.create_task 异步触发
    单原子事务(SELECT FOR UPDATE 防并发)· 内部仍持有连接 · 但已脱离 OCR 关键路径
    kind: 'pdf' (units=page_count) | 'excel' (units=char_count)
    豁免账号自动跳过返 ok=True charged=0
    """
    if not tenant_id:
        return {"ok": False, "error": "no_tenant"}
    if db.is_user_billing_exempt(user_id):
        return {
            "ok": True,
            "charged_thb": 0.0,
            "balance_after": None,
            "kind": kind,
            "units": units,
            "transaction_id": None,
            "exempt": True,
        }

    # 套餐额度折算:pdf 按物理页(1 页=1 张)· excel 文档按字符折算成张。
    if kind == "pdf":
        quota_pages = int(units)
    elif kind == "excel":
        quota_pages = db.doc_quota_pages(units)
    else:
        return {"ok": False, "error": f"unknown_kind:{kind}"}

    # 有有效订阅 → 优先抵套餐额度(超额按 over_rate 扣余额);无订阅/并发失效落到下方按量计费。
    if db.get_active_subscription(tenant_id) is not None:
        sub_out = _charge_with_subscription(
            user_id, tenant_id, kind, units, quota_pages, history_id, description
        )
        if sub_out is not None:
            return sub_out

    if kind == "pdf":
        used = 0
        try:
            with db.get_cursor_rls(tenant_id=str(tenant_id)) as _c:
                _c.execute(
                    "SELECT COALESCE(pages_used, 0) AS u FROM monthly_page_usage "
                    "WHERE tenant_id = %s::uuid AND year_month = %s",
                    (str(tenant_id), db._bkk_year_month()),
                )
                _r = _c.fetchone()
                used = int(_r["u"]) if _r else 0
        except Exception:
            used = 0
        cost = db.estimate_pdf_cost_thb(used, units)
        pages_inc = int(units)
    elif kind == "excel":
        cost = db.estimate_excel_cost_thb(units)
        pages_inc = 0
    else:
        return {"ok": False, "error": f"unknown_kind:{kind}"}

    if cost <= _Dec("0"):
        return {
            "ok": True,
            "charged_thb": 0.0,
            "balance_after": None,
            "kind": kind,
            "units": units,
            "transaction_id": None,
        }

    ym = db._bkk_year_month()
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id), commit=True) as cur:
            new_bal = _debit_balance(cur, tenant_id, cost)  # 可扣到负数(OCR 已完成 · 后续充值补)
            cur.execute(
                "INSERT INTO credit_transactions "
                "(tenant_id, user_id, type, amount_thb, pages, balance_after, description) "
                "VALUES (%s::uuid, %s::uuid, 'usage', %s, %s, %s, %s) RETURNING id",
                (
                    str(tenant_id),
                    str(user_id) if user_id else None,
                    str(-cost),
                    pages_inc,
                    str(new_bal),
                    description or f"OCR {kind} units={units} hid={history_id or ''}",
                ),
            )
            tx_id = cur.fetchone()["id"]

            if kind == "pdf" and pages_inc > 0:
                cur.execute(
                    "INSERT INTO monthly_page_usage (tenant_id, year_month, pages_used, updated_at) "
                    "VALUES (%s::uuid, %s, %s, NOW()) "
                    "ON CONFLICT (tenant_id, year_month) DO UPDATE "
                    "SET pages_used = monthly_page_usage.pages_used + EXCLUDED.pages_used, "
                    "    updated_at = NOW()",
                    (str(tenant_id), ym, pages_inc),
                )
        logger.info(
            f"[charge_ocr] OK tenant={str(tenant_id)[:8]} kind={kind} "
            f"units={units} cost=฿{cost} bal_after=฿{new_bal}"
        )
        return {
            "ok": True,
            "charged_thb": float(cost),
            "balance_after": float(new_bal),
            "kind": kind,
            "units": units,
            "transaction_id": tx_id,
        }
    except Exception as e:
        logger.error(f"[charge_ocr] FAIL tenant={tenant_id} kind={kind} units={units}: {e}")
        return {"ok": False, "error": str(e)[:200]}


def _excel_char_count_estimate(file_bytes: bytes, filename: str) -> int:
    """估算 Excel/CSV/Word 文件的总字符数 · 用于扣费"""
    if not file_bytes:
        return 0
    fn = (filename or "").lower()
    try:
        if fn.endswith(".xlsx") or fn.endswith(".xlsm") or fn.endswith(".xls"):
            try:
                import openpyxl
                import io

                wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
                total = 0
                for ws in wb.worksheets:
                    for row in ws.iter_rows(values_only=True):
                        for c in row:
                            if c is not None:
                                total += len(str(c))
                return total
            except Exception:
                return max(0, len(file_bytes) // 4)  # 粗估降级
        elif fn.endswith(".csv") or fn.endswith(".tsv") or fn.endswith(".txt"):
            try:
                return len(file_bytes.decode("utf-8", errors="ignore"))
            except Exception:
                return 0
        elif fn.endswith(".docx") or fn.endswith(".doc"):
            try:
                import docx
                import io

                doc = docx.Document(io.BytesIO(file_bytes))
                return sum(len(p.text) for p in doc.paragraphs)
            except Exception:
                return max(0, len(file_bytes) // 2)
    except Exception as e:
        logger.warning(f"_excel_char_count_estimate error fn={fn}: {e}")
    return 0


def charge_ocr_async(
    user_id, tenant_id, kind: str, units: int, history_id: str = None, description: str = ""
) -> None:
    """v0.21 · 异步扣费包装 · 调用方:
    asyncio.create_task(asyncio.to_thread(db.charge_ocr_async, ...))
    fire-and-forget · 不阻塞 OCR 关键路径 · 失败仅 log 不影响用户
    """
    try:
        result = charge_ocr(user_id, tenant_id, kind, units, history_id, description)
        if not result.get("ok"):
            logger.warning(f"[charge_ocr_async] failed silently: {result.get('error')}")
    except Exception as e:
        logger.error(f"[charge_ocr_async] exception(swallowed): {e}")


def deduct_thb(user_id, tenant_id, cost_thb, kind: str, description: str = "") -> dict:
    """通用泰铢扣费(知识库等非 OCR 用量)· 复用 OCR 钱路径范式(铁律 #26)。

    单原子事务:`tenant_credits.balance_thb` SELECT FOR UPDATE → UPDATE → `credit_transactions`
    INSERT(type='usage')。豁免账号不扣。余额可扣到负(用量已发生 · 后续充值补 · 同 charge_ocr)。
    cost_thb ≤ 0 直接放行。失败仅 log 不抛(不阻断已完成的用量)。
    """
    cost = _Dec(str(cost_thb))
    if cost <= 0:
        return {"ok": True, "charged_thb": 0.0, "balance_after": None}
    try:
        if db.is_user_billing_exempt(user_id):
            return {"ok": True, "charged_thb": 0.0, "balance_after": None, "exempt": True}
    except Exception:
        pass
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id) if tenant_id else None, commit=True) as cur:
            new_bal = _debit_balance(cur, tenant_id, cost)
            cur.execute(
                "INSERT INTO credit_transactions "
                "(tenant_id, user_id, type, amount_thb, pages, balance_after, description) "
                "VALUES (%s::uuid, %s::uuid, 'usage', %s, %s, %s, %s)",
                (
                    str(tenant_id),
                    str(user_id) if user_id else None,
                    str(-cost),
                    0,
                    str(new_bal),
                    description or f"knowledge {kind}",
                ),
            )
        return {"ok": True, "charged_thb": float(cost), "balance_after": float(new_bal)}
    except Exception as e:
        logger.warning(f"[deduct_thb] knowledge charge failed(tolerated): {e}")
        return {"ok": False, "charged_thb": 0.0, "balance_after": None}


# ⚠️ 见文件顶部注释 · `import db` 必须在所有 def 之后,解 charge ↔ db 循环 import。
from core import db  # noqa: E402
