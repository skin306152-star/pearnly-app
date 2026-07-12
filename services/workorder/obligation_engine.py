# -*- coding: utf-8 -*-
"""客户×当期→适用义务生成(B2-d · 税务画像-方案-B1.md §3)。

generate_obligations 是纯函数核心:profile × period × data_signals × defs → 义务清单,
不碰游标/不落库。defs 由 services.workspace.tax_profile_store.load_active_defs 读取
(tax_obligation_defs 是全租户共享法定常量表,无 tenant_id 列——放画像域而非本模块,
免了本包 test_workorder_sql_isolation 的"每句 DML 必带 tenant_id"机械闸误伤);
materialize_obligations 是本模块唯一的写路径,写 client_period_obligations(该表按
tenant_id 隔离,DML 带 tenant_id)。rematerialize_for_profile 是「取 defs → 现算 →
落库」三步曲的唯一编排入口(开单接线、画像保存后重算两处调用方共用,失败不抛只记
日志返 False——义务清单是供料层,不该挡住开单/画像保存主路径)。

算法(§3.1 并集 + 数据覆盖,§3.2 九义务映射表):
  - obligations = profile_triggered ∪ data_triggered,每条带 status ∈
    {due, tentative, data_triggered, nil, conflict}。
  - profile 'no' 遇 data 'yes' → conflict(防 stale 画像静默漏报,不是 data 压过 profile,
    是两者矛盾必须人工确认)。
  - profile 'unknown' 且无数据佐证 → tentative,义务仍进清单,不省略。
  - filing_disposition=dormant → 本应 due 的降级为 nil(义务仍在,须报零)。
  - PP30(VAT)对 vat_status=registered 恒生成;当期无任何料件(has_any_material=False)
    时同样降级 nil——"零申报 ≠ 免申报"。
  - PND54(pays_foreign)与 PP36 共享同一触发字段与数据信号(defs seed 两行 trigger_kind
    都是 pays_foreign),生成规则天然同步,无需额外联动代码。
  - 截止日 = defs 当期生效版本(effective_from/effective_to 过滤)的 day 字段,锚定
    「期间次月」的公历日期;period 是佛历「YYYY-MM」(如 2569-05),年份需 -543。
  - SSO 的 e-Payment 截止日 = 纸质截止 + sso_epayment_extra_workdays 天,按自然日直加、
    不做周末/节假日顺延——顺延算法是 G3 法定日历引擎的活,此处先记原样(方案 §3.3 边界)。

data_signals(付款对象类由 services.workorder.wht_signals 扫采购 WHT 提取;employees_paid 由
services.payroll 工资进料校验通过后喂):
    {"wht_individuals": bool, "wht_juristic": bool, "foreign_payment": bool,
     "interest_dividend": bool, "employees_paid": bool, "has_any_material": bool}
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from services.summary_import.dates import to_ad_year
from services.workspace import tax_profile_store

logger = logging.getLogger(__name__)

# 佛历「当期」判定(§3.3):佛历 = 公历 + 543(与 services/summary_import/dates.py 同口径),
# period 格式恒为「YYYY-MM」——本模块是 period↔公历互译的唯一权威,画像路由等消费方
# 一律 import 这两个常量,不许另起一份判据。
_BE_YEAR_OFFSET = 543
PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

# 义务状态(§3.1)。
STATUS_DUE = "due"
STATUS_TENTATIVE = "tentative"
STATUS_DATA_TRIGGERED = "data_triggered"
STATUS_NIL = "nil"
STATUS_CONFLICT = "conflict"

# trigger_source:标注一条义务凭什么进清单,供人审/审计追溯,不是给机器分支用的枚举。
SRC_PROFILE = "profile"
SRC_PROFILE_UNKNOWN = "profile_unknown"
SRC_DATA = "data"
SRC_DATA_OVERRIDE_PROFILE_NO = "data_override_profile_no"

# defs.trigger_kind → data_signals 键(§3.2:"付款对象"类四项 + 雇员 employees_paid(H1 工资
# 进料喂真信号);VAT/SBT 无对应数据信号,只从画像亮)。has_employees 走独立分支(见
# _obligation_for_code),不进本表 —— 它同时驱动 pnd1 与 sso 两义务,统一在分支里指信号键。
_DATA_SIGNAL_BY_TRIGGER = {
    "pays_individuals": "wht_individuals",
    "pays_juristic": "wht_juristic",
    "pays_foreign": "foreign_payment",
    "pays_interest_dividend": "interest_dividend",
}

_DATA_SIGNAL_KEYS = (
    "wht_individuals",
    "wht_juristic",
    "foreign_payment",
    "interest_dividend",
    "employees_paid",
    "has_any_material",
)


class ObligationEngineError(ValueError):
    """period 格式非法等输入错误,不静默吞、不猜测。"""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _empty_data_signals() -> dict:
    """TODO(D1):真实数据信号提取——扫当期采购行 WHT 命中个人/法人对手方、境外付款、
    利息股息付款、是否有任何入库料件。本批(B2-d)按方案要求只接调用方传入的信号,
    工单开单接线处先传空信号字典(见 services/workorder/api.py::open_order)。"""
    return {k: False for k in _DATA_SIGNAL_KEYS}


def current_be_period() -> str:
    """当前公历月 → 佛历「YYYY-MM」,给「当期」判据的所有消费方(义务重物化、义务清单
    GET 缺省 period)用同一权威,不许各自另算。"""
    today = datetime.now(timezone.utc).date()
    return f"{today.year + _BE_YEAR_OFFSET:04d}-{today.month:02d}"


def _period_to_ad_month_start(period: str) -> date:
    """佛历期「YYYY-MM」→ 该期对应公历月首日(佛历年 -543)。"""
    try:
        year_be_s, month_s = period.split("-")
        year_ad = to_ad_year(int(year_be_s))
        month = int(month_s)
        return date(year_ad, month, 1)
    except (ValueError, AttributeError, TypeError):
        raise ObligationEngineError("invalid_period") from None


def _next_month_start(d: date) -> date:
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)


def _as_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _def_active_for_period(defn: dict, period_anchor: date) -> bool:
    """defs 当期生效版本过滤:period 所在月须落在 [effective_from, effective_to] 内
    (effective_to 为空 = 长期有效)。锚点取「期间」本身(申报所属月),不是截止日。"""
    effective_from = _as_date(defn.get("effective_from"))
    effective_to = _as_date(defn.get("effective_to"))
    if effective_from and period_anchor < effective_from:
        return False
    if effective_to and period_anchor > effective_to:
        return False
    return True


def _due_dates(defn: dict, next_month_start: date) -> tuple[Optional[date], Optional[date]]:
    due_paper = _at_day(next_month_start, defn.get("due_paper_day"))
    due_efiling_day = defn.get("due_efiling_day")
    if due_efiling_day is not None:
        due_efiling = _at_day(next_month_start, due_efiling_day)
    else:
        extra = defn.get("sso_epayment_extra_workdays") or 0
        # SSO e-Payment:纸质基准 +N 天记原样,不做周末/节假日顺延(方案 §3.3 边界,
        # 顺延算法归 G3 法定日历引擎)。
        due_efiling = due_paper + timedelta(days=extra) if due_paper and extra else None
    return due_paper, due_efiling


def _at_day(month_start: date, day: Optional[int]) -> Optional[date]:
    if day is None:
        return None
    return date(month_start.year, month_start.month, int(day))


def _binary_profile_obligation(
    profile: dict, field: str, data_key: Optional[str], data_signals: dict
) -> Optional[tuple[str, str]]:
    """yes/no/unknown 三态画像字段 ∪ 数据实测的通用判定(§3.1)。返回 (status, source),
    None = 不生成该义务(profile 明确说'no' 且无数据佐证)。"""
    value = profile.get(field, "unknown")
    data_hit = bool(data_key) and bool(data_signals.get(data_key))
    if value == "yes":
        return STATUS_DUE, SRC_PROFILE
    if value == "no":
        if data_hit:
            # stale 画像说"不",当期数据却命中——两者矛盾,浮给人确认,不静默丢义务。
            return STATUS_CONFLICT, SRC_DATA_OVERRIDE_PROFILE_NO
        return None
    # unknown(含任何未识别取值,防御性同归 unknown 处理,不静默省略)。
    if data_hit:
        return STATUS_DATA_TRIGGERED, SRC_DATA
    return STATUS_TENTATIVE, SRC_PROFILE_UNKNOWN


def _pp30_obligation(profile: dict) -> Optional[tuple[str, str]]:
    value = profile.get("vat_status", "unregistered")
    if value == "registered":
        return STATUS_DUE, SRC_PROFILE
    if value == "unknown":
        return STATUS_TENTATIVE, SRC_PROFILE_UNKNOWN
    return None  # unregistered:确认无 VAT 登记,不生成


def _sbt_obligation(profile: dict) -> Optional[tuple[str, str]]:
    value = profile.get("sbt_status", "unknown")
    if value == "registered":
        return STATUS_DUE, SRC_PROFILE
    if value == "unknown":
        return STATUS_TENTATIVE, SRC_PROFILE_UNKNOWN
    return None  # none:窄行业默认不生成


def _obligation_for_code(
    defn: dict, profile: dict, data_signals: dict
) -> Optional[tuple[str, str]]:
    trigger_kind = defn.get("trigger_kind")
    if trigger_kind == "vat_status":
        return _pp30_obligation(profile)
    if trigger_kind == "sbt_status":
        return _sbt_obligation(profile)
    if trigger_kind in _DATA_SIGNAL_BY_TRIGGER:
        return _binary_profile_obligation(
            profile, trigger_kind, _DATA_SIGNAL_BY_TRIGGER[trigger_kind], data_signals
        )
    if trigger_kind == "has_employees":
        # H1:工资进料校验通过 → employees_paid 真信号点亮 pnd1/sso(画像 no 却有进料 → conflict)。
        return _binary_profile_obligation(profile, trigger_kind, "employees_paid", data_signals)
    return None  # 未识别的 trigger_kind(未来 defs 新增须先教引擎认,不猜)


def generate_obligations(
    *,
    profile: dict,
    period: str,
    data_signals: Optional[dict],
    defs: dict,
) -> list[dict]:
    """profile × period × data_signals × defs → 义务清单(纯函数,零 I/O)。

    每条:{obligation_code, status, trigger_source, due_paper, due_efiling}(后两者为
    date 或 None)。按 obligation_code 排序输出,结果确定性、不依赖 dict 迭代顺序。
    """
    signals = dict(_empty_data_signals())
    if data_signals:
        signals.update(data_signals)

    period_anchor = _period_to_ad_month_start(period)
    next_month_start = _next_month_start(period_anchor)
    dormant = profile.get("filing_disposition") == "dormant"

    out: list[dict] = []
    for code in sorted(defs):
        defn = defs[code]
        if not _def_active_for_period(defn, period_anchor):
            continue
        resolved = _obligation_for_code(defn, profile, signals)
        if resolved is None:
            continue
        status, source = resolved
        if status == STATUS_DUE and dormant:
            status = STATUS_NIL
        elif code == "pp30" and status == STATUS_DUE and not signals.get("has_any_material"):
            status = STATUS_NIL

        due_paper, due_efiling = _due_dates(defn, next_month_start)
        out.append(
            {
                "obligation_code": code,
                "status": status,
                "trigger_source": source,
                "due_paper": due_paper,
                "due_efiling": due_efiling,
            }
        )
    return out


def materialize_obligations(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    work_order_id: Optional[str],
    period: str,
    obligations: list[dict],
) -> None:
    """幂等 upsert 到 client_period_obligations(唯一键 tenant/client/period/code)。
    只碰 status/trigger_source/due_paper/due_efiling/work_order_id,批次 C/D 预留列
    (assignee/filed_at/receipt_ref)一律不动——它们的写路径不归本模块管。"""
    for ob in obligations:
        cur.execute(
            """
            INSERT INTO client_period_obligations
                (tenant_id, workspace_client_id, work_order_id, period, obligation_code,
                 status, trigger_source, due_paper, due_efiling)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (tenant_id, workspace_client_id, period, obligation_code)
            DO UPDATE SET
                work_order_id = EXCLUDED.work_order_id,
                status = EXCLUDED.status,
                trigger_source = EXCLUDED.trigger_source,
                due_paper = EXCLUDED.due_paper,
                due_efiling = EXCLUDED.due_efiling,
                updated_at = now()
            """,
            (
                tenant_id,
                workspace_client_id,
                work_order_id,
                period,
                ob["obligation_code"],
                ob["status"],
                ob["trigger_source"],
                ob["due_paper"],
                ob["due_efiling"],
            ),
        )


def rematerialize_for_profile(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    period: str,
    profile: dict,
    work_order_id: Optional[str] = None,
    data_signals: Optional[dict] = None,
) -> bool:
    """「取 defs → 现算 → 落库」三步曲的唯一编排入口(开单接线、画像保存后重算两处
    调用方共用)。data_signals 由调用方扫当期采购 WHT 后透传(见 services.workorder.
    wht_signals);None = 兜底走全 False 空信号,只吃画像判据、不虚报数据触发义务。
    义务清单是供料层,不该挡住调用方的主路径——任一环节出错都吞掉、记日志、返 False,
    调用方按返回值决定是否再报,不需自己包 try/except。"""
    try:
        defs = tax_profile_store.load_active_defs(cur)
        obligations = generate_obligations(
            profile=profile, period=period, data_signals=data_signals, defs=defs
        )
        materialize_obligations(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            work_order_id=work_order_id,
            period=period,
            obligations=obligations,
        )
        return True
    except Exception:
        logger.exception(
            "obligation_engine rematerialize failed (tenant=%s, client=%s, period=%s)",
            tenant_id,
            workspace_client_id,
            period,
        )
        return False
