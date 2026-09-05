---
name: debug-prod-500
description: 只读排查 Pearnly 生产报错、上传或 ERP 推送失败、线上版本未生效，定位 Cloudflare、Cloud Run Web/Worker 和依赖的因果链。
---

# 生产诊断

“查日志/什么原因”先给只读诊断。先读 `docs/deployment/MIGRATION_STATUS.md`，再按 `docs/RUNBOOK.md` 与 `docs/deployment/CLOUD_RUN.md` 获取当前环境的日志和版本信息。

- 定位时间范围、请求/任务标识与受影响入口；回读实际 revision、镜像 digest、流量及正式域名版本，避免拿本地 HEAD 推断线上代码。
- 沿实际请求链检查 Cloudflare、Web、Worker、队列与数据库/外部 ERP。请求未到 Worker 时检查 Web 转发、IAM 和网络；HTML 错误页不直接归因磁盘满，500 也不能单独排除下游超时。
- 查 Cloud Run 日志中的具体异常、内存/实例退出、GCS 挂载与依赖失败，和同时间请求对应。旧 Vultr 已退役，不连接旧 IP、SSH 别名或查询 systemd。
- 数据库/ERP 查询保持只读并限定范围；错误响应不进入成功缓存。不要打印凭据、连接串或完整客户单据。
- 输出可证实的因果链、影响范围、缺失证据和最小修复建议。只有任务已授权修复时才修改或重启；单纯查日志不自动清理磁盘、重发任务或改数据。
- 修复时用受影响的真实路径验证；涉及 SQL/异步/外部 ERP 时按 `docs/agent/VERIFICATION.md` 选择检查。发布后验证的是 Cloud Run revision 和实际业务结果。
