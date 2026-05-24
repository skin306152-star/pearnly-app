# -*- coding: utf-8 -*-
"""
对账异步任务系统(ADR-005 · BUG-FIX-RECON-ASYNC)。

三个对账(银行/收入/销项税)共用的"订单号 + 队列 + 进度"层:
  store.py  · recon_jobs 表的 DB 访问(enqueue / claim SKIP LOCKED / 进度 / 完成 / 回收)

结果仍写现有结果表 · 本层只管状态调度。详见 docs/refactor/adr-005-recon-async-jobs.md。
"""
