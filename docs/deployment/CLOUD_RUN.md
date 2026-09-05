# Pearnly Cloud Run 部署正本

本文件规定 Pearnly 应用的 Cloud Run 部署与操作边界。**当前真正上线的位置、版本及未完成项只看 [迁移状态账本](MIGRATION_STATUS.md)**；存在配置、workflow 或镜像不代表完成迁移。[RUNBOOK](../RUNBOOK.md) 已更新为 Cloud Run 操作入口。旧 Vultr 已销毁，历史 SSH/systemd 流程不能再用于发布或回退。

## 项目边界

| 项目 | 仓库/环境 | 本次处理 |
|---|---|---|
| Pearnly 网页、LINE、OCR、外部 ERP 接口 | `skin306152-star/pearnly-app`；日常本地路径 `/Users/skin/Developer/Pearnly/pearnly-app` | 从 Vultr 迁移到 Cloud Run |
| ERPNext 租户账务平台 | `/Users/skin/pearnly-erp`；GCP `project-d0fbd530-1ee3-436d-b58` | 不迁移、不改数据库、不停机或删除资源 |
| Supabase PostgreSQL | Pearnly 现有数据库 | 保持实例和数据；不是 ERPNext 的 MariaDB |

迁移施工 worktree 是 `/Users/skin/Developer/Pearnly/pearnly-app-cloud-run`。不得因会话初始目录在 ERPNext 仓库而在那里修改 Pearnly 文件或部署配置。两个项目可以通过 API 连接；ERPNext 是否开机只决定依赖它的功能是否可用。

## 目标资源

GCP 项目 `pearnly`（项目编号 `112074003592`），区域 `asia-southeast1`（新加坡）。以下为当前开发配置基线；每次调整后的实际值记在账本。

| 资源 | 目标 |
|---|---|
| Cloud Run `pearnly-web` | 1 vCPU / 1 GiB；开发 `min=0,max=2`；真实营业再按需调 `min=1` |
| Cloud Run `pearnly-worker` | 1 vCPU / 2 GiB；`min=0,max=2`；浏览器任务实例并发 1 |
| Cloud Tasks | 可靠派发、重试、并发控制；处理端必须幂等 |
| Cloud Scheduler | 触发邮件、对账、ERP 重试、清理；不在每个 Web 实例重复启动无限循环 |
| Cloud Storage | 私有文件与安装包；临时对象按生命周期过期；保留原文件授权与加密语义 |
| Secret Manager | 秘钥不入 Git、镜像、日志；Web 与 Worker 独立服务账号和最小权限 |
| Cloudflare | 保留 `pearnly.com`；HTTPS/域名入口；不新增 Google 负载均衡器 |
| Vertex AI | 保持现有新加坡区域配置 |

Cloud Run 本地磁盘只作临时空间。响应后继续执行的进程内任务不能作为可靠任务承诺。实例扩容或启动不得全局打断其他实例的 `running` 任务。数据库初始化必须在发布流程中串行执行，不能依赖本机文件锁协调多实例。

## 发布与回读

1. 在隔离 worktree 完成改动、按风险运行本地检查；前端源码/产物与缓存版本同提交。
2. 推送精确候选 SHA。使用仓库当前 Cloud Run 发布 workflow（名称及运行证据记在账本），通过 GitHub OIDC / GCP Workload Identity Federation 获得短期权限。
3. GitHub 构建容器，推送 Artifact Registry；保留完整 commit SHA、镜像 digest、workflow run，禁止浮动 `latest` 作为发布身份。
4. 使用该镜像发布 Web/Worker 候选 revision，先验证 readiness，再切换流量。未通过的候选不得接管正式流量。
5. 回读 GCP 项目、区域、服务配置、revision、实际 digest、流量分配；在正式域名核对健康、就绪及应用版本，并按变更验证网页、LINE、任务、附件、OCR、ERP 实际消费路径。
6. 分别记录本地检查、容器检查、远程 workflow、生产回读和用户真机验收。HTTP 200 不等于 OCR 成功或外部 ERP 已入账。

当前 `.github/workflows/manual-deploy.yml` 已重写为 Cloud Run 的 `Manual CD`；同名文件的历史 VM 内容已退役。旧 `/internal/deploy/manual` / `git-deploy.sh` 不得再用于发布。切流前后明确停用旧发布及后台任务入口，避免同一个 Supabase 上运行两套调度器。不要同时向两边部署来“保险”。

## 切换与回退

迁移前记录旧版本、配置与文件清单并备份；初拷后必须处理最后增量和在途任务。切换时仅一个环境负责周期任务/消费者，保留可核验的文件数量、大小或校验和证据。确认域名与新版本一致后再按账本处理旧实例。

Cloud Run 回退是把流量切回**已验证、与当前数据库及文件兼容**的 revision。数据库或持久文件变更不能仅靠旧镜像恢复。旧 Vultr 已销毁。未来如需 VM 部署，须另行建立新资源并验证数据库/文件恢复，再协调流量与单一调度器；旧 IP 和 SSH 别名不得复用。

Vultr 已经用户明确授权销毁，备份、技术验证和销毁回读证据见状态账本。退款是否批准是单独事项，不把迁移完成等同于余额到账。

## 监控与成本

监控网页/LINE 可用性、任务失败、队列积压、内存和费用；设置预算告警及日志保留。最大实例数与预算告警不是绝对账单封顶。`min=0` 允许空闲缩零，不保证任务结束立即归零。开发月费、每千任务费和切固定机器的时机应以计算时长、流量、存储及实际账单判断，历史几美元估算不是承诺。

## 发布探针身份

候选 revision 的 IAM 探针显式模拟 `pearnly-deploy@pearnly.iam.gserviceaccount.com`，ID token audience 使用服务 canonical URL，实际请求访问 candidate tag URL。发布脚本仅添加服务级 Invoker：Worker 授予 Web、Tasks 和 deploy 账号；Web 授予 deploy。初次 Web 保持私有，正式域名切换由迁移主控单独处理；后续发布保留已有 IAM。

WIF 发布身份需要在 deploy 服务账号上具备 `iam.serviceAccounts.getOpenIdToken`。如身份已是该账号，可授予其自身较窄的 `roles/iam.serviceAccountOpenIdTokenCreator`，不要为 ID token 探针授予能反复生成 access token 的宽泛自模拟权限。本机操作者也需有该账号的 ID-token 生成权限。[Google ID token 说明](https://docs.cloud.google.com/docs/authentication/get-id-token)。

## 大文件下载与发布验证

Cloud Run HTTP/1 非流式响应受32 MiB限制，见[官方配额](https://docs.cloud.google.com/run/quotas)。Cloud入口的LargeResponseStreaming中间件对至少32 MiB的有正文响应移除Content-Length，让ASGI服务器在HTTP/1连接中按chunked发送；不缓存正文，不改变文件权限、ETag、Last-Modified、Content-Range或小响应，HEAD及HTTP/2响应保留长度（下载进度仍可取得完整大小）。标准FileResponse和StaticFiles继续分块读GCS挂载。

Web和Worker候选及正式流量检查都必须完整下载现有安装包，与GCS对象大小/MD5比对并确认generation未变；不能仅凭health/ready或HEAD判定大文件可用。deploy账号因此只有安装包桶额外objectViewer权限，不获写权限。任何下载失败均阻断候选切流。

上传契约包括100 MiB单文件和超过32 MiB的多文件批次，因此Web/Worker容器均通过`ports.name=h2c`使用HTTP/2入口，云端由Hypercorn单进程提供ASGI服务，原开发/VM入口不变。Web→Worker的HTTPX客户端强制HTTP/2；不能只移除请求Content-Length绕过HTTP/1请求限制。服务复用原Uvicorn ProxyHeadersMiddleware以保留客户端IP和scheme语义，Cloudflare与WorkerProxy继续清理代理头。云专用依赖由`requirements-cloud.in`在原业务依赖约束下编译到`requirements-cloud.lock`。
