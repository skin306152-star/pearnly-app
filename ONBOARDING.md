# Pearnly 项目入口

先读 [AGENTS.md](AGENTS.md)，然后按任务定位代码和文档。项目是 FastAPI、原生 JS/Vite 和 Supabase Postgres 应用，独立 ERPNext 与 Companion 使用各自仓库。

| 内容                     | 位置                                                                                            |
| ------------------------ | ----------------------------------------------------------------------------------------------- |
| API 与应用入口           | `app.py`、`routes/`                                                                             |
| 业务和共享基础设施       | `services/`、`core/`                                                                            |
| 前端源码与静态资源       | `src/`、`static/`，实际映射见前端技能                                                           |
| 本地开发与依赖           | [CONTRIBUTING](CONTRIBUTING.md)                                                                 |
| 业务词典与状态语义       | `docs/agent/BUSINESS_GLOSSARY.md`、`docs/agent/ERROR_CODES_AND_STATES.md`                       |
| 测试与机械检查           | `tests/`、[GATES](docs/GATES.md)、[VERIFICATION](docs/agent/VERIFICATION.md)                    |
| 按需开发技能             | `.agents/skills/`                                                                               |
| 业务规格、设计和历史记录 | `docs/project/`                                                                                 |
| 生产运行状态与发布       | [部署账本](docs/deployment/MIGRATION_STATUS.md)、[Cloud Run 规范](docs/deployment/CLOUD_RUN.md) |

本地使用仓库虚拟环境和已锁定依赖。凭据留在本机配置中，不写进代码或交接；数据库测试遵循 `tests/integration/README.md` 的隔离要求。

以当前用户任务决定工作范围。重构主计划、历史规模数字和旧状态卡仅在调查相关事项时查阅，不要求新窗口执行历史主线。

换电脑时按 [Codex 换机恢复](docs/codex/README.md) 恢复全局协作约定和实验性上下文设置。
