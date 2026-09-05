---
name: deploy-release
description: 准备或执行 Pearnly 发布候选、Cloud Run 部署、切流或回退时，检查精确版本、迁移与验收证据。
---

# Pearnly 发布

先读 `docs/deployment/MIGRATION_STATUS.md` 确认实际状态，再按 `docs/deployment/CLOUD_RUN.md` 的当前流程操作。本技能不复制主机命令、资源名称或易过期的部署 SHA。

- 按任务授权准备或执行发布；单纯诊断、文档与开发工具变更不自动触发业务发布。独立 ERPNext 与 Companion 仓库不随本仓部署改变。
- 保留本地风险分层检查与 pre-push；候选必须是明确的完整 SHA，前端构建产物和相关缓存引用一致。只暂存本任务路径，使用与实际改动一致的 Conventional Commit，不伪造模型署名。
- 发布使用 Cloud Run 的不可变镜像 digest、revision 与流量回读。旧 SSH/systemd、git-deploy.sh 和旧 webhook 发布流程已退役。
- schema 初始化按部署正本串行执行；保持持久数据、调度器归属和幂等，避免双份后台消费者。不得用单机文件锁协调实例。
- 回读 Web/Worker 的镜像 digest、revision、流量和 readiness；正式域名版本与目标 SHA 对齐后，验证本次涉及的网页、LINE、附件、队列及外部 ERP 结果。
- workflow 绿、HTTP 200、外部业务成功和用户真机确认分别记录，详见 `docs/agent/VERIFICATION.md`。文档 HEAD 晚于线上镜像不意味着需要重发容器。
- 回退使用与数据库/文件兼容且已验证的 revision；数据恢复需要配套备份，不能只换旧镜像。失败时报告实际状态，按部署正本恢复。
- 实际发布、切流或回退后更新部署账本和本任务交接；不覆盖其他窗口的状态。已退役的 release_notes 横幅不再要求四语发布说明，用户可见文案仍按多语言契约维护。
