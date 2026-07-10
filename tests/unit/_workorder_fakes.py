#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/_workorder_fakes.py

工单内存 store 替身共享基类:add_item(幂等镜像 pg store 的 dedupe_key 复用)+
append_event(seq 递增造事件行)。此前 test_workorder_api.py 的 _FakeStore 与
test_workorder_sales_summary.py 的 _RecordingStore 逐字重复这两个方法,收到这里。

两处对「新增事件落哪」需求不同,故只共享构造事件行的机械部分,落点留给子类:
_FakeStore 把预置夹具(self.events)与新增记录(self.appended)分两个桶,方便单独断言
record_decision/record_sales_summary 具体 append 了什么;_RecordingStore 需要
reconcile.run() 经 list_events() 立刻看到新增事件(回放解锁验证),故新增即并入同一条流。
下划线开头文件名 · unittest discovery 不收本文件当测试模块。
"""

from __future__ import annotations


class WorkOrderFakeStoreBase:
    """add_item/append_event 的共享核心。子类补 __init__ 的其余字段 + _on_event_appended。"""

    def __init__(self):
        self.items = []
        self._seq = 0

    def add_item(
        self,
        cur,
        *,
        tenant_id,
        work_order_id,
        source,
        kind="unknown",
        file_ref=None,
        original_name=None,
        ocr_history_id=None,
        status="pending",
        flag_reason=None,
        dedupe_key=None,
    ):
        # 幂等镜像 store.add_item:同 (work_order_id, dedupe_key) 复用既有 item(重填不新增)。
        if dedupe_key is not None:
            for i in self.items:
                if i["work_order_id"] == work_order_id and i.get("dedupe_key") == dedupe_key:
                    return dict(i)
        self._seq += 1
        row = {
            "id": f"item-{self._seq}",
            "work_order_id": work_order_id,
            "source": source,
            "kind": kind,
            "file_ref": file_ref,
            "original_name": original_name,
            "status": status,
            "flag_reason": flag_reason,
            "dedupe_key": dedupe_key,
        }
        self.items.append(row)
        return dict(row)

    def append_event(
        self, cur, *, tenant_id, work_order_id, step, event_type, payload=None, actor="system"
    ):
        self._seq += 1
        row = {
            "id": self._seq,
            "step": step,
            "event_type": event_type,
            "payload": payload or {},
            "actor": actor,
        }
        self._on_event_appended(row)
        return dict(row)

    def _on_event_appended(self, row):
        raise NotImplementedError
