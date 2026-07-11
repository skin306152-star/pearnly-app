# -*- coding: utf-8 -*-
"""Express 推送前置条件体检(preflight · 纯读)。

把 enqueue 的闸链抽成可单独调用、返回逐项结果的函数:enqueue 消费它产推送结果(单一
真相源,不分叉);UI / 异常页消费它渲染"还差什么"的红绿灯清单。与 enqueue 旧行为同序、
同 reason、同 request_body —— 由 test_express_enqueue 的 65 条契约钉死。

体检序:特性开关 → 账套白名单 → 方向(税号锚点)→ 方向启用 → 单据防呆(币种/贷项/押金/
日期/税号)→ 映射(科目/金额/日期/借贷)→ 写前 GLACC 白名单 → 置信评级。任一不过即 blocked,
其后未跑项标 pending。绝不写库。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from services.erp.express_push import account_set_allowed, chart_codes, express_push_enabled
from services.erp.express_push import direction as direction_mod
from services.erp.express_push.common import PAYLOAD_VERSION
from services.erp.express_push.doc_sanity import check_document
from services.erp.express_push.mapper import build_express_payload
from services.erp.express_push.sales_mapper import build_express_sales_payload
from services.purchase.field_clean import clean_tax_id

logger = logging.getLogger(__name__)

# 体检项顺序(UI 渲染 + pending 回填用 · 与闸序一致)。
CHECK_KEYS = (
    "feature",
    "account_set",
    "payload_version",
    "direction",
    "direction_enabled",
    "document",
    "mapping",
    "chart",
    "confidence",
)

OK = "ok"
BLOCKED = "blocked"
PENDING = "pending"  # 早闸已拦,本项未跑到


@dataclass
class Check:
    key: str
    status: str
    reason: str = ""


@dataclass
class Preflight:
    """体检结果。reason=None 且非 disabled → ready(可入队);disabled → 特性关;其余 blocked。"""

    disabled: bool = False
    reason: Optional[str] = None  # 规范 manual reason(喂 enqueue · 与旧行为逐字一致)
    request_body: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None
    direction: Optional[str] = None
    category: str = ""
    verdict: Any = None
    checks: List[Check] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return not self.disabled and self.reason is not None

    @property
    def ready(self) -> bool:
        return not self.disabled and self.reason is None

    def checks_json(self) -> List[Dict[str, str]]:
        return [{"key": c.key, "status": c.status, "reason": c.reason} for c in self.checks]


def _category_of(flat: Dict[str, Any]) -> str:
    fields = flat.get("fields") if isinstance(flat.get("fields"), dict) else {}
    return str(flat.get("category") or (fields or {}).get("category") or "").strip()


def _own_tax_id(endpoint: Dict[str, Any], flat: Dict[str, Any], tenant_id: Optional[str]) -> str:
    """账套自家公司税号(方向判定锚点)= 该 history 所属 workspace 主体的 tax_id。

    workspace_clients 即"卖方抬头/账套主体"。失败/缺 workspace_client_id → 返 ''(下游判
    ambiguous,留人工,不误推)。多公司扩展位:将来可返本 workspace 客户公司税号集合。
    """
    try:
        wcid = flat.get("workspace_client_id")
        if not wcid:
            return ""
        from core import db

        wc = db.get_workspace_client(int(wcid), endpoint.get("user_id"), tenant_id=tenant_id)
        return str((wc or {}).get("tax_id") or "").strip()
    except Exception:
        logger.exception("express own tax id resolve failed; direction will be ambiguous")
        return ""


def _resolve_direction(
    endpoint: Dict[str, Any],
    flat: Dict[str, Any],
    history: Dict[str, Any],
    tenant_id: Optional[str],
    own_tax_cache: Optional[Dict[int, str]] = None,
) -> tuple:
    """方向判定的唯一定义(单票/批量共用防手抄漂移):显式标签优先,否则懒取自家税号
    比对票面(批量传 own_tax_cache 按套账缓存,免每票一次库往返)。返回 (direction, own_tax);
    own_tax 仅在走了税号锚才非空,单票路径拿它区分 subject_unbound/ambiguous。
    """
    direction = direction_mod.explicit_direction(flat, history)
    if direction is not None:
        return direction, ""
    if own_tax_cache is None:
        own_tax = _own_tax_id(endpoint, flat, tenant_id)
    else:
        wcid = int(flat["workspace_client_id"])
        if wcid not in own_tax_cache:
            own_tax_cache[wcid] = _own_tax_id(endpoint, flat, tenant_id)
        own_tax = own_tax_cache[wcid]
    return direction_mod.detect_by_tax(flat, own_tax), own_tax


def _unknown_account(payload: Dict[str, Any], codes: set) -> Optional[str]:
    """返回首个不在科目表白名单里的分录科目码(None=全部合法)。挡死码/AI 乱码/缓存过期。"""
    for ln in payload.get("lines") or []:
        acc = str((ln or {}).get("acc") or "").strip()
        if acc and acc not in codes:
            return acc
    return None


def _allowed_directions(config: Dict[str, Any]) -> tuple:
    """本连接处理的方向(进项/销项/两者)· 默认两者。"""
    raw = config.get("directions")
    if not raw:
        return ("purchase", "sales")
    if isinstance(raw, str):
        raw = [x.strip() for x in raw.split(",") if x.strip()]
    out = tuple(str(x).lower() for x in raw)
    return out or ("purchase", "sales")


def _grade(history: Dict[str, Any], payload: Dict[str, Any], has_category: bool, direction: str):
    """置信判级(复用 confidence.grade · 按实际方向传)。失败返 None 放行。"""
    try:
        from services.expense import confidence

        fields = history.get("fields") if isinstance(history.get("fields"), dict) else {}
        party = payload.get("customer") if direction == "sales" else payload.get("supplier")
        # confidence 的"可入账"门是采购/费用语义(销项不在其中)。销项按 Express 政策可过账,
        # 故以 purchase 口径复用其金额/卖家/票号/band 闸 —— direction 仅控可入账门,其余无关。
        grade_direction = "purchase" if direction == "sales" else direction
        return confidence.grade(
            amount=payload.get("total_amount"),
            vendor_name=(party or {}).get("name") or "",
            invoice_number=payload.get("ref_no") or "",
            document_type=str((fields or {}).get("document_type") or "tax_invoice"),
            direction=grade_direction,
            confidence_band=str(history.get("confidence") or ""),
            has_category=has_category,
            require_category=False,
        )
    except Exception:
        logger.exception("express confidence grade failed; passing through")
        return None


def _attach_payment_evidence(
    flat: Dict[str, Any],
    mappings: Dict[str, Any],
    tenant_id: Optional[str],
    user_id: Any,
    *,
    prefetch: Optional[Dict[str, Any]] = None,
) -> None:
    """F4(L2)+F6(L3):供应商过账档案(仅进项 · 档案锚是卖方税号)+ 银行流水索引(两方向)·
    就地写进 mappings 供 mapper/sales_mapper 的 payment_verdict 判据链读取。

    prefetch 给了(批量入口 build_batch_prefetch 算好的整批份)→ 直接消费,单票 0 查询;
    否则(单票直推/重试路径)原样自查 —— 两条路径消费同一套判据,结果必须等价。
    查不到/表未建/无日期 → 对应键留空,绝不挡推送(与 F4/F6 本身"只加固不否决"的定位一致)。
    """
    if flat.get("direction") == "purchase" and tenant_id and flat.get("workspace_client_id"):
        fields = flat.get("fields") if isinstance(flat.get("fields"), dict) else {}
        seller_tax = clean_tax_id(
            (fields or {}).get("seller_tax") or (fields or {}).get("seller_tax_id")
        )
        if seller_tax:
            wcid = int(flat["workspace_client_id"])
            if prefetch is not None:
                mappings["_supplier_profile"] = (
                    (prefetch.get("profiles") or {}).get(wcid, {}).get(seller_tax)
                )
            else:
                try:
                    from core import db
                    from services.purchase.supplier_posting import get_profiles

                    with db.get_cursor() as cur:
                        profiles = get_profiles(
                            cur, tenant_id=tenant_id, workspace_client_id=wcid, tax_ids=[seller_tax]
                        )
                    mappings["_supplier_profile"] = profiles.get(seller_tax)
                except Exception:
                    logger.exception("preflight_express: supplier profile lookup failed")

    if prefetch is not None:
        mappings["_bank_index"] = prefetch.get("bank_index") or []
        return

    try:
        from services.erp.express_push.bank_evidence import load_bank_index_for_history

        mappings["_bank_index"] = load_bank_index_for_history(flat, user_id)
    except Exception:
        logger.exception("preflight_express: bank index attach failed")


def build_batch_prefetch(
    endpoint: Dict[str, Any], histories: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """批级预取(去 N+1):整批一次拉供应商过账档案(F4)+ 银行流水索引(F6),逐票 preflight
    消费同一份结果代替各自查询 —— N 张票的 2N 次查询收成 1 次银行查询 + 每个 workspace_client
    一次档案查询(通常整批共用同一账套 → 常态就是 1 次)。

    profiles 按 workspace_client_id 分组(套账隔离 · 不可跨套账混档案),键与
    `_attach_payment_evidence` 消费时的 int(flat['workspace_client_id']) 对齐。方向判定走
    `_resolve_direction`(与单票同一份定义 · own_tax 按套账缓存批内只解析一次)。任一环节
    失败 → 对应键留空,消费侧按"查不到"处理,与单票路径的失败语义一致。
    """
    from core import db
    from services.erp.erp_payload import flatten_history_for_mrerp
    from services.erp.express_push.bank_evidence import load_bank_index_for_histories
    from services.purchase.supplier_posting import get_profiles

    user_id = endpoint.get("user_id")
    tenant_id = db.get_user_tenant_id(user_id) if user_id else None
    flats = [flatten_history_for_mrerp(h) for h in histories]

    bank_index: List[Dict[str, Any]] = []
    try:
        bank_index = load_bank_index_for_histories(flats, user_id)
    except Exception:
        logger.exception("build_batch_prefetch: bank index attach failed")

    profiles: Dict[int, Dict[str, dict]] = {}
    if tenant_id:
        own_tax_cache: Dict[int, str] = {}
        tax_ids_by_wcid: Dict[int, set] = {}
        for history, flat in zip(histories, flats):
            wcid_raw = flat.get("workspace_client_id")
            if not wcid_raw:
                continue
            fields = flat.get("fields") if isinstance(flat.get("fields"), dict) else {}
            seller_tax = clean_tax_id(
                (fields or {}).get("seller_tax") or (fields or {}).get("seller_tax_id")
            )
            if not seller_tax:
                continue
            wcid = int(wcid_raw)
            direction, _ = _resolve_direction(endpoint, flat, history, tenant_id, own_tax_cache)
            if direction != "purchase":
                continue
            tax_ids_by_wcid.setdefault(wcid, set()).add(seller_tax)

        for wcid, tax_ids in tax_ids_by_wcid.items():
            try:
                with db.get_cursor() as cur:
                    profiles[wcid] = get_profiles(
                        cur, tenant_id=tenant_id, workspace_client_id=wcid, tax_ids=list(tax_ids)
                    )
            except Exception:
                logger.exception(
                    "build_batch_prefetch: supplier profile lookup failed wcid=%s", wcid
                )

    return {"profiles": profiles, "bank_index": bank_index}


def _fill_pending(checks: List[Check]) -> None:
    present = {c.key for c in checks}
    for k in CHECK_KEYS:
        if k not in present:
            checks.append(Check(k, PENDING))


def _block(
    pf: Preflight,
    key: str,
    *,
    reason: str,
    request_body: Dict[str, Any],
    check_reason: Optional[str] = None,
) -> Preflight:
    pf.checks.append(Check(key, BLOCKED, check_reason if check_reason is not None else reason))
    _fill_pending(pf.checks)
    pf.reason = reason
    pf.request_body = request_body
    return pf


def preflight_express(
    endpoint: Dict[str, Any],
    history: Dict[str, Any],
    *,
    prefetch: Optional[Dict[str, Any]] = None,
) -> Preflight:
    """对一条 history 跑全部前置条件,返回逐项体检结果(纯读 · 不入队不写库)。

    prefetch:批量入口(build_batch_prefetch)算好的批级供应商档案/银行索引,原样透传给
    _attach_payment_evidence;None(单票直推/重试路径)→ 该函数内部自查,行为不变。
    """
    config = (endpoint or {}).get("config") or {}
    pf = Preflight()

    if not express_push_enabled():
        pf.disabled = True
        pf.checks.append(Check("feature", BLOCKED, "express_disabled"))
        _fill_pending(pf.checks)
        return pf
    pf.checks.append(Check("feature", OK))

    # 账套白名单(逐端点 · 须 == 本端点配置账套)。
    account_set = str(config.get("account_set") or "").strip()
    if not account_set_allowed(account_set, endpoint):
        return _block(
            pf,
            "account_set",
            reason=f"account_set_not_allowed:{account_set or 'none'}",
            request_body={"adapter": "express", "account_set": account_set},
        )
    pf.checks.append(Check("account_set", OK))

    # 载荷版本协商:小助手心跳上报过 max_payload_version 且低于当前契约 → 拦下(会推一份它
    # 解析不了的字段)。未上报(老客户端 · 未升级过心跳)→ 视同支持 1,绝不误拦现有推送。
    reported_pv = config.get("max_payload_version")
    if reported_pv is not None:
        try:
            supported_pv = int(reported_pv)
        except (TypeError, ValueError):
            supported_pv = PAYLOAD_VERSION  # 脏值读不出数 → 不拿它误拦,按支持最新处理
        if supported_pv < PAYLOAD_VERSION:
            return _block(
                pf,
                "payload_version",
                reason=f"payload_version_outdated:{supported_pv}",
                request_body={"adapter": "express", "max_payload_version": supported_pv},
            )
    pf.checks.append(Check("payload_version", OK))

    try:
        from core import db
        from services.erp.erp_payload import flatten_history_for_mrerp

        flat = flatten_history_for_mrerp(history)
        user_id = endpoint.get("user_id")
        tenant_id = db.get_user_tenant_id(user_id) if user_id else None
        mappings = db.get_mrerp_mappings_bundle(tenant_id) if tenant_id else {}
        category = _category_of(flat)
        pf.category = category

        # 方向(确定性·税号锚点):显式标签优先,否则比对自家公司税号 × 票面 seller/buyer。
        direction, own_tax = _resolve_direction(endpoint, flat, history, tenant_id)
        if direction is None:
            # 区分两种判不出:主体没绑/税号没读到(subject_unbound)vs 票面对不上(ambiguous)。
            # 仅供 UI 提示;喂 enqueue 的规范 reason 仍是 direction_unknown。
            sub = "subject_unbound" if not own_tax else "ambiguous"
            return _block(
                pf,
                "direction",
                reason="direction_unknown",
                request_body={"adapter": "express", "history_id": str(flat.get("id") or "")},
                check_reason=sub,
            )
        flat["direction"] = direction  # 写回 → 下游同口径分流
        pf.direction = direction
        pf.checks.append(Check("direction", OK))

        if direction not in _allowed_directions(config):
            return _block(
                pf,
                "direction_enabled",
                reason=f"direction_not_enabled:{direction}",
                request_body={"adapter": "express", "direction": direction},
            )
        pf.checks.append(Check("direction_enabled", OK))

        # 单据防呆(确定性):外币/贷项/押金/未来日期/坏税号等"不该当普通票直推"的单据 → 转人工。
        doc_reason = check_document(flat.get("fields") or {}, flat, direction)
        if doc_reason:
            return _block(
                pf,
                "document",
                reason=doc_reason,
                request_body={"adapter": "express", "history_id": str(flat.get("id") or "")},
            )
        pf.checks.append(Check("document", OK))

        _attach_payment_evidence(flat, mappings, tenant_id, user_id, prefetch=prefetch)

        if direction == "sales":
            mres = build_express_sales_payload(
                flat, config=config, mappings=mappings, category=category
            )
        else:
            mres = build_express_payload(flat, config=config, mappings=mappings, category=category)
        if not mres.ok:
            return _block(
                pf,
                "mapping",
                reason=mres.reason,
                request_body={"adapter": "express", "manual_reason": mres.reason},
            )
        payload = mres.payload
        pf.payload = payload
        pf.checks.append(Check("mapping", OK))

        # 防御性复核白名单(mapper 已带 account_set · 与 Agent lease 同口径)· 命中归 account_set 项。
        if not account_set_allowed(payload.get("account_set"), endpoint):
            for c in pf.checks:
                if c.key == "account_set":
                    c.status = BLOCKED
                    c.reason = "account_set_not_allowed"
            _fill_pending(pf.checks)
            pf.reason = "account_set_not_allowed"
            pf.request_body = payload
            return pf

        # 写前科目白名单(闸2):分录每个科目须 ∈ 账套上报科目表;未上报则跳过(不阻塞旧 Agent)。
        chart = chart_codes(config)
        if chart is not None:
            bad = _unknown_account(payload, chart)
            if bad:
                return _block(
                    pf, "chart", reason=f"account_not_in_chart:{bad}", request_body=payload
                )
        pf.checks.append(Check("chart", OK))

        verdict = _grade(history, payload, bool(category), direction)
        pf.verdict = verdict
        if verdict is not None and verdict.action != "post":
            reason = "low_confidence:" + ",".join(verdict.reasons)
            return _block(pf, "confidence", reason=reason, request_body=payload)
        pf.checks.append(Check("confidence", OK))

        return pf  # ready

    except Exception as e:
        logger.exception("preflight_express failed")
        pf.reason = f"enqueue_error:{type(e).__name__}"
        pf.request_body = {"adapter": "express"}
        _fill_pending(pf.checks)
        return pf
