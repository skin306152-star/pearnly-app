# Pearnly 监控配置

2026-09-05已在项目`pearnly`实际应用并回读。ERPNext是独立项目，本目录不管理它。用户指定邮箱`skinzihao@gmail.com`，通知渠道`projects/pearnly/notificationChannels/9342288420654696611`已启用；未发送测试邮件，不把渠道创建等同于邮件实收。

`provision.py`默认只读取并输出计划；`--apply`才创建/更新。按唯一displayName幂等更新，重名则停止；不删除其他策略、不创建渠道、不制造测试事故。

```bash
python deployment/cloud-run/monitoring/provision.py --queue pearnly-background
python deployment/cloud-run/monitoring/provision.py \
  --queue pearnly-background \
  --channel projects/pearnly/notificationChannels/9342288420654696611 --apply
```

## 已启用的配置

| 资源 | 实际配置 / ID |
|---|---|
| HTTPS uptime | `https://pearnly.com/api/ready`，HTTP200且JSON包含ready:true，每15分钟，30秒超时，证书验证 |
| 公共readiness不可用 | 至少两个地点报告失败，policy `6213068893030375282` |
| 内存 | Web/Worker p99超过85%持续5分钟，policy `296200291680164183` |
| Tasks积压 | `pearnly-background`深度超过10持续10分钟，policy `6213068893030373606` |
| 任务日志 | failed/uncertain/delivery_pending/queue_wakeup_pending，policy `6213068893030372174`，15分钟通知限频 |
| 日志 | 项目`_Default`保留14天 |

四条策略均enabled并绑定上述邮箱渠道。Uptime check ID为`pearnly-cloud-run-public-readiness-d7ACZquLk80`；09-05 15:45回读六个探测地点的最近样本均为true。Uptime会唤醒min=0的Web，低频配置不能视为分钟级可用性保证；冷启动超过30秒可能失败。内存无实例时无样本，不对空闲缺数据报警。

Cloud Tasks深度不等于所有数据库pending/running任务。日志规则依赖应用确实产生日志；某些取消请求或业务失败未落匹配日志时，不会被这条策略覆盖。没有LINE消息往返探针，也不能声称所有LINE/ERP/OCR业务故障均已覆盖。真实业务和邮件投递验收另记[状态账本](../../../docs/deployment/MIGRATION_STATUS.md)。

## 已配置的预算

账单币种是THB，开发基础设施预算为**300 THB/月**。Budget ID：`billingAccounts/018212-2CEAC6-1B3C5D/budgets/541ea14c-9842-407d-a672-50d01d7a131d`。实际用量50%/90%/100%，预测100%触发，发送至同一指定渠道；默认IAM收件人关闭。

`render_budget.py --amount 300 --currency THB --include-supporting-services`只生成请求体，不执行创建。生成结果默认没有收件渠道；本次实际应用前，在Cloud Billing API的`notificationsRule.monitoringNotificationChannels`中加入了上述渠道。更新现有预算时必须保留此字段，不能直接用无渠道草稿覆盖。

预算仅筛选`projects/112074003592`的Cloud Run、Cloud Storage、Artifact Registry、Tasks、Scheduler、Secret Manager。排除Vertex AI、ERPNext项目及Supabase；日志、网络、构建等独立计费项未必属于筛选服务，不能称总账单预算。预算不是花费封顶，不自动停止资源；免费赠款抵扣也会影响预算统计，另看账单原始费用。

首次创建时Google Catalog API已实时核对这些服务ID。调整资源或阈值后须回读实际配置并更新账本；历史几美元/月的估算不是账单承诺。

来源：[指标目录](https://docs.cloud.google.com/monitoring/api/metrics_gcp_c)、[Cloud Run指标](https://docs.cloud.google.com/monitoring/api/metrics_gcp_p_z)、[AlertPolicy API](https://docs.cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.alertPolicies)、[预算API](https://docs.cloud.google.com/billing/docs/reference/budget/rest/v1/billingAccounts.budgets)。
