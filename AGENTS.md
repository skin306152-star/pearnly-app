# Pearnly 开发约定

本仓库是 FastAPI、原生 JS/Vite、Supabase Postgres 的多入口应用；独立 ERPNext 与 Companion 仓库有各自的开发和发布流程。
按用户当前任务开工。历史主线、旧交接和示例不构成新任务，也不授权自动推送、发布或写入外部系统。

## 开工与范围

- 查看当前分支和 `git status`，保护其他任务的文件、暂存内容和工作树。跨文件修改使用隔离工作树，只提交自己的路径。
- 按需读代码与下列文档；仅在续接相关任务时读 `docs/project/STATE_PEARNLY.md` 或该任务交接。只有调查代码规模/重构进度时才运行 `scripts/refactor_progress.py`。
- 需求明确时直接实施；产品方案尚有关键分歧时先澄清。项目工作流不强制指定模型、外派代理或重复审查。
- 本仓库 Python 优先使用 `venv/bin/python`（或 `.venv/bin/python`），Windows 使用对应 `Scripts` 路径。不要根据系统 `python3` 缺包认定项目依赖损坏。

## 业务与实现边界

- `workspace_client_id` 是账套主体，`history.client_id` 是发票买方，不能混用。多租户查询和写入保持服务端权限与租户隔离。
- ERP 推送状态以 `erp_push_logs` 为唯一来源；`rows=0`、`needs_mapping`、`failed`、`blocked`、`retrying` 不显示为完成。HTTP 200 不能证明外部 ERP 已写入。
- 金额用 `Decimal`，时间存 UTC，SQL 参数化；写操作保持幂等和必要审计。测试不触碰真实付费用户余额，不往真实账套写测试单据。
- `db.get_cursor()` 的 DDL 需要显式提交；后端响应字段变化同步检查 Pydantic `response_model`。Cloud Run schema 初始化由发布流程串行执行，不擅自运行 `alembic upgrade` 或用单机锁协调实例。
- 新业务放 `services/<领域>/`，新路由放 `routes/`；保持现有模块边界，避免把新逻辑堆进巨石。源码大小、棘轮、格式等以现有机械闸为准。
- 前端先核对实际路由与源文件；由构建生成的 HTML/JS/CSS 要更新对应产物并同批提交，受影响缓存引用同步更新，保持原文件编码和换行。
- 真实导入样本、账套映射和人工核对边界见业务词典与 ERP 集成技能；不以模糊归一化替代用户会计判断。

## 验证与发布

- 日常按影响面验证，参见 [验证与证据](docs/agent/VERIFICATION.md)。同一份检查结果可复用；无新变化不在开工、收尾、提交时手动重复全套。
- 提交/推送保留现有闸门，命令与触发条件见 [GATES](docs/GATES.md)。发布前完成候选版本要求的检查，不绕过钩子、不放宽失败条件。
- 提交使用真实作者身份，不添加工具或模型的联合署名。
- 部署操作只使用 [Cloud Run 规范](docs/deployment/CLOUD_RUN.md)，实际状态看 [部署账本](docs/deployment/MIGRATION_STATUS.md)。旧 Vultr/SSH/systemd 发布已退役；旧工作树缺少新发布文件时，先同步迁移改动，不能用旧流程发布。
- 只有任务包含发布时才执行发布流程。文档或开发工具改动不需要重发业务容器；本地检查、上线身份、外部系统结果和用户真机验收分别报告。

## 按需技能与文档

技能正文维护在 `.agents/skills/`，仅在任务匹配时读取。

- 前端页面或用户可见文案：[frontend-change](.agents/skills/frontend-change/SKILL.md)，包含路由地图和多语言参考。
- 外部 ERP、导入模板、Companion：[erp-integration](.agents/skills/erp-integration/SKILL.md)。
- 发布候选、部署与回退：[deploy-release](.agents/skills/deploy-release/SKILL.md)。
- 生产报错与线上版本排查：[debug-prod-500](.agents/skills/debug-prod-500/SKILL.md)，默认只读诊断。
- 业务字段：[业务词典](docs/agent/BUSINESS_GLOSSARY.md)；状态语义：[错误与状态](docs/agent/ERROR_CODES_AND_STATES.md)；工程质量：[工程标准](docs/ENGINEERING_STANDARD.md)。
- 需要产品方案时读 [任务范围与产品设计](docs/agent/TASK_MODES.md)，不把 discovery 套在每次小修上。

## 交接

长任务或用户要求收尾时记录目标、当前分支/SHA、已验证证据、剩余事项与下一步；更新本任务的记录，避免覆盖其他窗口的状态卡。
收尾不自动扩展审查或延后已授权的必要修复。仅回收本次创建的临时文件、进程和工作树；数据、共享依赖和他人改动保留。
