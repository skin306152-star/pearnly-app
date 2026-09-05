# Pearnly 部署与迁移状态账本

更新时间：2026-09-05（Asia/Bangkok，UTC+7）。状态：**Cloud Run 已接管正式域名；启动状态检查修复与最终验收收尾中**。
本文件是部署状态唯一正本；[CLOUD_RUN.md](CLOUD_RUN.md) 是操作规范。历史 STATE、RUNBOOK 和聊天中的“当前部署”不覆盖本页。每次发布、切流或回退须更新本页；不把配置完成当作已运行或用户验收。

## 当前部署

| 部分 | 已回读的实际状态 |
|---|---|
| Pearnly 源码 | `skin306152-star/pearnly-app`；日常目录 `/Users/skin/Developer/Pearnly/pearnly-app` |
| Pearnly 云项目 | GCP `pearnly` / `112074003592`，新加坡 `asia-southeast1` |
| 正式域名 | `pearnly.com`、`www.pearnly.com` → Cloudflare Worker `pearnly-cloud-run` → Cloud Run Web；不使用 Google 负载均衡器 |
| Web | `pearnly-web`，1 vCPU / 1 GiB，min=0 / max=2，实例并发4，超时1800秒，公开入口 |
| Worker | `pearnly-worker`，1 vCPU / 2 GiB，min=0 / max=2，实例并发1，超时1800秒，IAM 私有入口 |
| 数据库 | 原 Supabase PostgreSQL 保持；业务数据、JWT 与文件加密配置沿用。发布 Job 执行兼容性 schema 初始化 |
| AI | Vertex AI 保持项目 `pearnly`、区域 `asia-southeast1` |
| 文件 | 私有 GCS 文件、临时文件、安装包分桶；临时文件7天过期；原访问权限/加密语义保留 |
| 后台派发 | Cloud Tasks `pearnly-background`，每秒最多1次派发、并行派发1、最多5次尝试；应用有幂等回执及不确定状态 |
| 周期任务 | Scheduler `pearnly-background-recovery`，每5分钟调用私有 Worker recovery；状态 ENABLED，实际执行成功 |
| 密钥和账号 | Secret Manager `pearnly-web-env` / `pearnly-worker-env`；各自独立运行账号，只读取各自密钥 |
| 发布 | GitHub `Manual CD`（当前 `manual-deploy.yml`）→ WIF → Artifact Registry → schema Job → 候选验证 → 两服务切流 |
| 旧 Vultr | `66.42.49.213` 的 `mrpilot` 已停止且禁用开机自启；实例尚未 Destroy，**仍计费** |
| ERPNext | 独立仓库 `/Users/skin/pearnly-erp`，GCP `project-d0fbd530-1ee3-436d-b58`，VM `pearnly-erp-dev`；只读回查 RUNNING，本次未修改 |

Web 使用1 GiB而非早期讨论的512 MiB，max=2而非3；是开发阶段保守配置。min=0允许空闲缩零，并不保证请求结束立即归零；正在运行的小助手轮询和定时探针仍会产生调用。

## 正在服务的发布身份

- 完整 SHA：`c3797e18278559f7ae9fa6ba88e07aadd759db52`。
- 镜像：`asia-southeast1-docker.pkg.dev/pearnly/pearnly-app/app@sha256:1c4a43f58fa6723e775abe71e839da59770260989907d04deda190e14f0779f0`。
- Web revision：`pearnly-web-c3797e182785-s1`，100%流量；Worker revision：`pearnly-worker-c3797e182785-s1`，100%流量。
- [成功的 GitHub 发布运行 33954963112](https://github.com/skin306152-star/pearnly-app/actions/runs/33954963112)。schema execution `pearnly-schema-98hsn` 成功，使用同一精确镜像。
- 服务地址：`https://pearnly-web-112074003592.asia-southeast1.run.app`；私有 Worker `https://pearnly-worker-112074003592.asia-southeast1.run.app`。
- 2026-09-05 15:28 左右切流。正式域名 readiness nonce `cutover-20260905-0828` 的 Cloud Run 请求日志确认命中新 Web revision，HTTP 200；www health 也为200。
- 当前待修：将 DDL 移至 schema Job 后，四项 Express 进程内 schema-ready 状态未恢复。无效小助手 heartbeat 从旧环境401变为503；不算验收成功，必须补齐只读启动校验再发布。

## 域名与旧发布入口

Cloudflare Worker 两条 route 为 `pearnly.com/*` 和 `www.pearnly.com/*`，均 fail closed。没有新增 `*.pearnly.com/*`，避免接管其他租户子域名。源站在 Worker 中明确指定 Cloud Run Web。

2026-09-05 DNS 回读：主域名由旧 A `66.42.49.213` 改成 proxied CNAME `pearnly-web-112074003592.asia-southeast1.run.app`；www 保持 proxied CNAME `pearnly.com`。原有 MX、SPF、DKIM 保留。旧 IP 不再是网站 DNS 源站。

旧 GitHub webhook `625195648`（`/internal/deploy`）已 inactive；Cloudflare 阻断 `/internal/`，新应用也不提供旧 VM 发布路径。旧 systemd 不得自行重启；不要同时运行两套周期消费者。

## 数据与恢复证据

- 旧应用停用后，本地源文件与 GCS **1448个业务文件逐一 MD5 核对，0不一致**；最终 rsync 因重复复制已相同对象被中断，以独立完整哈希复核为准。
- 安装包 `PearnlyCompanion-Setup.exe` 为62,905,102字节，云端 MD5 与源文件一致；latest.json 可从正式域名读取。
- Supabase 初始备份 `supabase-before.dump` 4,518,313字节，SHA256 `69dbb6d5c80c38397f4bdb9213d044cccb220aaca96a0380e96ed0395e7c92cd`；在隔离 PostgreSQL17+pgvector 容器中严格恢复 public schema/数据并执行新 schema 成功。5张原有零策略 RLS 表保持启用，未为迁移全局关闭 RLS。
- 切流前另存 `supabase-pre-cutover.dump`（4,518,312字节）；已上传。恢复试验针对初始备份，未把第二份声称为另一次完整恢复试验。
- 完整旧文件归档 `legacy-files-complete.tar.gz`，6,521,306,807字节，gzip 完整性通过；GCS 对象已在08:29:57 UTC创建，CRC32C `Uz0lgg==`，独立本地CRC32C计算与云对象匹配。完整归档包括历史安装包备份。
- 旧 nginx、systemd和环境配置存于私有 `legacy-server-config.tar.gz`，4,777字节；不把密钥写入 Git。
- 私有云备份前缀 `gs://pearnly-app-backups-112074003592/20260905/`；本机受限目录 `/Users/skin/.config/pearnly-migration/20260905/`。`.partial` 是失败中间件，不能用于恢复。
- 真实 Cloud Run 独立 Job 完成三处挂载的跨实例写入/读取哈希验证、Chromium启动和测试对象清理；不是仅本地单元测试。

| GCS bucket | 用途 |
|---|---|
| `pearnly-app-files-112074003592` | 持久业务文件与 uploads 前缀 |
| `pearnly-app-temp-112074003592` | var 临时任务文件，7天过期 |
| `pearnly-app-installers-112074003592` | 当前安装包与 latest.json，由应用转发下载 |
| `pearnly-app-backups-112074003592` | 迁移备份，版本保留；旧版本30天清理 |
| `pearnly-app-build-112074003592` | 构建临时源，7天过期 |

所有桶均新加坡、统一桶级权限、阻止公共访问。Cloud Run 本地临时磁盘不是备份。

## 验证与告警边界

- 本地：当前发布的完整 pre-push 已通过（1146个测试模块与静态闸）；定向真实 PostgreSQL 任务状态测试与备份恢复分别执行。GitHub通用CI仍停用，不把本地通过写成远程CI通过。
- 远程：上述 GitHub CD成功；镜像内 Python compileall、Chromium启动、schema Job、候选健康/就绪/精确版本及最终流量检查通过。
- 线上：正式域名健康/就绪、页面与静态文件检查通过；保留登录态的管理后台可读取。真实 Cloud Tasks OIDC 探针到私有 Worker 返回200。
- Scheduler启用后，数据库已回读 `maintenance`、`queue.ocr`、`queue.recon`、`queue.steward` 各3次 succeeded。这里只证明调度/消费；无待处理业务时不等于完成一次真实OCR或外部ERP交易。
- 原有小助手每3秒 lease 返回401，旧 Vultr 日志也存在；不能通过迁移放宽认证。真实设备需使用有效绑定验收。历史 ERP retrying 记录（2026-06-20）保留，不冒充已修复。
- 邮件通知渠道已配置为用户指定的 `skinzihao@gmail.com`，channel `9342288420654696611`；4条告警已启用：公开readiness、内存85%、队列积压、任务失败/不确定日志。没有主动发送测试邮件，未确认邮件实收。
- Uptime每15分钟，至少两个地点失败触发；15:45回读六个探测地点的最近样本均为true。任务日志规则不是所有LINE/ERP业务失败的全覆盖。详见 [监控配置](../../deployment/cloud-run/monitoring/README.md)。
- 预算实际为 **300 THB/月**，50%/90%/100%实际用量及100%预测告警；仅项目pearnly的Run、Storage、Artifact Registry、Tasks、Scheduler、Secret Manager，排除Vertex和Supabase。预算不是硬停机或总费用上限。
- 项目 `_Default` 日志保留14天。历史“$1–3/月”等仅初步估算；真实支出受任务时长、客户端轮询、存储、流量和构建影响。
- **用户手机 LINE、OCR 文件处理和实际 ERP 写后回查仍未验收，不标记 USER_ACCEPTED。**

## 退役与回退规则

旧 VM仍存在时也不得用历史 `git-deploy.sh` 再发布。Destroy须在新站验证和备份完成后单独明确确认；关应用或Stop都不代表Vultr停止实例计费。退款是独立工单事项，本次没有提交退款回复。

后续 Cloud Run 回退只切到已验证、与当前schema/持久文件兼容的 revision。施工用 preflight revision不是验收基线。数据库/文件破坏性变更需配套恢复，不能只换旧镜像。

若必须回到旧VM，先暂停Scheduler并处理在途任务，确认数据库向后兼容，把切流后新增/修改的GCS文件同步回旧挂载，再验证旧服务和单一消费者；不能直接重启旧Vultr导致新文件缺失或双份任务。备份恢复须在隔离环境验证后单独决策，禁止覆盖现有Supabase来“试一下”。
