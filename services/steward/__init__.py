# -*- coding: utf-8 -*-
"""智能管家(B2-M1)· /ai 顶部对话入口的后端。

分层(照 front_desk / agent 先例,每层单一职责):
  registry.py     工具注册表(闭集)+ 工具执行上下文
  tools.py        六个只读工具实现 —— 一律薄封装既有服务层,零新 SQL
  planner.py      大脑层:一句话 → 闭集里的一个工具 + 参数(降级信封 fail-closed)
  orchestrator.py 单轮编排:计划 → 参数接地 → 执行 → 任务落库 → 答复
  copy.py         答复/步骤的 zh+th 文案(数字全部来自工具返回,模板不做任何计算)
  store.py        会话/消息/任务三表 DAL(RLS 按 tenant)
"""
