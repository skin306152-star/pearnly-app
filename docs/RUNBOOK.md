# Pearnly 运维手册

**当前Pearnly已由Cloud Run接管。** 每次操作先读[部署状态账本](deployment/MIGRATION_STATUS.md)，发布规范见[Cloud Run正本](deployment/CLOUD_RUN.md)。本页不再提供旧Vultr上线命令，避免两个环境争用同一个Supabase。

## 0. 30秒速查

| 需要处理 | 当前入口 |
|---|---|
| 确认部署版本和未完成项 | [状态账本](deployment/MIGRATION_STATUS.md) |
| 发布代码 | 下方精确SHA的GitHub `Manual CD` |
| 故障诊断 | Cloud Run revision、请求日志、数据库及任务状态 |
| 文件或安装包异常 | [持久存储规范](CLOUD_RUN_STORAGE.md)，检查私有GCS挂载与应用授权 |
| 告警/预算 | [实际监控配置](../deployment/cloud-run/monitoring/README.md) |
| ERPNext故障 | 独立仓库 `/Users/skin/pearnly-erp`；不使用Pearnly应用的发布或退役命令 |

## 1. 基础设施

Pearnly项目始终显式使用`--project=pearnly --region=asia-southeast1`。本机gcloud默认项目可能仍是ERPNext，不能省略项目参数。

正式入口为Cloudflare的`pearnly.com`和`www.pearnly.com`，Web公开、Worker受IAM保护，Supabase实例保持。Web/Worker共用精确镜像和私有GCS文件，账号/密钥分开；Cloud Tasks派发，Cloud Scheduler周期恢复。

旧`66.42.49.213`已于2026-09-05 18:25（Bangkok）Destroy，控制台回读No Instances；证据见状态账本。旧IP和`pearnly-prod` SSH别名已退役，不得再连接或部署。

## 2. 部署

在Pearnly隔离worktree完成有针对性的本地验证，提交并推送。当前`.github/workflows/manual-deploy.yml`已重写为Cloud Run流程，同名历史VM流程不可恢复。

```bash
# 候选必须正好等于GitHub master的完整40位SHA；不能跳过现有pre-push闸。
git rev-parse HEAD
gh api repos/skin306152-star/pearnly-app/commits/master --jq .sha
gh workflow run manual-deploy.yml --repo skin306152-star/pearnly-app --ref master -f sha=<完整候选SHA>
gh run list --repo skin306152-star/pearnly-app --workflow manual-deploy.yml --limit 3
```

Workflow通过WIF取得短期身份，构建容器并执行编译/Chromium探针，推送Artifact Registry，运行同镜像schema Job，再发布Web/Worker候选。两个候选精确SHA、digest、revision和readiness均通过后才切换流量。失败不得手工跳过门禁来切流。

schema Job执行DDL；服务实例只做读取验证，不能在每次冷启动创建表或重复启动后台循环。新增schema/security对象时同步维护启动契约检查与定向真实PG回归。

## 3. 回滚

流量回退只选择账本中已验证、与当前数据库/文件兼容的revision；施工preflight不能当成已验收版本。分别记录Web和Worker目标后，按顺序更新并验证两边：

```bash
gcloud run services update-traffic pearnly-worker --to-revisions=<已验证WorkerRevision>=100 --project=pearnly --region=asia-southeast1
gcloud run services update-traffic pearnly-web --to-revisions=<已验证WebRevision>=100 --project=pearnly --region=asia-southeast1
```

普通回退不会自动撤销数据库或文件变更。若schema不向后兼容，须先制定兼容迁移或备份恢复方案，禁止直接拿旧数据库覆盖现有Supabase。源码修复或`git revert`后仍走完整精确SHA发布。

旧Vultr已不存在，不能重启旧systemd回退。如未来需要VM部署，须另行建立新资源、暂停Scheduler并处理在途任务，验证兼容DB及完整文件恢复，再协调唯一消费者和流量。

## 4. CI状态查看

通用GitHub CI workflow仍按项目原决策停用；本地风险分层测试和pre-push闸继续执行。`Manual CD`是实际远程构建/发布流程；不得把“已配置workflow”写成“CI已运行通过”。成功/失败的run链接写入状态账本。

## 5. 健康检查与部署身份

```bash
curl -fsS https://pearnly.com/api/health
curl -fsS https://pearnly.com/api/ready
gcloud run services describe pearnly-web --project=pearnly --region=asia-southeast1 --format='yaml(status.latestReadyRevisionName,status.traffic)'
gcloud run services describe pearnly-worker --project=pearnly --region=asia-southeast1 --format='yaml(status.latestReadyRevisionName,status.traffic)'
```

`/internal/runtime-version`仅供直接Cloud Run/IAM发布探针；Cloudflare阻断内部路径。正式域名请求加唯一查询nonce后，在Cloud Run请求日志核对实际revision，可证明边缘流量抵达新服务。Python默认urllib的User-Agent可能被Cloudflare拒绝；使用正常浏览器或明确探针身份，不为此关闭安全规则。

HTTP200、登录后页面读成功、任务消费、实际外部ERP入账和用户真机验收是不同层级，分别记录。

## 6. 故障诊断

```bash
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="pearnly-web" AND severity>=ERROR' --project=pearnly --freshness=30m --limit=30
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="pearnly-worker" AND severity>=ERROR' --project=pearnly --freshness=30m --limit=30
gcloud scheduler jobs describe pearnly-background-recovery --project=pearnly --location=asia-southeast1 --format='yaml(state,status,lastAttemptTime)'
gcloud tasks queues describe pearnly-background --project=pearnly --location=asia-southeast1
```

先分清Cloudflare、Web代理、Worker、数据库/挂载与第三方业务错误。Cloud Run无空闲样本不等于故障；频繁客户端轮询、冷启动、长任务和IAM错误应看实际日志。队列HTTP200只说明派发处理完毕，还须查`cloud_task_deliveries`的failed/uncertain和原业务表；ERP推送状态正本仍为`erp_push_logs`。

不确定任务可能已执行外部写入，不能直接重放。先查第三方详情、幂等键及原日志，再按原业务重试规则处理。

旧Vultr诊断记录可查[迁移前RUNBOOK历史版本](https://github.com/skin306152-star/pearnly-app/blob/776808e7c3e5e4369d2d3b0129224204d019f0f8/docs/RUNBOOK.md)，仅用于理解旧环境，不能覆盖本页当前操作。
