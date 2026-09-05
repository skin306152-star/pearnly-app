# 当前任务交接入口

开发约定见 [AGENTS.md](AGENTS.md)。续接任务时先核对当前用户要求、分支和工作区，再读取该任务的证据与未完成事项；需要项目状态时查看 [状态记录](docs/project/STATE_PEARNLY.md)。

发布操作遵循 [Cloud Run 规范](docs/deployment/CLOUD_RUN.md)，实际线上版本与验收状态以 [部署账本](docs/deployment/MIGRATION_STATUS.md) 为准。仅在任务包含发布时执行，回读精确 SHA、镜像 digest、revision、流量和正式域名结果。

历史银行对账记录保存在 [M4 归档](docs/archive/HANDOFF-2026-05-23-银行对账M4-收尾.md)，不作为当前流程。用户不需要自己 push；任务已授权的必要操作由执行者完成，不从历史文档推导额外授权。
