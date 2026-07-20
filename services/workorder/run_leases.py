# -*- coding: utf-8 -*-
"""工单级独占操作租约 + 死亡判据 DAL(C-1 · MC2-0 · MC2-A1 · D6)。

work_orders 行上的 run_lease_owner / run_lease_expires_at 两列是「同一工单同一时刻只允许一个
长活操作在推进」的跨进程互斥锁,全部读写出口从 store.py 拆出(单文件 <500 铁律)——store 原样
re-export,调用方(runner/reaper/routes/bank_sales_brain)与既有测试的 `store.acquire_run_lease`
口径不变,实现单源在此。

谁会持约:① /run 引擎推进(runner,owner=进程标识);② bank_sales_brain 大脑批量分类
(owner 前缀 `bank_sales_brain:`)。D6 起大脑在工单 review/stuck 态也持约(复用 runner 空闲租约免
费得跨进程互斥),故「持约」不再等价于「status=running」——review 态存在合法的悬空租约。

租约协议:
  - 抢约(acquire)单句条件 UPDATE 原子判「无人持有 / 自己续租 / 过期接管」;抢不到 = 有人持
    未过期租约 → 调用方按 409 撞约让位(不裸奔双跑)。
  - 心跳(renew)只续自己 owner;释放(release)只放自己 owner;owner 已易主则都不动。
  - 收尸(list/claim)只认 status=running 的死租约(见 _DEAD_RUN_PREDICATE + 调用方注入的
    status);review/stuck 态的悬空租约不被 reaper 咬,靠 TTL 自然过期让位——大脑批量结束正常
    release,异常退出则租约过期后下一次抢约即接管。
"""

from __future__ import annotations

from typing import Optional

# 死亡判据 = status=running 的「活 run 却已失去有效租约」这条 reaper 收尸条件(MC2-0 + MC2-A1 F3),
# 与调用方注入的 status=running 联合成立(见 list_dead_runs / claim_dead_run),两支:
#   ① 租约已过期 —— 进程被杀(部署 SIGKILL)实锤;
#   ② 租约 NULL 且 updated_at 老于宽限 —— 翻了 running 却没抢到租约的孤儿(如调度被吞)。
# MC1-a 进程内崩溃路径自己落 run_failed + 状态离开 running,不落入本判据。
# review/stuck 态的大脑持约(D6)status 不是 running,天然不被本判据咬 → 只靠 TTL 过期。
# list 与 claim 必须同一判据:扫描命中而抢占谓词不认,孤儿永远收不走。
_DEAD_RUN_PREDICATE = (
    "((run_lease_expires_at IS NOT NULL AND run_lease_expires_at < now()) "
    "OR (run_lease_owner IS NULL AND run_lease_expires_at IS NULL "
    "AND updated_at < now() - make_interval(secs => %s)))"
)


def acquire_run_lease(
    cur, *, tenant_id: str, work_order_id: str, owner: str, ttl_seconds: int
) -> bool:
    """抢 /run 推进租约(单句条件 UPDATE,原子)。抢到返 True,被他人未过期租约占着返 False。

    可抢条件:无人持有 / 自己已持有(续租)/ 上一持有者租约已过期(接管)。过期由 now()
    与 run_lease_expires_at 比较判定,无需后台回收线程。双终端并发 /run 各自跑这条 UPDATE,
    Postgres 行锁串行化 → 恰一个 RETURNING 到行。
    """
    cur.execute(
        """
        UPDATE work_orders
           SET run_lease_owner = %s,
               run_lease_expires_at = now() + make_interval(secs => %s),
               updated_at = now()
         WHERE tenant_id = %s AND id = %s
           AND (run_lease_owner IS NULL
                OR run_lease_owner = %s
                OR run_lease_expires_at IS NULL
                OR run_lease_expires_at < now())
        RETURNING id
        """,
        (owner, int(ttl_seconds), tenant_id, work_order_id, owner),
    )
    return cur.fetchone() is not None


def renew_run_lease(
    cur, *, tenant_id: str, work_order_id: str, owner: str, ttl_seconds: int
) -> bool:
    """跑批心跳续约(MC2-A1 ④):只续自己仍持有的租约(条件 UPDATE),owner 已易主
    (被收尸人接管)则不续、返 False。逐件检查点提交时顺带调,超长合法跑批不再耗穿
    TTL 被跨 worker 误判为死;updated_at 同步刷新,孤儿宽限判据不误咬活 run。"""
    cur.execute(
        """
        UPDATE work_orders
           SET run_lease_expires_at = now() + make_interval(secs => %s),
               updated_at = now()
         WHERE tenant_id = %s AND id = %s AND run_lease_owner = %s
        RETURNING id
        """,
        (int(ttl_seconds), tenant_id, work_order_id, owner),
    )
    return cur.fetchone() is not None


def release_run_lease(cur, *, tenant_id: str, work_order_id: str, owner: str) -> None:
    """释放租约(仅当仍是自己持有——防误释放别人接管后的租约)。"""
    cur.execute(
        "UPDATE work_orders SET run_lease_owner = NULL, run_lease_expires_at = NULL, "
        "updated_at = now() WHERE tenant_id = %s AND id = %s AND run_lease_owner = %s",
        (tenant_id, work_order_id, owner),
    )


def run_lease_holder(cur, *, tenant_id: str, work_order_id: str) -> Optional[dict]:
    """当前有效租约(过期视为无);无 → None。观测/详情用,不参与抢占决策。"""
    cur.execute(
        "SELECT run_lease_owner, run_lease_expires_at FROM work_orders "
        "WHERE tenant_id = %s AND id = %s AND run_lease_owner IS NOT NULL "
        "AND (run_lease_expires_at IS NULL OR run_lease_expires_at > now())",
        (tenant_id, work_order_id),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def list_dead_runs(cur, *, status: str, orphan_grace_seconds: int, limit: int = 20) -> list[dict]:
    """收尸扫描(MC2-0):status(调用方传 engine.STATUS_RUNNING;engine→store 的 import
    方向不能反,状态词由调用方注入)且命中死亡判据(见 _DEAD_RUN_PREDICATE)。
    跨租户系统扫描,与 background_loops 其它恢复队列同口径。"""
    cur.execute(
        "SELECT id, tenant_id FROM work_orders "
        f"WHERE status = %s AND {_DEAD_RUN_PREDICATE} "
        "ORDER BY COALESCE(run_lease_expires_at, updated_at) LIMIT %s",
        (status, int(orphan_grace_seconds), limit),
    )
    return [dict(r) for r in cur.fetchall()]


def claim_dead_run(
    cur,
    *,
    tenant_id: str,
    work_order_id: str,
    owner: str,
    ttl_seconds: int,
    status: str,
    orphan_grace_seconds: int,
) -> bool:
    """收尸抢占(MC2-0):单句条件 UPDATE 重验死亡判据(与 list_dead_runs 同一谓词)并接管
    租约(照 acquire_run_lease 的接管先例)。多 worker 同时收尸,行锁串行化后恰一个
    RETURNING 到行;扫描与抢占之间判据若不再成立(别人已收/原单已推进),抢不到即放手。"""
    cur.execute(
        f"""
        UPDATE work_orders
           SET run_lease_owner = %s,
               run_lease_expires_at = now() + make_interval(secs => %s),
               updated_at = now()
         WHERE tenant_id = %s AND id = %s
           AND status = %s
           AND {_DEAD_RUN_PREDICATE}
        RETURNING id
        """,
        (owner, int(ttl_seconds), tenant_id, work_order_id, status, int(orphan_grace_seconds)),
    )
    return cur.fetchone() is not None
