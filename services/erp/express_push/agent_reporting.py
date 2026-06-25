# -*- coding: utf-8 -*-
"""Express 本地 Agent 心跳上报的数据访问层(账套/科目表/所选账套/科目映射/在线状态)。

从 agent_store 拆出(单一职责 + 控行数):agent_store 管 token/lease/ack 状态机,本模块
管 Agent 周期心跳带上来的【探测/选择数据】,统一净化后并进本 express endpoint 的 config
(网页只读镜像 · 小助手为唯一真相源)。隔离沿用现有 ERP 约定:只更新本 endpoint 的 config。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_ACCOUNT_SET_KEYS = ("code", "name", "name_en", "tax_id", "path", "writable")
_MAX_ACCOUNT_SETS = 50


def _sanitize_account_sets(raw: Any) -> List[Dict[str, Any]]:
    """净化 Agent 上报的账套列表:只留已知键、限长限量,布尔归一(防被塞脏数据)。"""
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw[:_MAX_ACCOUNT_SETS]:
        if not isinstance(item, dict):
            continue
        clean: Dict[str, Any] = {}
        for k in _ACCOUNT_SET_KEYS:
            v = item.get(k)
            if k == "writable":
                clean[k] = bool(v)
            elif v is not None:
                clean[k] = str(v)[:200]
        if clean.get("code") or clean.get("name"):
            out.append(clean)
    return out


def store_account_sets(endpoint_id: str, account_sets: Any) -> int:
    """存 Agent 探测的可用账套列表进 config.reported_account_sets(供 FE「选账套」读)。

    净化后整体替换(非累加),并记 account_sets_seen_at。返回存入条数。
    """
    sets = _sanitize_account_sets(account_sets)
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_endpoints
                SET config = COALESCE(config, '{}'::jsonb) || jsonb_build_object(
                        'reported_account_sets', %s::jsonb,
                        'account_sets_seen_at', to_jsonb(NOW()::text))
                WHERE id = %s AND adapter = 'express'
                """,
                (json.dumps(sets, ensure_ascii=False), endpoint_id),
            )
        return len(sets)
    except Exception as e:
        logger.error(f"store_account_sets failed: {e}")
        return 0


# ── 科目表(chart of accounts)· 供 FE「科目映射」下拉按名字选 ──────────────────
# 小助手登录 Express 读科目 DBF(如 GLMAS)上报。科目表【可自定义·每账套不同】→ 必须按
# 账套发现,不能在程序里写死默认码(Owner 2026-06-22 拍板)。
_ACCOUNT_KEYS = ("code", "name", "type")
_MAX_ACCOUNTS = 3000


def _sanitize_accounts(raw: Any) -> List[Dict[str, Any]]:
    """净化 Agent 上报的科目表:只留 code/name/type、限长限量。code 必填(科目码=记账锚)。"""
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw[:_MAX_ACCOUNTS]:
        if not isinstance(item, dict):
            continue
        clean: Dict[str, Any] = {}
        for k in _ACCOUNT_KEYS:
            v = item.get(k)
            if v is not None and str(v).strip() != "":
                clean[k] = str(v).strip()[:120]
        if clean.get("code"):
            out.append(clean)
    return out


def store_reported_accounts(endpoint_id: str, accounts: Any) -> int:
    """存小助手探测的【科目表】进 config.reported_accounts(供 FE「科目映射」下拉读)。

    净化后整体替换 + 记 accounts_seen_at;返回存入条数。镜像 store_account_sets。
    客户在下拉里按【名字】选科目,FE 存科目【码】进 config(revenue_acc 等)。
    """
    accs = _sanitize_accounts(accounts)
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_endpoints
                SET config = COALESCE(config, '{}'::jsonb) || jsonb_build_object(
                        'reported_accounts', %s::jsonb,
                        'accounts_seen_at', to_jsonb(NOW()::text))
                WHERE id = %s AND adapter = 'express'
                """,
                (json.dumps(accs, ensure_ascii=False), endpoint_id),
            )
        return len(accs)
    except Exception as e:
        logger.error(f"store_reported_accounts failed: {e}")
        return 0


# 所选账套【整组】· 方法无关(直录/RPA 共用 · 见 11-dispatch 可扩展性契约 §1/§2/§5)。
# account_set 名(白名单)+ account_dir(DBF 写文件)+ account_company(公司名硬闸)
# + account_set_row(RPA 登录后公司 grid 行)。客户选一次整组都推出,RPA 来零新增字段。
_SELECTED_ACCOUNT_KEYS = ("account_set", "account_dir", "account_company", "account_set_row")


def _merge_config(endpoint_id: str, patch: Dict[str, Any]) -> bool:
    """把 patch 以 jsonb `||` 合并进本 express endpoint 的 config(顶层键 create-or-replace)。"""
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_endpoints
                SET config = COALESCE(config, '{}'::jsonb) || %s::jsonb
                WHERE id = %s AND adapter = 'express'
                """,
                (json.dumps(patch, ensure_ascii=False), endpoint_id),
            )
        return True
    except Exception as e:
        logger.error(f"_merge_config failed: {e}")
        return False


def _clean_selected(fields: Dict[str, Any]) -> Dict[str, Any]:
    """从上报 dict 取所选账套整组的非空字段(account_set_row 转 int)。"""
    sel: Dict[str, Any] = {}
    for k in _SELECTED_ACCOUNT_KEYS:
        v = (fields or {}).get(k)
        if k == "account_set_row":
            if v is not None and str(v).strip() != "":
                try:
                    sel[k] = int(v)
                except (TypeError, ValueError):
                    pass
        elif v is not None and str(v).strip() != "":
            sel[k] = str(v).strip()
    return sel


def selected_account_changed(current: Dict[str, Any], reported: Dict[str, Any]) -> bool:
    """上报的所选账套整组是否与已存 config 不同(防每拍无谓写库)。"""
    for k in _SELECTED_ACCOUNT_KEYS:
        if str((reported or {}).get(k) or "").strip() != str((current or {}).get(k) or "").strip():
            return True
    return False


def store_selected_account(endpoint_id: str, fields: Dict[str, Any]) -> bool:
    """存小助手上报的【所选账套整组】→ config(方法无关·不按 method 阉割)。

    账套选择唯一真相源 = 本地小助手(客户在那里选)。云端存整组、网页镜像账套名。
    只写上报到的非空字段;`account_set` 名缺失 → 整体跳过(没选不覆盖)。只更新本 express endpoint。
    """
    sel = _clean_selected(fields if isinstance(fields, dict) else {})
    if not sel.get("account_set"):
        return False
    return _merge_config(endpoint_id, sel)


_MAPPING_KEYS = (
    "revenue_acc",
    "ar_acc",
    "vat_output_acc",
    "fallback_acc",
    "ap_acc",
    "vat_input_acc",
)


def store_mapping(endpoint_id: str, mapping: Dict[str, Any]) -> bool:
    """存小助手上报的【科目映射】6 个科目码 → config(网页只读镜像·小助手为唯一真相源)。

    只合并非空码(避免未配置时的空上报清掉已存值)。镜像 store_selected_account 的语义。
    """
    patch: Dict[str, Any] = {}
    for k in _MAPPING_KEYS:
        v = str((mapping or {}).get(k) or "").strip()[:40]
        if v:
            patch[k] = v
    if not patch:
        return False
    return _merge_config(endpoint_id, patch)


def mark_offline(endpoint_id: str) -> None:
    """小助手优雅退出 → 把 last_seen 置远古,令前端在线判定(now-seen<180s)立即失败 → 显示离线。"""
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_endpoints
                SET config = COALESCE(config, '{}'::jsonb)
                    || jsonb_build_object('agent_last_seen_at', '1970-01-01 00:00:00+00')
                WHERE id = %s AND adapter = 'express'
                """,
                (endpoint_id,),
            )
    except Exception as e:
        logger.error(f"mark_offline failed: {e}")


def touch_heartbeat(endpoint_id: str) -> None:
    """更新 config.agent_last_seen_at = NOW(UTC)。"""
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_endpoints
                SET config = jsonb_set(
                        COALESCE(config, '{}'::jsonb),
                        '{agent_last_seen_at}', to_jsonb(NOW()::text), true)
                WHERE id = %s AND adapter = 'express'
                """,
                (endpoint_id,),
            )
    except Exception as e:
        logger.error(f"touch_heartbeat failed: {e}")
