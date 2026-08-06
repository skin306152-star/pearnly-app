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

# 存货科目组的判据(筛候选 / 选哪个)已拆去 stock_acc_group —— 本模块只管上报数据的存取。
# 此处 re-import 当 facade:agent_reporting.fit_stock_acc_groups 的既有调用点不用跟着改。
from services.erp.express_push.stock_acc_group import fit_stock_acc_groups  # noqa: F401

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


# ── 存货科目组候选 · 小助手读 ISACC.DBF(METHOD='A')上报 ──────────────────────────
# 账套里一件库存品都没有时,小助手没有可克隆的 STMAS 模板行,只能靠一个 ISACC 科目组
# (ACCCOD → 存货资产 ACCNUM01 + 销货成本 ACCNUM02)从零建 STKTYP=0。METHOD='A' 只是必要
# 条件:真账套 70EXP 的 10 个 A 组里有 6 个 ACCNUM01 挂的是费用科目(52/53),拿来建库存品
# 会把存货记成费用。能不能用由小助手判(fit),云端只存不猜。
_STOCK_ACC_GROUP_KEYS = (
    "acccod",
    "name",
    "method",
    "stock_acc",
    "stock_acc_name",
    "cogs_acc",
    "cogs_acc_name",
)
# 上游有两套叫法,都归一到上面这套(键名对不上 → 整表被丢成空 → 下拉永远没候选,
# 2026-07-25 真机就是这么哑掉的):小助手 catalog_probe 发 code/desc/inv_acc*,
# 若直接回传 ISACC 原始行则是 DBF 列名。
_ISACC_ALIASES = {
    "accdes": "name",
    "accnum01": "stock_acc",
    "accnum02": "cogs_acc",
    "code": "acccod",
    "desc": "name",
    "inv_acc": "stock_acc",
    "inv_acc_name": "stock_acc_name",
}
_MAX_STOCK_ACC_GROUPS = 100


def _sanitize_stock_acc_groups(raw: Any) -> List[Dict[str, Any]]:
    """净化上报的存货科目组候选:只留已知键、限长限量,fit 归一布尔。

    acccod 必填 —— 它是「选哪个组」的唯一锚,没有它这条候选选不了也存不住。
    """
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw[:_MAX_STOCK_ACC_GROUPS]:
        if not isinstance(item, dict):
            continue
        src = {str(k).strip().lower(): v for k, v in item.items()}
        for alias, key in _ISACC_ALIASES.items():
            if alias in src and key not in src:
                src[key] = src[alias]
        clean: Dict[str, Any] = {"fit": bool(src.get("fit"))}
        for k in _STOCK_ACC_GROUP_KEYS:
            v = src.get(k)
            if v is not None and str(v).strip() != "":
                clean[k] = str(v).strip()[:120]
        try:  # 下拉上显示「N 个商品在用」,帮会计认出哪个才是这家真在用的组
            clean["used_by"] = max(0, int(src.get("used_by") or 0))
        except (TypeError, ValueError):
            clean["used_by"] = 0
        if clean.get("acccod"):
            out.append(clean)
    return out


def store_reported_stock_acc_groups(endpoint_id: str, candidates: Any) -> int:
    """存小助手上报的【存货科目组候选】→ config.reported_stock_acc_groups(整体快照替换)。

    净化后替换 + 记 stock_acc_groups_seen_at;返回存入条数。镜像 store_reported_accounts。
    端点 PATCH 据此校验「选的是不是真候选」,推送异常卡据此渲染科目组下拉。
    """
    groups = _sanitize_stock_acc_groups(candidates)
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_endpoints
                SET config = COALESCE(config, '{}'::jsonb) || jsonb_build_object(
                        'reported_stock_acc_groups', %s::jsonb,
                        'stock_acc_groups_seen_at', to_jsonb(NOW()::text))
                WHERE id = %s AND adapter = 'express'
                """,
                (json.dumps(groups, ensure_ascii=False), endpoint_id),
            )
        return len(groups)
    except Exception as e:
        logger.error(f"store_reported_stock_acc_groups failed: {e}")
        return 0


# ── 商品/客户目录 + 记账指纹 · 小助手读 STMAS/ARMAS/STCRD 上报 ─────────────────────
# reported_products/customers 供 catalog_resolver 判「复用现有 vs 新建」;catalog_fingerprint
# 供 posting_profile 推库存模式。目录可上万条 → 限量;整体快照替换(与账套列表同语义,非累加)。
_PRODUCT_KEYS = ("code", "name", "kind")  # kind = stock | non_stock(companion 从 STKTYP 派生)
_CUSTOMER_KEYS = ("code", "name", "tax_id", "kind", "branch")  # branch=ARMAS ORGNUM(5 位分店号)
_FINGERPRINT_INT_KEYS = ("stock_master_count", "stcrd_lines", "stcrd_lines_moving_stock")
_MAX_CATALOG = 20000


def _sanitize_catalog(raw: Any, keys: tuple) -> List[Dict[str, Any]]:
    """净化上报目录:只留已知键、限长限量;code 或 name 至少一个非空才收。"""
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw[:_MAX_CATALOG]:
        if not isinstance(item, dict):
            continue
        clean: Dict[str, Any] = {}
        for k in keys:
            v = item.get(k)
            if v is not None and str(v).strip() != "":
                clean[k] = str(v).strip()[:200]
        if clean.get("code") or clean.get("name"):
            out.append(clean)
    return out


def _sanitize_fingerprint(raw: Any) -> Dict[str, int]:
    """净化记账指纹:只留三个计数键、归一非负整数(喂 posting_profile 推库存模式)。"""
    if not isinstance(raw, dict):
        return {}
    fp: Dict[str, int] = {}
    for k in _FINGERPRINT_INT_KEYS:
        v = raw.get(k)
        try:
            fp[k] = max(0, int(v))
        except (TypeError, ValueError):
            continue
    return fp


def store_reported_catalog(
    endpoint_id: str, products: Any, customers: Any, fingerprint: Any = None
) -> tuple:
    """存小助手上报的【商品 + 客户目录 + 记账指纹】→ config(整体快照替换)。

    reported_products/customers 供 catalog_resolver 判复用;catalog_fingerprint 供
    posting_profile 推库存模式。返回 (商品数, 客户数)。指纹为空则不动既有 catalog_fingerprint。
    """
    prods = _sanitize_catalog(products, _PRODUCT_KEYS)
    custs = _sanitize_catalog(customers, _CUSTOMER_KEYS)
    fp = _sanitize_fingerprint(fingerprint)
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_endpoints
                SET config = COALESCE(config, '{}'::jsonb) || jsonb_build_object(
                        'reported_products', %s::jsonb,
                        'reported_customers', %s::jsonb,
                        'catalog_seen_at', to_jsonb(NOW()::text))
                    || CASE WHEN %s::jsonb = '{}'::jsonb THEN '{}'::jsonb
                            ELSE jsonb_build_object('catalog_fingerprint', %s::jsonb) END
                WHERE id = %s AND adapter = 'express'
                """,
                (
                    json.dumps(prods, ensure_ascii=False),
                    json.dumps(custs, ensure_ascii=False),
                    json.dumps(fp),
                    json.dumps(fp),
                    endpoint_id,
                ),
            )
        return (len(prods), len(custs))
    except Exception as e:
        logger.error(f"store_reported_catalog failed: {e}")
        return (0, 0)


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


def store_max_payload_version(endpoint_id: str, value: Any) -> bool:
    """存小助手心跳上报的【最高支持载荷版本】→ config.max_payload_version(整数)。

    preflight 拿它跟 common.PAYLOAD_VERSION 比:上报值更低 → 拦截该端点的推送(提示升级),
    避免推一份老小助手解析不了的新契约字段。非法值(非数字/<1)→ 不写,视同未上报。
    """
    try:
        n = int(value)
    except (TypeError, ValueError):
        return False
    if n < 1:
        return False
    return _merge_config(endpoint_id, {"max_payload_version": n})


def bump_stock_master_count(endpoint_id: str, created: int) -> bool:
    """推送真建出了 N 个库存主档 → 就地把指纹里的库存品数加上去。

    指纹由小助手心跳上报,但目录扫描节流到 30 分钟一次。采购刚把第一个库存品建出来、
    会计立刻重推销售票时,零主档闸读的还是旧指纹 → 又拦一次,人看到的是「补完了还是不让推」。
    ack 这里已经确知建了几个,当场加上,别让人等下一次目录上报。
    """
    if not created or created < 1:
        return False
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_endpoints
                SET config = jsonb_set(
                        COALESCE(config, '{}'::jsonb),
                        '{catalog_fingerprint,stock_master_count}',
                        to_jsonb(
                            COALESCE(
                                (config #>> '{catalog_fingerprint,stock_master_count}')::int, 0
                            ) + %s
                        ),
                        true
                    )
                WHERE id = %s AND adapter = 'express'
                """,
                (int(created), endpoint_id),
            )
        return True
    except Exception as e:
        logger.error(f"bump_stock_master_count failed: {e}")
        return False


def store_companion_version(endpoint_id: str, value: Any) -> bool:
    """存小助手心跳上报的自身版本号 → config.companion_version。

    小助手一直在心跳里发它,但此前只落进单次推送回执的 meta —— 于是「发版后在用的小助手
    有没有真更新到新版」在系统侧查不到,只能上机器看托盘。发版铁律的第三步因此每次都靠人肉。
    存进端点后 SELECT 一下就能答。形如 "1.1.51";脏值/超长不写,视同未上报。
    """
    v = str(value or "").strip()
    if not v or len(v) > 20:
        return False
    return _merge_config(endpoint_id, {"companion_version": v})


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


def touch_heartbeat(endpoint_id: str, device: str = "") -> None:
    """更新 config.agent_last_seen_at = NOW(UTC);附带本机名(供网页显示是哪台电脑在连)。

    一次 UPDATE 同时写 last_seen + agent_device_name(有 device 才写),不额外加写库次数。
    """
    try:
        from core import db

        if device:
            sql = """
                UPDATE erp_endpoints
                SET config = jsonb_set(
                        jsonb_set(COALESCE(config, '{}'::jsonb),
                                  '{agent_last_seen_at}', to_jsonb(NOW()::text), true),
                        '{agent_device_name}', to_jsonb(%s::text), true)
                WHERE id = %s AND adapter = 'express'
            """
            params = (device[:60], endpoint_id)
        else:
            sql = """
                UPDATE erp_endpoints
                SET config = jsonb_set(
                        COALESCE(config, '{}'::jsonb),
                        '{agent_last_seen_at}', to_jsonb(NOW()::text), true)
                WHERE id = %s AND adapter = 'express'
            """
            params = (endpoint_id,)
        with db.get_cursor(commit=True) as cur:
            cur.execute(sql, params)
    except Exception as e:
        logger.error(f"touch_heartbeat failed: {e}")
