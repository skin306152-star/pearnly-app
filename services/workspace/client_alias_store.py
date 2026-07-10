# -*- coding: utf-8 -*-
"""泰英商号别名 DAL(B2-c · client_name_aliases · G1R2 毛刺②根治)。

方向锚现状只认 workspace_clients.name(单一泰文法定名),票面印英文商号(Ocha 的
"Sister Makeup")时归一化跨语种永不相等 → 名称锚空转。本表存客户的**额外别名**,读时
与法定名并集喂方向锚(sort._direction_by_name),把跨语种失锚补上。

precedence 铁律不动:税号仍第一优先,别名只在税号失锚后兜底(消费点见 sort.py)。

污染防护(方案 §4.6,错别名→错客户→错方向 = 账错级,故写前多层闸):
  闸1 同租户 active alias_norm 唯一(应用层预检 + DB 部分唯一索引 uq_client_alias_norm 兜底):
      一个 norm 只能指一个 active 客户,第二客户认领同别名 → 结构化错误,绝不静默二选一。
  闸2 最小特异性:alias_norm 长度 ≥4;拒纯泛词停用表;substring 模式要求 norm ≥6。
  闸3 source 分级:方向锚只消费 human_confirmed(resolve_names 过滤),ai_suggested 进影子不生效。
归一化复用 sort._normalize_company_name(单一事实源,与法定名同口径,不另抄一份)。

隔离=每句 WHERE tenant_id(+ workspace_client_id);值一律 %s 参数化。调用方负责事务
(cur 注入 + keyword-only,与 services/purchase/supplier_posting.py 同风格)。
"""

from __future__ import annotations

from typing import Optional

from services.workorder.steps.sort import _normalize_company_name

# 方向锚消费的可信来源:只认人工确认的别名(方案 §4.6 闸3)。ai_suggested / data_inferred
# 走影子(只记不锚),由 B2-e 建档引导提示待确认,人确认才转 human_confirmed。
CONSUMED_SOURCES = frozenset({"human_confirmed"})

# 别名归一化后的最小长度(闸2)。exact 模式 ≥4,substring 模式 ≥6(子串更易误扫,门槛更高)。
MIN_NORM_LEN = 4
MIN_SUBSTRING_NORM_LEN = 6

# 纯泛词停用表(闸2):归一化后落到这些通用词的别名会扫中无关票,一律拒。法人前后缀
# (บริษัท/จำกัด/co.,ltd…)已被 _normalize_company_name 剥掉,这里补的是「字号位」上的泛词。
_STOPWORDS = frozenset(
    {
        "shop",
        "store",
        "company",
        "limited",
        "market",
        "mart",
        "cafe",
        "coffee",
        "restaurant",
        "makeup",
        "beauty",
        "general",
        "trading",
        "service",
        "services",
        "ร้าน",
        "ห้าง",
        "บริษัท",
        "จำกัด",
        "ขายดี",
    }
)

# match_mode 合法值:exact = 归一等值(默认,最防污染);substring = 允许子串(需 norm ≥6)。
MATCH_MODES = ("exact", "substring")

ERR_ALIAS_TOO_SHORT = "alias.too_short"
ERR_ALIAS_GENERIC_TERM = "alias.generic_term"
ERR_ALIAS_SUBSTRING_TOO_SHORT = "alias.substring_too_short"
ERR_ALIAS_NORM_CONFLICT = "alias.norm_conflict"

_MESSAGES: dict[str, dict[str, str]] = {
    ERR_ALIAS_TOO_SHORT: {
        "zh": "别名太短,归一化后至少要 4 个字符(防泛词误扫无关票)",
        "en": "Alias too short: at least 4 characters after normalization",
        "th": "ชื่อย่อสั้นเกินไป ต้องมีอย่างน้อย 4 ตัวอักษรหลังจัดรูปแบบ",
        "ja": "エイリアスが短すぎます。正規化後4文字以上必要です",
    },
    ERR_ALIAS_GENERIC_TERM: {
        "zh": "别名过于泛用(如 shop/store/makeup),会扫中无关票,请填更具体的商号",
        "en": "Alias is too generic (e.g. shop/store); please use a more specific trade name",
        "th": "ชื่อย่อทั่วไปเกินไป (เช่น shop/store) กรุณาใช้ชื่อทางการค้าที่เฉพาะเจาะจง",
        "ja": "エイリアスが一般的すぎます(shop/store 等)。具体的な商号を入力してください",
    },
    ERR_ALIAS_SUBSTRING_TOO_SHORT: {
        "zh": "子串匹配的别名归一化后至少要 6 个字符",
        "en": "Substring-match alias needs at least 6 characters after normalization",
        "th": "ชื่อย่อแบบจับคู่บางส่วนต้องมีอย่างน้อย 6 ตัวอักษรหลังจัดรูปแบบ",
        "ja": "部分一致エイリアスは正規化後6文字以上必要です",
    },
    ERR_ALIAS_NORM_CONFLICT: {
        "zh": "该别名已被本机构另一客户占用,不能重复认领(防错挂客户)",
        "en": "This alias is already claimed by another client in your org",
        "th": "ชื่อย่อนี้ถูกใช้โดยลูกค้ารายอื่นในองค์กรแล้ว",
        "ja": "このエイリアスは組織内の別の顧客が既に使用しています",
    },
}


class AliasError(ValueError):
    """别名污染闸拒绝(结构化,绝不静默)。code 供前端逻辑分支;message 四语就地可读。

    继承 ValueError 让未接住时也当输入错误处理,不被误当 500 内部故障。
    """

    def __init__(self, code: str):
        self.code = code
        self.message = _MESSAGES[code]
        super().__init__(code)

    def payload(self) -> dict:
        return {"code": self.code, "message": self.message}


def _guard_norm(alias_norm: str, match_mode: str) -> None:
    """写前闸2:长度 / 泛词 / substring 门槛。命中即 raise AliasError(不静默截断)。"""
    if len(alias_norm) < MIN_NORM_LEN:
        raise AliasError(ERR_ALIAS_TOO_SHORT)
    if alias_norm in _STOPWORDS:
        raise AliasError(ERR_ALIAS_GENERIC_TERM)
    if match_mode == "substring" and len(alias_norm) < MIN_SUBSTRING_NORM_LEN:
        raise AliasError(ERR_ALIAS_SUBSTRING_TOO_SHORT)


def _active_norm_owner(cur, tenant_id: str, alias_norm: str) -> Optional[int]:
    """同租户是否已有 active 别名占了这个 norm → 返回占用它的 workspace_client_id,否则 None。"""
    cur.execute(
        "SELECT workspace_client_id FROM client_name_aliases "
        "WHERE tenant_id = %s AND alias_norm = %s AND is_active = TRUE LIMIT 1",
        (tenant_id, alias_norm),
    )
    row = cur.fetchone()
    if not row:
        return None
    return int(row["workspace_client_id"] if isinstance(row, dict) else row[0])


def add_alias(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    alias_raw: str,
    alias_kind: str = "misc",
    match_mode: str = "exact",
    source: str = "human_confirmed",
    confidence: Optional[float] = None,
) -> Optional[int]:
    """加一条别名,过污染闸后落库(alias_norm 由 _normalize_company_name 归一)。

    返回新行 id;别名归一化后为空则 no-op 返回 None;闸2/闸1 命中 raise AliasError。
    同客户重复认领同一 active norm → 幂等返回既有 id;别的客户认领 → 冲突拒绝(闸1)。
    """
    raw = str(alias_raw or "").strip()
    alias_norm = _normalize_company_name(raw)
    if not alias_norm:
        return None
    mode = match_mode if match_mode in MATCH_MODES else "exact"
    _guard_norm(alias_norm, mode)

    owner = _active_norm_owner(cur, tenant_id, alias_norm)
    if owner is not None:
        if owner != int(workspace_client_id):
            raise AliasError(ERR_ALIAS_NORM_CONFLICT)
        # 同客户已有 active 同 norm → 幂等,取既有 id 不重复插(DB 部分唯一索引也会挡)。
        cur.execute(
            "SELECT id FROM client_name_aliases WHERE tenant_id = %s "
            "AND workspace_client_id = %s AND alias_norm = %s AND is_active = TRUE LIMIT 1",
            (tenant_id, int(workspace_client_id), alias_norm),
        )
        row = cur.fetchone()
        return int(row["id"] if isinstance(row, dict) else row[0]) if row else None

    cur.execute(
        "INSERT INTO client_name_aliases "
        "(tenant_id, workspace_client_id, alias_raw, alias_norm, alias_kind, match_mode, "
        "source, confidence, is_active) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE) RETURNING id",
        (
            tenant_id,
            int(workspace_client_id),
            raw[:200],
            alias_norm,
            alias_kind,
            mode,
            source,
            confidence,
        ),
    )
    row = cur.fetchone()
    return int(row["id"] if isinstance(row, dict) else row[0]) if row else None


def deactivate_alias(cur, *, tenant_id: str, alias_id: int) -> bool:
    """软删一条别名(is_active=FALSE)。保留历史 + 让占用的 norm 释放给别的客户认领。"""
    cur.execute(
        "UPDATE client_name_aliases SET is_active = FALSE, updated_at = now() "
        "WHERE tenant_id = %s AND id = %s AND is_active = TRUE",
        (tenant_id, int(alias_id)),
    )
    return cur.rowcount > 0


def list_aliases(
    cur, *, tenant_id: str, workspace_client_id: int, active_only: bool = True
) -> list[dict]:
    """列一个客户的别名(B2-e 别名管理界面 + 巡检用)。active_only=False 含已软删的历史行。"""
    sql = (
        "SELECT id, alias_raw, alias_norm, alias_kind, match_mode, source, confidence, "
        "is_active, created_at, updated_at FROM client_name_aliases "
        "WHERE tenant_id = %s AND workspace_client_id = %s"
    )
    if active_only:
        sql += " AND is_active = TRUE"
    sql += " ORDER BY id"
    cur.execute(sql, (tenant_id, int(workspace_client_id)))
    return [dict(r) for r in (cur.fetchall() or [])]


def resolve_names(cur, *, tenant_id: str, workspace_client_id: int) -> list[tuple[str, str]]:
    """方向锚名集:[(法定名, "legal")] + 该客户 active 且 human_confirmed 的 [(别名, match_mode)]。

    法定名走 workspace_clients.name(不镜像进别名表,免双写漂移),别名只并入可信来源
    (闸3:ai_suggested 不进)。返回 (name, mode) 序列直接喂 sort._direction_by_name。
    """
    entries: list[tuple[str, str]] = []
    cur.execute(
        "SELECT name FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (int(workspace_client_id), tenant_id),
    )
    row = cur.fetchone()
    legal = (row["name"] if isinstance(row, dict) else row[0]) if row else None
    if legal:
        entries.append((str(legal), "legal"))

    cur.execute(
        "SELECT alias_raw, match_mode FROM client_name_aliases "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND is_active = TRUE "
        "AND source = ANY(%s) ORDER BY id",
        (tenant_id, int(workspace_client_id), list(CONSUMED_SOURCES)),
    )
    for r in cur.fetchall() or []:
        raw = r["alias_raw"] if isinstance(r, dict) else r[0]
        mode = r["match_mode"] if isinstance(r, dict) else r[1]
        if raw:
            entries.append((str(raw), mode if mode in MATCH_MODES else "exact"))
    return entries
