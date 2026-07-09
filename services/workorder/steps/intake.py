# -*- coding: utf-8 -*-
"""intake 步:把调用方给的文件清单登记成 work_order_items(任务包 §5 步 1)。

输入契约:ctx.data["intake_files"] = 文件清单,每项是路径字符串或 {"path", "source"}
(source 缺省 upload;CLI T7 扫语料目录后按此契约喂入)。清单缺失/为空/有文件不存在
一律 needs(缺料,人补齐后续跑),不登记半截。

dedupe 指纹分两层名字空间:intake 只认文件本身 → `file:` + 字节 sha256,同一份文件
重复登记(重跑/清单重复)靠 store.add_item 的 upsert 收敛成一行;票面级指纹
(税号|票号|金额,复用 services/purchase/totals.dedupe_key,`doc:` 前缀)要等 OCR 出
字段才算得出,归 classify 步管重复票判定。
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from services.workorder.engine import StepContext, StepResult

_DEFAULT_SOURCE = "upload"


def _normalize_specs(raw) -> list[tuple[Path, str]]:
    specs = []
    for entry in raw or []:
        if isinstance(entry, dict):
            specs.append((Path(entry["path"]), entry.get("source") or _DEFAULT_SOURCE))
        else:
            specs.append((Path(entry), _DEFAULT_SOURCE))
    return specs


def run(ctx: StepContext) -> StepResult:
    """登记全部来料。幂等:同文件(同字节)重跑不重复登记。"""
    specs = _normalize_specs(ctx.data.get("intake_files"))
    if not specs:
        return StepResult.needs(["intake_files"])

    missing = [f"file_missing:{p.name}" for p, _ in specs if not p.is_file()]
    if missing:
        return StepResult.needs(missing)

    fingerprints = set()
    for path, source in specs:
        digest = "file:" + hashlib.sha256(path.read_bytes()).hexdigest()
        ctx.store.add_item(
            ctx.cur,
            tenant_id=ctx.tenant_id,
            work_order_id=ctx.work_order_id,
            source=source,
            file_ref=str(path),
            dedupe_key=digest,
        )
        fingerprints.add(digest)
    return StepResult.ok(items_registered=len(fingerprints))
