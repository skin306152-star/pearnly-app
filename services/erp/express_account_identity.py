"""Express 账套身份:路径归一 + "数据目录 → 程序目录"配对(零重依赖的叶子模块)。

单独成模块是为了避开循环 import:services/erp/express_push/__init__.py 需要在模块顶层用
配对口径,而它被 services/erp/push_exception_classify 链引用;若从 express_target_projection
(该模块顶层 import core.db)取,就会绕回 push_exception_classify 自身的半初始化状态
(2026-09-18 实测:直接 import services.erp.push_exception_classify 会 ImportError)。
本模块只依赖 ntpath,谁都能安全引。
"""

from __future__ import annotations

import ntpath
from typing import Any, Mapping


def normalize_express_account_key(value: Any) -> str:
    raw = str(value or "").strip().replace("/", "\\").rstrip("\\")
    return ntpath.normcase(ntpath.normpath(raw))[:500] if raw else ""


def reported_account_set_roots(rows: Any) -> dict[str, str]:
    """账套配对(数据目录 → 程序目录)· 键与值都已 normalize_express_account_key。

    数据目录与程序目录是两个独立字段:事务所常把数据放在盘符(S:\\2569\\EXP69\\69SINCER),
    Express 程序却装在网络共享(\\\\accserver\\ACCOUNT\\69EXP)· 两者的字符串形态甚至可能不同
    (同一目录既可用映射盘符、也可用 UNC 描述)。所以只认上报里成对给出的 root,
    **绝不从数据目录的路径反推父目录** —— 反推出来的"上一层"跟程序目录不是一回事。

    兼容两种行形状:Agent 心跳的 {path, root} 与投影快照的 {source_id, attributes:{path, root}}。
    只给出数据目录、没给出程序目录的行不入表(caller 自己决定缺配对时是放行还是拦)。
    """
    roots: dict[str, str] = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, Mapping):
            continue
        attributes = row.get("attributes") if isinstance(row.get("attributes"), Mapping) else {}
        key = normalize_express_account_key(
            row.get("path") or attributes.get("path") or row.get("source_id")
        )
        root = normalize_express_account_key(row.get("root") or attributes.get("root"))
        if key and root:
            roots.setdefault(key, root)
    return roots


__all__ = ["normalize_express_account_key", "reported_account_set_roots"]
