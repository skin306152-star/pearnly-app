# -*- coding: utf-8 -*-
"""智能管家(B2-M1)· /ai 顶部对话入口的后端。

分层(照 front_desk / agent 先例,每层单一职责):
  registry.py     工具注册表(闭集)+ 工具执行上下文
  tools.py        六个只读工具实现 —— 一律薄封装既有服务层,零新 SQL
  planner.py      大脑层:一句话 → 闭集里的一个工具 + 参数(降级信封 fail-closed)
  orchestrator.py 单轮编排:计划 → 参数接地 → 入队 → 应承答复(追问仍同步)
  worker.py       后台工人:认领 steward_tasks 队列 → 真跑工具 → 收尾 + 回话(B3 异步)
  copy.py         答复/步骤的 zh+th 文案(数字全部来自工具返回,模板不做任何计算)
  store.py        会话/消息/任务三表 DAL(RLS 按 tenant;steward_tasks 兼作队列)

闸(pearnly_ai_steward · tenant 级 · 默认关)读的是 platform_settings,那层有 30s 进程内
TTL 缓存(services/platform_settings/store._CACHE_TTL_S):超管在后台开闸后,每个 web 进程
最迟 30s 才看得到,多 worker 各自到点收敛。验收时刷新页面没出管家先等半分钟再报障。
"""
