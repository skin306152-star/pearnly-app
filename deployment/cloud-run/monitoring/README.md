# Pearnly 监控配置（待执行）

2026-09-05 通过 Monitoring API 只读核查：项目 `pearnly` 当前没有 Notification Channel。以下文件是未执行配置，不代表告警已启用、通知已送达或迁移已验收。只限 Pearnly 项目，不碰 ERPNext。

`provision.py` 默认只读取现有渠道并输出计划；显式 `--apply` 才创建/更新资源。按唯一 displayName 幂等更新，发现重名即停止，不删除其他策略。没有渠道仍能产生控制台 incident，但不能声称用户收到通知。不创建邮件渠道、不自动发消息。所有阈值为开发阶段初始建议，需根据正常任务时长调整。

```bash
python deployment/cloud-run/monitoring/provision.py --queue <实际pearnly队列名>
# 主控审阅后才能实际执行；可附 --channel projects/pearnly/notificationChannels/已有编号
python deployment/cloud-run/monitoring/provision.py --queue <实际pearnly队列名> --apply
```

配置包括：

- `https://pearnly.com/api/ready` HTTPS 与 JSON `ready:true`，每 15 分钟检查；至少两个地点报告失败才告警。频繁探测会唤醒 min=0 Web；此配置选择低频，不能理解为分钟级可用性保证。首次冷启动超过 30 秒可能出现失败，待实测调整。
- Cloud Run Web/Worker 内存 p99 超过 85% 持续 5 分钟；无实例时没有样本，不对空闲缺数据报警。
- 指定 Cloud Tasks 队列深度超过 10 持续 10 分钟；仅反映 Cloud Tasks 队列，不等于数据库所有 pending/running 工作总量。
- Cloud Run 日志命中 `cloud_task_failed`、`cloud_task_uncertain`、`cloud_task_delivery_pending`、`cloud_queue_wakeup_pending`，15 分钟通知限频。依赖应用确实产生日志；取消请求直接写 uncertain 的路径若未记录该日志，不能被本策略覆盖。LINE/ERP/OCR 的业务失败若不抛异常或不落这些日志，也不能以此声称全部已监控。

Root 在正式域名切流并健康检查通过后再应用 uptime；提前应用会测旧服务器或迁移中的入口。应用后回读实际策略、绑定渠道和 uptime 状态，另做可控验证再记账。脚本不创建测试事故或发送测试通知。

## 费用预算（只生成，绝不创建）

`render_budget.py --amount <批准金额> --currency <账单币种>` 输出 Cloud Billing Budget API 请求体。默认只计算 Cloud Run + Cloud Storage；附 `--include-supporting-services` 后加入 Artifact Registry、Tasks、Scheduler、Secret Manager。项目严格筛为 `projects/112074003592`，排除 Vertex AI、其他项目和非 GCP 的 Supabase。日志、网络、构建等独立计费项未必属于这些筛选服务，不可称总账单预算。

Catalog API 于 2026-09-05 实时回读并确认脚本中的服务 ID。预算金额与币种由主控/用户决定，未硬填金额。生成文件关闭默认 IAM 收件人；没有添加通知渠道或 Pub/Sub，因此它只是预算范围草稿，不是已能送达的费用通知。实际创建前明确已有通知渠道或经授权启用账单默认收件人。预算不限制花费、不自动停止资源；免费赠款计入抵扣会掩盖未抵扣资源成本，另看费用报表。

来源：[指标目录](https://docs.cloud.google.com/monitoring/api/metrics_gcp_c)、[Cloud Run 指标](https://docs.cloud.google.com/monitoring/api/metrics_gcp_p_z)、[AlertPolicy API](https://docs.cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.alertPolicies)、[预算筛选 API](https://docs.cloud.google.com/billing/docs/reference/budget/rest/v1/billingAccounts.budgets)。
