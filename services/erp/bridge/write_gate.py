# -*- coding: utf-8 -*-
"""桥写路的云端闸:job kind 白名单 + 写桥角色闸 + 写桥挑选。

从 store.py 拆出(体积闸 <500 行):store 管任务信箱的增删查,写路特有的判定住这里。
写活在桥端 = 备份账套 → 写 DBF → 重建 CDX,全程跨 SMB,比一次查询慢一个量级,
租约与排队超龄单独放宽,常量归这里,store 的 lease SQL 按 kind 取用。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from services.erp.bridge import BridgeRejected, BridgeUnavailable
from services.erp.bridge.schema import BRIDGES, JOBS, heal

logger = logging.getLogger(__name__)

JOB_KINDS = ("query", "write")
KIND_WRITE = "write"

# 「知道了,还是推」的载荷位(桥 writepath/duplicate_gate.CONFIRM_PARAM)。它关掉的正是桥端
# 写侧那道「同 ref_no + 对手方码就当重投」的幂等闸,所以带这一位的写活不能享受「租约过期退回
# 队列」——退回去再派一次就是账上再多一张,而一次真写(备份→写 DBF→重建 CDX)是分钟级,
# 租约 300s 罩不住慢盘。判真值取「有这个键且不是明摆着的假」:宁可把不确定的也按至多一次
# 处置,也不能漏判一个真确认。
_CONFIRMED = (
    "lower(coalesce(payload->>'duplicate_confirmed', 'false')) "
    "NOT IN ('false', '0', '', 'null', 'no', 'off')"
)
# 领走了没回结果的确认写活落这个码。状态仍取 expired 而非 failed:桥可能已经写完只是回执丢了,
# finish_job 对 expired 的写活会收下迟到的 result(里面的 docnum 是改票号重推时防重单链的唯一
# 钥匙)。码另开一个,是因为「没人来领」与「领了没回」该跟会计说的话正相反 —— 前者可以放心
# 再说一次,后者绝不能(见 services/steward/copy_erp_push)。
CONFIRMED_UNACKED_CODE = "bridge.confirmed_write_unacked"

# 写活租约/超龄:跨 SMB 的备份+写+CDX 重建是分钟级(查询 60/120 秒不动)。
# 租约 300s = 桥崩溃后写活最多压 5 分钟才退回队列;超龄 600s = 排队半天没桥领,
# 结果没人等了,诚实落 expired 而不是突然写进账套吓会计一跳。
# ⚠️ expired 只对「从没被领走」的写活保证没写进账套:被领走后租约被回收再超龄落
# expired 的单,桥仍可能写完迟到 ack —— 结果照落库(store.finish_job),对账认
# result 里的 docnum,别把 expired 一律当「没推进去」展示给会计。
WRITE_LEASE_SECONDS = 300
WRITE_JOB_TTL_SECONDS = 600


def close_unacked_confirmed_writes(cur, bridge_id: str) -> int:
    """确认放行的写活领走后没回结果、租约已过期 → 落 expired,**不退回队列**(至多一次)。

    必须排在「租约过期退回队列」那一句之前:它一旦把这类活改回 queued,下一拍就又派出去了。
    这里说的是实话 —— 系统分不出桥是没写还是写完丢了回执,分不出就交给会计去 Express 看。
    返回被收尾的活数。
    """
    error = json.dumps(
        {
            "code": CONFIRMED_UNACKED_CODE,
            "message": "确认放行的写单被领走后没回结果:可能已写进账套,也可能没有",
        },
        ensure_ascii=False,
    )
    cur.execute(
        f"UPDATE {JOBS} SET status = 'expired', finished_at = now(), error = %s, "
        "lease_owner = NULL, lease_expires_at = NULL "
        f"WHERE bridge_id = %s AND status = 'leased' AND kind = %s AND {_CONFIRMED} "
        "AND lease_expires_at < now()",
        (error, bridge_id, KIND_WRITE),
    )
    if cur.rowcount:
        logger.warning(
            "确认写活租约过期未回执 · 已落 expired 待人工核对: bridge=%s n=%d",
            bridge_id[:8],
            cur.rowcount,
        )
    return cur.rowcount


def assert_enqueue_allowed(bridge: Dict[str, Any], kind: str) -> None:
    """入队前两道闸:kind 白名单 + 写活只投 effective_role=write 的桥。

    看 effective_role 不看 role:role 是桥的自述,effective_role 才是唯一闸
    (register_hello)判过的生效角色 —— 被降级的写桥必须在入队口就被拒,
    否则双写从这里漏进账套。
    """
    if kind not in JOB_KINDS:
        raise BridgeRejected(f"未知 job kind: {kind!r}", "bridge.bad_kind")
    if kind == KIND_WRITE and bridge.get("effective_role") != "write":
        raise BridgeRejected(
            f"目标桥不是生效写桥(effective_role={bridge.get('effective_role')!r})",
            "bridge.write_role_required",
        )


def leasable_kinds(bridge: Dict[str, Any]) -> List[str]:
    """本桥可领的 kind 集合 —— lease 侧兜底,放这里(派发口)而不是别处:

    hello 后被唯一闸降级为 read 的桥,队列里可能还躺着降级前投进来的写活;
    lease 每拍都重新鉴权拿最新桥行,按 effective_role 现算可领集合 ——
    写活绝不派给非写桥,留给真写桥来领,或到 WRITE_JOB_TTL_SECONDS 诚实落 expired。
    """
    if bridge.get("effective_role") == "write":
        return list(JOB_KINDS)
    return [k for k in JOB_KINDS if k != KIND_WRITE]


def pick_write_bridge(tenant_id: str, book_id: str) -> Dict[str, Any]:
    """挑能写这个账套的在线写桥;挑不到抛 BridgeUnavailable。

    只认 effective_role=write + 在线 + book_id 在其上报清单内。唯一闸保证同账套
    同时刻至多一个在线写桥,ORDER BY 只是并列时的确定性兜底。
    store 在函数内才 import:store 模块级引用本文件的常量,反向必须延迟否则成环。
    """
    from core import db
    from services.erp.bridge import store

    def _run():
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                f"SELECT * FROM {BRIDGES} WHERE tenant_id = %s AND effective_role = 'write' "
                "AND last_seen_at > now() - make_interval(secs => %s) "
                "ORDER BY last_seen_at DESC",
                (str(tenant_id), store.ONLINE_WINDOW_SECONDS),
            )
            rows = [dict(r) for r in (cur.fetchall() or [])]
        for row in rows:
            if str(book_id) in store.book_ids(row.get("books")):
                return row
        return None

    bridge = heal(_run)
    if bridge is None:
        raise BridgeUnavailable(f"该账套当前没有在线写桥: {book_id}")
    return bridge
