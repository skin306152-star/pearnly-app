# -*- coding: utf-8 -*-
"""LINE 待问客户池的唯一词汇表(纯常量叶子模块 · 照 services/workorder/decisions.py 范式)。

状态字符串 / question_type / 状态跳转合法性——D2 方案 §0 状态机 + §2.3 schema 的单一事实源。
S3 起及以后各单(push/answer/dunning/自动关闭)一律 import 本模块取词,绝不散抄字面量
(C4 血泪:改一处漏改另一处)。

零依赖:不 import 任何本包模块,避免循环导入。裁决状态词(assign_kind/recalc/...)不在此重造,
仍照旧 import services.workorder.decisions(方案 §2.3 明载)。
"""

from __future__ import annotations

# 六态状态机(D2 方案 §0)。三终态之外无悬空:APPLIED / RESOLVED_INTERNALLY / CANCELLED。
STAGED = "staged"  # 暂挂草稿·已归集入池·未推送
PENDING = "pending"  # 已推送客户·等回答(跨月留存态)
MANUAL_REVIEW = "manual_review"  # 客户答了但机器不敢判·过渡态
APPLIED = "applied"  # 回写已改判(终态)
RESOLVED_INTERNALLY = "resolved_internally"  # 内部已解决·不等客户了(终态)
CANCELLED = "cancelled"  # 撤回 / 作废(终态)

# active = 还在池里占位、防同票重复轰炸客户的三态(对应 uq_lcq_active_item 部分唯一索引)。
ACTIVE_STATUSES = frozenset({STAGED, PENDING, MANUAL_REVIEW})
# 终态三选一,落地即封口,不再流动。
TERMINAL_STATUSES = frozenset({APPLIED, RESOLVED_INTERNALLY, CANCELLED})
ALL_STATUSES = ACTIVE_STATUSES | TERMINAL_STATUSES

# 状态跳转合法性表(§7.2 S3 断言:表驱动,非法跳转结构化拒)。
# staged→pending/cancelled;pending→manual_review/applied/resolved_internally/cancelled/staged
# (推送失败回退);manual_review→applied/cancelled;终态不出。
LEGAL_TRANSITIONS: dict[str, frozenset[str]] = {
    STAGED: frozenset({PENDING, CANCELLED}),
    PENDING: frozenset({MANUAL_REVIEW, APPLIED, RESOLVED_INTERNALLY, CANCELLED, STAGED}),
    MANUAL_REVIEW: frozenset({APPLIED, CANCELLED}),
    APPLIED: frozenset(),
    RESOLVED_INTERNALLY: frozenset(),
    CANCELLED: frozenset(),
}

# 问题类型(D2 方案 §2.3 · §4.1 裁决通道映射键)。
QUESTION_DIRECTION = "direction"  # 买/卖不明 → assign_kind
QUESTION_AMOUNT = "amount"  # 票面金额存疑 → recalc
QUESTION_DROP = "drop"  # 该不该计入这月 → exclude
QUESTION_FREEFORM = "freeform"  # 任意自由文本 → 不自动回写,恒交人审
QUESTION_TYPES = (QUESTION_DIRECTION, QUESTION_AMOUNT, QUESTION_DROP, QUESTION_FREEFORM)


def is_legal_transition(from_status: str, to_status: str) -> bool:
    """状态跳转是否合法(表驱动 · 未知 from_status 一律非法,不猜)。"""
    return to_status in LEGAL_TRANSITIONS.get(from_status, frozenset())
