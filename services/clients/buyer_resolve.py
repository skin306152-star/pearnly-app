# -*- coding: utf-8 -*-
"""买家名/税号 → Pearnly 客户的学习与解析 DAL(REFACTOR-WA-B1 · 2026-05-29 从 clients/store 抽出 · 纯搬家 0 逻辑改)

buyer_to_client_memory 学习 + try_resolve_buyer_to_client(候选检索/冲突)+ resolve_or_create +
归属后回写 ocr_history.client_id。组内自洽(只依赖 db + 组内)· clients/store 顶部 re-import 当 facade ·
db.X/store.X/本模块.X 单一对象不变。
"""

import logging
from typing import Optional, Dict, Any, List  # noqa: F401

logger = logging.getLogger(__name__)


def ensure_buyer_to_client_table():
    """改动 1 (Zihao 2026-05-19 拍板 · v118.34.33) · OCR 完成时按 buyer_name +
    buyer_tax 学习买家 → Pearnly 客户的映射 · 下次 OCR 出同 buyer 自动归属.

    幂等:lifespan 启动调一次. 跟 supplier_categories 同 pattern.
    """
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS buyer_to_client_memory (
                    id           BIGSERIAL PRIMARY KEY,
                    tenant_id    UUID,
                    user_id      UUID NOT NULL,
                    buyer_name   TEXT NOT NULL,
                    buyer_tax    TEXT,
                    client_id    INTEGER NOT NULL,
                    use_count    INTEGER NOT NULL DEFAULT 1,
                    last_used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                -- tenant-or-user-scoped uniqueness on buyer_name+tax pair
                CREATE UNIQUE INDEX IF NOT EXISTS buyer_to_client_unique_scope
                    ON buyer_to_client_memory
                    (COALESCE(tenant_id::text, user_id::text),
                     LOWER(buyer_name),
                     COALESCE(buyer_tax, ''));
                CREATE INDEX IF NOT EXISTS buyer_to_client_tax_idx
                    ON buyer_to_client_memory (buyer_tax)
                    WHERE buyer_tax IS NOT NULL AND length(buyer_tax) >= 10;
            """)
        logger.info("✅ buyer_to_client_memory table ensured")
    except Exception as e:
        logger.warning(f"ensure_buyer_to_client_table failed: {e}")


def learn_buyer_to_client(
    buyer_name: Optional[str],
    buyer_tax: Optional[str],
    client_id: int,
    user_id: str,
    tenant_id: Optional[str] = None,
) -> bool:
    """改动 1 · 用户在抽屉里 assign client_id 时调 · 学习买家 → 客户 映射.
    下次 OCR 出同 buyer 自动归属(改动 1 的 resolve 路径).

    幂等:如果同 (scope, buyer_name, buyer_tax) 已存在 · 更新 client_id
    + use_count++ + last_used_at.
    """
    if not buyer_name or not buyer_name.strip():
        return False
    if not client_id:
        return False
    name = buyer_name.strip()[:200]
    tax = (buyer_tax or "").strip()[:30] or None
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO buyer_to_client_memory
                    (tenant_id, user_id, buyer_name, buyer_tax, client_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (COALESCE(tenant_id::text, user_id::text),
                             LOWER(buyer_name), COALESCE(buyer_tax, ''))
                DO UPDATE SET client_id = EXCLUDED.client_id,
                              use_count = buyer_to_client_memory.use_count + 1,
                              last_used_at = NOW()
            """,
                (tenant_id, str(user_id), name, tax, int(client_id)),
            )
        return True
    except Exception as e:
        logger.warning(f"learn_buyer_to_client failed: {e}")
        return False


def try_resolve_buyer_to_client(
    buyer_name: Optional[str],
    buyer_tax: Optional[str],
    user_id: str,
    tenant_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """改动 1 (Zihao 2026-05-19 拍板) · 按 buyer_name + buyer_tax 查找 Pearnly
    客户 · 返 {client_id, client_name, confidence}.

    阈值 (Zihao 拍板):
      ≥0.95 → 自动绑 + 学习
      0.80-0.95 → 抽屉标"建议归属" (caller 决定)
      <0.80 → 标"待归属" (caller 决定)

    匹配优先级:
      1. buyer_to_client_memory 学习记忆(完全匹配 buyer_name + 同 tax)
         → confidence 1.0
      2. clients.tax_id 完全匹配(13 位 tax_id 唯一)
         → confidence 0.98
      3. clients.name 完全匹配(case-insensitive)
         → confidence 0.95
      4. clients.name 包含 buyer_name (substring 双向)
         → confidence 0.85
      5. clients.short_name 完全/部分匹配
         → confidence 0.80
      没匹配返 None.

    Tenant-scoped lookup · 跟 list_clients 一致.
    """
    if not buyer_name or not buyer_name.strip():
        return None
    name = buyer_name.strip()
    tax = (buyer_tax or "").strip() or None

    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            # Layer 1: 学习记忆完全匹配
            if tenant_id:
                cur.execute(
                    """
                    SELECT m.client_id, c.name AS client_name
                    FROM buyer_to_client_memory m
                    JOIN clients c ON c.id = m.client_id
                    WHERE COALESCE(m.tenant_id::text, m.user_id::text) =
                          COALESCE(%s::text, %s::text)
                      AND LOWER(m.buyer_name) = LOWER(%s)
                      AND COALESCE(m.buyer_tax, '') = COALESCE(%s, '')
                      AND c.is_active = TRUE
                    LIMIT 1
                """,
                    (tenant_id, str(user_id), name, tax),
                )
            else:
                cur.execute(
                    """
                    SELECT m.client_id, c.name AS client_name
                    FROM buyer_to_client_memory m
                    JOIN clients c ON c.id = m.client_id
                    WHERE m.user_id = %s AND m.tenant_id IS NULL
                      AND LOWER(m.buyer_name) = LOWER(%s)
                      AND COALESCE(m.buyer_tax, '') = COALESCE(%s, '')
                      AND c.is_active = TRUE
                    LIMIT 1
                """,
                    (str(user_id), name, tax),
                )
            r = cur.fetchone()
            if r:
                return {
                    "client_id": int(r["client_id"]),
                    "client_name": r["client_name"],
                    "confidence": 1.0,
                    "match_source": "memory",
                }

            # Layer 2: tax_id 完全匹配(13 位 unique)
            if tax and len(tax.replace("-", "").replace(" ", "")) >= 10:
                tax_clean = tax.replace("-", "").replace(" ", "")
                if tenant_id:
                    cur.execute(
                        """
                        SELECT id, name FROM clients
                        WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                          AND REPLACE(REPLACE(COALESCE(tax_id, ''), '-', ''), ' ', '') = %s
                          AND is_active = TRUE
                        LIMIT 1
                    """,
                        (tenant_id, tax_clean),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, name FROM clients
                        WHERE user_id = %s
                          AND REPLACE(REPLACE(COALESCE(tax_id, ''), '-', ''), ' ', '') = %s
                          AND is_active = TRUE
                        LIMIT 1
                    """,
                        (str(user_id), tax_clean),
                    )
                r = cur.fetchone()
                if r:
                    return {
                        "client_id": int(r["id"]),
                        "client_name": r["name"],
                        "confidence": 0.98,
                        "match_source": "tax_id_exact",
                    }

            # Layer 3-5: 名字匹配
            if tenant_id:
                cur.execute(
                    """
                    SELECT id, name, short_name FROM clients
                    WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                      AND is_active = TRUE
                """,
                    (tenant_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, name, short_name FROM clients
                    WHERE user_id = %s AND is_active = TRUE
                """,
                    (str(user_id),),
                )
            rows = cur.fetchall()
            if not rows:
                return None

            name_lower = name.lower()
            best = None  # (confidence, client_id, client_name, source)
            for r in rows:
                cname = (r["name"] or "").strip()
                sname = (r["short_name"] or "").strip()
                if not cname:
                    continue
                cname_lower = cname.lower()
                sname_lower = sname.lower() if sname else ""

                # Layer 3: name 完全匹配 (case-insensitive)
                if cname_lower == name_lower:
                    return {
                        "client_id": int(r["id"]),
                        "client_name": cname,
                        "confidence": 0.95,
                        "match_source": "name_exact",
                    }
                # Layer 3.5: short_name 完全匹配
                if sname_lower and sname_lower == name_lower:
                    return {
                        "client_id": int(r["id"]),
                        "client_name": cname,
                        "confidence": 0.90,
                        "match_source": "short_name_exact",
                    }
                # Layer 4: substring 双向 (一个含另一个)
                if cname_lower in name_lower or name_lower in cname_lower:
                    # 取较短的占较长的比例当 confidence (越接近 1 越像)
                    ratio = min(len(cname_lower), len(name_lower)) / max(
                        len(cname_lower), len(name_lower)
                    )
                    conf = 0.80 + (ratio * 0.10)  # 0.80-0.90
                    if best is None or conf > best[0]:
                        best = (conf, int(r["id"]), cname, "name_substring")
                # Layer 5: short_name substring
                if sname_lower and (sname_lower in name_lower or name_lower in sname_lower):
                    ratio = min(len(sname_lower), len(name_lower)) / max(
                        len(sname_lower), len(name_lower)
                    )
                    conf = 0.78 + (ratio * 0.08)
                    if best is None or conf > best[0]:
                        best = (conf, int(r["id"]), cname, "short_substring")

            if best:
                return {
                    "client_id": best[1],
                    "client_name": best[2],
                    "confidence": round(best[0], 3),
                    "match_source": best[3],
                }
            return None
    except Exception as e:
        logger.warning(f"try_resolve_buyer_to_client failed: {e}")
        return None


def _buyer_candidates_conflict(candidates: Optional[List[str]]) -> bool:
    """判断同一张发票多页是否出现「互不包含」的两个买方名(真冲突)。

    缩写/全称(一个是另一个的子串)视为同一实体 · 不算冲突。
    OCR 噪声(大小写/首尾空格)归一后比对。
    用于 qa_4 那种「同号多页 buyer 候选冲突」→ 不自动建客户 · 转人工确认。
    """
    norm: List[str] = []
    for c in candidates or []:
        s = (c or "").strip().lower()
        if s and s not in norm:
            norm.append(s)
    if len(norm) <= 1:
        return False
    for i in range(len(norm)):
        for j in range(i + 1, len(norm)):
            a, b = norm[i], norm[j]
            if a in b or b in a:
                continue
            return True  # 存在两个互不包含的买方 → 真冲突
    return False


def resolve_or_create_buyer_client(
    buyer_name: Optional[str],
    buyer_tax: Optional[str],
    user_id: str,
    tenant_id: Optional[str] = None,
    *,
    buyer_candidates: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """OCR 落库后把「发票买方」解析到 Pearnly client（税号优先·混合策略，
    Zihao 2026-05-26 拍板）。返回决策 dict，**不写 ocr_history**（caller 负责把
    client_id 写回对应 history + 处理 suggest/review 的 UI 标记）。

    返回:
      {action, client_id, client_name, confidence, match_source, reason}
      action ∈
        "assigned" — 命中已存在高置信客户（memory/税号/名字精确）· 已学习 · 可放行推送
        "created"  — 有合法 13 位税号但无匹配 → 按税号建新客户（去重）· 已学习 · 可放行推送
        "suggest"  — 名字近似但无税号 → 建议归属（不绑/不建）· 等用户一键确认
        "review"   — 多页买方冲突 / 无税号且无匹配 → 待确认（不建垃圾客户）
        "none"     — 没有买方名 → 无可做

    设计要点:
      - **税号 = 泰国法定唯一身份**：有合法 13 位税号且没命中已存在客户 → 直接建（按税号
        去重），这才是「新买方自动建」闭环；只靠名字模糊匹配不建（防同名异主体错并）。
      - 多页买方候选**冲突**（qa_4）→ 绝不自动建 · 转人工 · 杜绝静默高信心错建。
      - 只「移除」模糊情况下的自动建，不会绑/建出错误客户 → 比旧行为严格更安全。
    """
    decision = {
        "action": "none",
        "client_id": None,
        "client_name": None,
        "confidence": 0.0,
        "match_source": "",
        "reason": "",
    }
    if not buyer_name or not buyer_name.strip():
        decision["reason"] = "no_buyer_name"
        return decision

    # 多页买方冲突 → 不自动建,转人工(qa_4)
    if _buyer_candidates_conflict(buyer_candidates):
        decision["action"] = "review"
        decision["reason"] = "buyer_candidates_conflict"
        return decision

    tax_clean = (buyer_tax or "").replace("-", "").replace(" ", "").strip()
    has_valid_tax = len(tax_clean) == 13 and tax_clean.isdigit()

    # 1) 已存在高置信客户(memory 1.0 / 税号精确 0.98 / 名字精确 0.95)→ 用它
    resolved = try_resolve_buyer_to_client(buyer_name, buyer_tax, user_id, tenant_id)
    if resolved and resolved.get("confidence", 0.0) >= 0.95 and resolved.get("client_id"):
        cid = int(resolved["client_id"])
        learn_buyer_to_client(buyer_name, buyer_tax, cid, user_id, tenant_id)
        decision.update(
            action="assigned",
            client_id=cid,
            client_name=resolved.get("client_name"),
            confidence=float(resolved.get("confidence", 0.0)),
            match_source=resolved.get("match_source", ""),
            reason="existing_high_confidence",
        )
        return decision

    # 2) 税号权威:有合法 13 位税号但没高置信匹配 → 按税号找或建(去重),闭环放行
    if has_valid_tax:
        cid = db.find_or_create_client_by_tax_id(user_id, tenant_id, tax_clean, buyer_name.strip())
        if cid:
            learn_buyer_to_client(buyer_name, buyer_tax, int(cid), user_id, tenant_id)
            decision.update(
                action="created",
                client_id=int(cid),
                client_name=buyer_name.strip(),
                confidence=0.98,
                match_source="tax_id_create",
                reason="auto_created_by_tax_id",
            )
            return decision
        # 建失败 → 别静默,转人工
        decision.update(action="review", reason="create_by_tax_failed")
        return decision

    # 3) 名字近似但无税号 → 建议归属(不绑/不建),等用户确认
    if resolved and resolved.get("confidence", 0.0) >= 0.80 and resolved.get("client_id"):
        decision.update(
            action="suggest",
            client_id=int(resolved["client_id"]),
            client_name=resolved.get("client_name"),
            confidence=float(resolved.get("confidence", 0.0)),
            match_source=resolved.get("match_source", ""),
            reason="name_suggestion_no_tax",
        )
        return decision

    # 4) 无税号且无匹配 → 待确认(不建垃圾客户)
    decision.update(action="review", reason="no_tax_no_match")
    return decision


def update_history_client_id(
    history_id: str,
    client_id: Optional[int],
    user_id: str,
    tenant_id: Optional[str] = None,
) -> bool:
    """改动 1 · auto-resolve 时 update history.client_id. Mirror of
    assign_invoice_to_client but skips visible_ids permission check
    (called from server-side auto-resolve hook · not from user click)."""
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            if tenant_id:
                cur.execute(
                    """
                    UPDATE ocr_history
                    SET client_id = %s, updated_at = NOW()
                    WHERE id = %s
                      AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                """,
                    (client_id, history_id, tenant_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE ocr_history
                    SET client_id = %s, updated_at = NOW()
                    WHERE id = %s AND user_id = %s
                """,
                    (client_id, history_id, str(user_id)),
                )
            return cur.rowcount > 0
    except Exception as e:
        logger.warning(f"update_history_client_id failed: {e}")
        return False


from core import db  # noqa: E402 · 循环 import 解法
