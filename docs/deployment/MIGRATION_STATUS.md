# Pearnly 部署与迁移状态账本

更新时间：2026-09-05。状态：**迁移施工中，尚未确认 Cloud Run 接管生产**。
本文件是部署状态唯一正本；[CLOUD_RUN.md](CLOUD_RUN.md) 是目标设计和发布规范。历史 STATE、RUNBOOK、聊天截图中的“当前”不覆盖本页。每次发布、切流或回退必须重写本页当前状态并追加证据。

## 当前确认与边界

| 项目 | 当前记录 | 证据/限制 |
|---|---|---|
| 旧 Pearnly 生产 | Vultr `66.42.49.213`，`/opt/mrpilot`，systemd `mrpilot`，SHA `776808e7` | 迁移主控提供的施工基线；切流前须再次实时回读完整 SHA |
| 新 Pearnly 项目 | GCP `pearnly` / `112074003592`，`asia-southeast1` | 不代表服务已部署 |
| 新 Web / Worker | 计划 `pearnly-web` / `pearnly-worker` | revision、digest、URL、流量验证待登记 |
| 正式域名 | `pearnly.com` 继续由 Cloudflare 管理 | Cloud Run 接管尚无证据；不要根据目标架构断言 DNS 已切换 |
| 数据库 | 现有 Supabase PostgreSQL 保持 | 不搬到 ERPNext，不用 MariaDB 替换 |
| 文件 | 计划迁入私有 GCS | 对象清单、完整性、增量同步与读取验证待登记 |
| ERPNext | 独立仓库 `/Users/skin/pearnly-erp`、GCP `project-d0fbd530-1ee3-436d-b58` | 本次不修改；不把该 VM 当作待退役 Vultr |
| 旧实例退役 | 尚未确认停用或销毁 | 不得声称已停止计费；删除前保留迁移与恢复证据 |
| 用户验收 | 未完成 | 不标记 `USER_ACCEPTED` |

## 切流前待完成

- Cloud Run 运行改造与对应本地/容器验证；启动、schema、持久文件和后台任务跨实例安全。
- GitHub WIF、Artifact Registry、Secret Manager、独立运行账号、Tasks/Scheduler 与存储实际配置回读。
- 精确 SHA 镜像发布；记录完整 SHA、digest、Web/Worker revision、服务 URL 和 workflow run。
- 文件初拷及最后增量核验；旧调度器与在途任务交接；新任务幂等和重试验证。
- 正式域名切换、新站关键路径验收和回退材料；旧发布入口禁用回读。
- 监控/费用告警与实际资源配置回读；旧实例停用/保留/销毁状态及用户真机验收分别记录。

## 证据记录格式

每条记录包含时间（注明时区）、执行动作、项目/区域、候选完整 SHA、workflow run、镜像 digest、revision/流量、实际检查结果及未覆盖范围。秘钥与用户原始资料不写入本文件。失败或未执行保持明确状态，不以“已配置”代替“已运行”。

### 2026-09-05：开始迁移

用户授权迁移 Pearnly 应用并同步开发入口，ERPNext 保持现状。主控建立隔离 worktree；本账本先记录旧生产基线和待验收目标，等待真实部署与切流证据后更新。
