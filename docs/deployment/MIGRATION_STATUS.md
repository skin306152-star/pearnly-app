# Pearnly 部署与迁移状态账本

更新时间：2026-09-05 22:20（Asia/Bangkok，UTC+7）。状态：**Cloud Run已接管，OCR 重构已发布；旧Vultr已销毁，用户业务验收单列**。
2026-09-05 用户暂停后已明确回复“可以继续了”；已完成恢复后的大文件传输和安装包发布验证，历史检查点见[暂停与恢复记录](RESUME_MIGRATION.md)。
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
| 旧 Vultr | `66.42.49.213` / UUID `25a6d7e9-bbcd-4c00-958b-c771f503cdbc` 已于2026-09-05 18:25销毁；控制台回读已终止、No Instances |
| ERPNext | 独立仓库 `/Users/skin/pearnly-erp`，GCP `project-d0fbd530-1ee3-436d-b58`，VM `pearnly-erp-dev`；只读回查 RUNNING，本次未修改 |

Web 使用1 GiB而非早期讨论的512 MiB，max=2而非3；是开发阶段保守配置。min=0允许空闲缩零，并不保证请求结束立即归零；正在运行的小助手轮询和定时探针仍会产生调用。

## 正在服务的发布身份

- 完整 SHA：`7dc72a7550755d88784f48682854757294bb542e`。
- 镜像：`asia-southeast1-docker.pkg.dev/pearnly/pearnly-app/app@sha256:2fd9ffa9f94a2aabbe126789fa418030fe36c67bd7f3b74ede35e54b9d4b25aa`。
- Web revision：`pearnly-web-7dc72a755075-s2`，100%流量；Worker revision：`pearnly-worker-7dc72a755075-s2`，100%流量。
- OCR 发布 [33974005122](https://github.com/skin306152-star/pearnly-app/actions/runs/33974005122) 成功，schema execution `pearnly-schema-m6928`、两端候选/正式安装包完整校验通过。正式域名 health/ready 均 200，nonce `ocr_release=7dc72a755075` 的请求日志命中新 Web revision。旧镜像 674909a0 为迁移基线，以下记录保留作历史证据。
- 22:19:52 Bangkok 原子更新 OCR 策略并写操作审计：invoice=economy（3.1-lite→3.8 LOW）；其余现有 OCR task=enterprise。银行/GL/VAT 扫描件使用冻结 Enterprise 财务适配器；ID、SalesVAT 发票、通用网格保留专用 Schema 使用 3.8；结构化文件保留原生解析。不能将选 A 档解读为每个文件都会收费调用 Document AI。
- Web/Worker 各自 runtime secret v2 新增 Enterprise 四项配置：项目112074003592、处理器6c7dfffac937fcd9、新加坡、共享9 RPM；代码固定 v2.1.1，不用处理器默认 v1.0。两 SA 新增 Document AI API User，其他运行配置不变。Worker 身份单页合成探针成功；不代表全部业务文件人工验收。详细边界见 [OCR 记录](../ocr-integration-progress-2026-09-05.md)。
- [成功的 GitHub 发布运行33962463833](https://github.com/skin306152-star/pearnly-app/actions/runs/33962463833)。同镜像schema execution `pearnly-schema-mmsws`于11:11:11 UTC确认完成；Web/Worker候选及正式流量均通过完整安装包校验，18:13 Bangkok完成切流回读。上一已验证版本为85cc56b4（CD33956960191）；它尚有大文件传输限制，不作为当前传输能力基线。
- 服务地址：`https://pearnly-web-112074003592.asia-southeast1.run.app`；私有 Worker `https://pearnly-worker-112074003592.asia-southeast1.run.app`。
- 2026-09-05 15:28 左右切流。正式域名 readiness nonce `cutover-20260905-0828` 的 Cloud Run 请求日志确认命中初次接管的 `pearnly-web-c3797e182785-s1`，HTTP 200；www health 也为200。
- 当前版本已补齐四项Express进程内schema-ready：每次启动只读验证列、约束、RLS、策略、函数与触发器，失败阻止启动。85cc56b4阶段在09:13:51 UTC以nonce `final-readiness`回读无token heartbeat恢复401；674909a0已保留该修复并再次回读401，直接匿名Worker仍为403。
- 历史85cc56b4发布曾因错误SHA输入取消33956937444，未进入云端变更；随后33956960191成功。当前674909a0的发布记录为33962463833，两者不可混用。
- 账本/CI文档提交可能晚于线上镜像SHA；文档更新不自动重发容器，不能据仓库HEAD推断线上版本。

## 域名与旧发布入口

Cloudflare Worker 两条 route 为 `pearnly.com/*` 和 `www.pearnly.com/*`，均 fail closed。没有新增 `*.pearnly.com/*`，避免接管其他租户子域名。源站在 Worker 中明确指定 Cloud Run Web。

2026-09-05 DNS 回读：主域名由旧 A `66.42.49.213` 改成 proxied CNAME `pearnly-web-112074003592.asia-southeast1.run.app`；www 保持 proxied CNAME `pearnly.com`。原有 MX、SPF、DKIM 保留。旧 IP 不再是网站 DNS 源站。

小助手安装包来自独立仓库`pearnly-companion`。旧SSH workflow已替换，新流程提交`ed48b1a1295f01e2f9d8b4ed7afbe0eb39f3e5ce`已推送，workflow331277700已重新启用，staging验证[33961319994，第2次attempt](https://github.com/skin306152-star/pearnly-companion/actions/runs/33961319994)已成功：Windows构建、WIF、GCS完整回读和正式域名完整下载均通过。第1次attempt发现HTTP/1大响应限制并正确阻断；应用674909a0修复后只重跑publish job，沿用原Windows artifact，未重建或替换生产包。生产仍为1.1.77，未替换安装包；操作见[安装包发布](COMPANION_PUBLICATION.md)。

通用CI仍停用，ci.yml已移除旧VM deploy job并保留所有验证job，避免未来恢复CI时误触发历史部署。

旧 GitHub webhook `625195648`（`/internal/deploy`）已 inactive；Cloudflare 阻断 `/internal/`，新应用也不提供旧 VM 发布路径。旧实例已销毁，SSH别名 `pearnly-prod` 已退役；旧IP可能重新分配，不得再连接或发布。不要重新建立第二套周期消费者。

## 数据与恢复证据

- 旧应用停用后，本地源文件与 GCS **1448个业务文件逐一 MD5 核对，0不一致**；最终 rsync 因重复复制已相同对象被中断，以独立完整哈希复核为准。
- 安装包 `PearnlyCompanion-Setup.exe` 为62,905,102字节，云端 MD5 与源文件一致；latest.json 可从正式域名读取。
- Supabase 初始备份 `supabase-before.dump` 4,518,313字节，SHA256 `69dbb6d5c80c38397f4bdb9213d044cccb220aaca96a0380e96ed0395e7c92cd`；在隔离 PostgreSQL17+pgvector 容器中严格恢复 public schema/数据并执行新 schema 成功。5张原有零策略 RLS 表保持启用，未为迁移全局关闭 RLS。
- 切流前另存 `supabase-pre-cutover.dump`（4,518,312字节）；已上传。恢复试验针对初始备份，未把第二份声称为另一次完整恢复试验。
- 完整旧文件归档 `legacy-files-complete.tar.gz`，6,521,306,807字节，gzip 完整性通过；GCS 对象已在08:29:57 UTC创建，CRC32C `Uz0lgg==`，独立本地CRC32C计算与云对象匹配。完整归档包括历史安装包备份。
- 旧 nginx、systemd和环境配置存于私有 `legacy-server-config.tar.gz`，4,777字节；不把密钥写入 Git。
- 私有云备份前缀 `gs://pearnly-app-backups-112074003592/20260905/`；本机受限目录 `/Users/skin/.config/pearnly-migration/20260905/`。失败的`.partial`中间文件已移入本机废纸篓，不能用于恢复。
- 真实 Cloud Run 独立 Job 完成三处挂载的跨实例写入/读取哈希验证、Chromium启动和测试对象清理；不是仅本地单元测试。测试Job已删除，两只专用PG验证容器已停止；ERPNext管理后台容器未清理。

| GCS bucket | 用途 |
|---|---|
| `pearnly-app-files-112074003592` | 持久业务文件与 uploads 前缀 |
| `pearnly-app-temp-112074003592` | var 临时任务文件，7天过期 |
| `pearnly-app-installers-112074003592` | 当前安装包与 latest.json，由应用转发下载 |
| `pearnly-app-backups-112074003592` | 迁移备份，版本保留；旧版本30天清理 |
| `pearnly-app-build-112074003592` | 构建临时源，7天过期 |

所有桶均新加坡、统一桶级权限、阻止公共访问。业务文件桶启用7天soft-delete保护。Cloud Run 本地临时磁盘不是备份。

## 验证与告警边界

- 启动修复：40个聚焦测试及24个subtest通过；真实PG副本12种安全结构破坏均阻断启动，只读线上目录预检通过。
- 本地：当前发布的完整 pre-push 已通过（1149个测试模块与静态闸）；定向真实 PostgreSQL 任务状态测试与备份恢复分别执行。GitHub通用CI仍停用，不把本地通过写成远程CI通过。
- 远程：上述 GitHub CD成功；镜像内 Python compileall、Chromium启动、schema Job、候选健康/就绪/精确版本及最终流量检查通过。
- 线上：正式域名健康/就绪、页面与静态文件检查通过；保留登录态的管理后台可读取；真实历史记录详情和迁移前PDF在浏览器中正确渲染，未保存修改或推送ERP。真实 Cloud Tasks OIDC 探针到私有 Worker 返回200。
- Scheduler启用后，数据库已回读 `maintenance`、`queue.ocr`、`queue.recon`、`queue.steward` 各10次 succeeded。这里只证明调度/消费；无待处理业务时不等于完成一次真实OCR或外部ERP交易。
- 原有小助手每3秒 lease 返回401，旧 Vultr 日志也存在；不能通过迁移放宽认证。真实设备需使用有效绑定验收。历史 ERP retrying 记录（2026-06-20）保留，不冒充已修复。
- 邮件通知渠道已配置为用户指定的 `skinzihao@gmail.com`，channel `9342288420654696611`；4条告警已启用：公开readiness、内存85%、队列积压、任务失败/不确定日志。没有主动发送测试邮件，未确认邮件实收。
- Uptime每15分钟，至少两个地点失败触发；15:45回读六个探测地点的最近样本均为true。任务日志规则不是所有LINE/ERP业务失败的全覆盖。详见 [监控配置](../../deployment/cloud-run/monitoring/README.md)。
- 预算实际为 **300 THB/月**，50%/90%/100%实际用量及100%预测告警；仅项目pearnly的Run、Storage、Artifact Registry、Tasks、Scheduler、Secret Manager，排除Vertex和Supabase。预算不是硬停机或总费用上限。
- 项目 `_Default` 日志保留14天。历史“$1–3/月”等仅初步估算；真实支出受任务时长、客户端轮询、存储、流量和构建影响。
- **用户手机 LINE、OCR 文件处理和实际 ERP 写后回查仍未验收，不标记 USER_ACCEPTED。**

## 恢复后补齐的传输与安装包验证

- 原HTTP/1容器的约63MB安装包下载被平台限制为500；同时原业务支持100MiB单文件和超过32MiB的多文件批次，不能把迁移后的上限降到32MiB。
- 当前Web/Worker均为Hypercorn单进程ASGI、h2c容器入口，Web→Worker强制HTTP/2。保留原代理头处理；HTTP/1大响应使用流式传输，HTTP/2和HEAD保留长度。Cloudflare原有额度和应用自身上传限制仍适用。
- 新增发布检查会对Web/Worker候选及正式流量完整下载安装包，核对GCS大小/MD5，并验证generation未变；任一步失败阻断切流。本次四次检查均实际通过。
- 本地38个聚焦测试与20个subtests通过；34MiB（35,651,584字节）在直接Hypercorn与Web代理的HTTP/1、HTTP/2链路均完整回读。
- 使用同一已发布镜像在两个临时IAM私有CloudRun服务上做真实34MiB验证：直接Worker和经Web→Worker，各用HTTP/1与HTTP/2客户端，共四条链路；容器均回读HTTP/2、正确大小及SHA256 `23dfbc08258fa16e92089de9eeedd0d199590c6983c0deebeca11b3baffab7b2`。无业务写入。首次新IAM授权传播期间转发返回403/503，授权不变的后续完整验证通过。两服务已删除，匿名调用曾分别验证403。
- Companion构建来源`ed48b1a1295f01e2f9d8b4ed7afbe0eb39f3e5ce`，VERSION/ProductVersion=1.1.77，staging包62,904,235字节，SHA256 `5e6b3d1e3bb98c98cf2f961d336c75148d38a02c64d70fc500cc78eea4d3cc6d`。这是测试构建，不是新的正式客户端发布。
- 生产原安装包仍62,905,102字节、generation `1788593866085056`；latest.json仍86字节、generation `1788593862422782`。两者MD5/大小/generation与staging前逐项一致。仅清理本次`staging/33961319994-1/`和`-2/`对象，未清理生产releases或其他发布。
- Companion本地发布/更新相关17 tests和5 subtests通过；1项PySide6 UI测试在Mac缺依赖跳过，未冒称Windows用户设备验收。真实Windows构建及ProductVersion检查由上述GitHub run完成。

## 退役与回退规则

用户明确回复“销毁”后，2026-09-05约11:25 UTC（18:25 Bangkok）在Vultr控制台核对IP及UUID并执行Destroy。回读显示“Your VPS has been terminated”和“No Instances”。此前已核查无快照、附加磁盘、对象存储、保留IP，自动备份未启用。旧实例不再新增实例使用费；已产生账单及余额退款另行结算，本次没有提交退款回复，也没有获得退款批准。

销毁后正式域名 `/api/ready` 回读ready=true，db/gemini/smtp/line均ok；GCP项目pearnly仅保留Web/Worker两个服务，latestReady均为674909a0bd51-s1。独立ERPNext VM `pearnly-erp-dev` 回读RUNNING，未修改。

后续 Cloud Run 回退只切到已验证、与当前schema/持久文件兼容的 revision。施工用 preflight revision不是验收基线。数据库/文件破坏性变更需配套恢复，不能只换旧镜像。

旧VM已不存在，不能再通过旧IP或systemd回退。未来如需恢复VM部署，必须另行建立新资源、暂停Scheduler并处理在途任务，验证兼容数据库和完整文件恢复，再协调单一消费者及流量；不得使用迁移前文件覆盖切流后的新增数据。备份恢复须在隔离环境验证后单独决策，禁止覆盖现有Supabase来“试一下”。
