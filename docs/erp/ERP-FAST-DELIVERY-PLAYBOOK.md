# ERP 快速交付执行手册

## 目的

在不降低真实验收标准的前提下，缩短 ERP/Cowork 全部剩余功能从冻结合同到用户确认的时间。
当前校准：F1–F7 全部剩余工程合计约 **7–11 个工程日**，约 **8–15 个日历日**；若等待真实设备、Express、MR.ERP 或用户，可延长至 **2–3 周**。

## 不可关闭的质量门

- 远程 CI workflow `281113573` 当前为 `disabled_manually`：自动 CI/E2E 已关闭；本地分层机械闸、lint、真实 PG、RLS、HTTP contract 和定向 unit 仍保持开启。真实 E2E 改为每个功能边界由主控执行。
- 不把 flag-off 的技术切片称为“完成”，也不做长期灰度。当前功能做到可用 candidate 后，直接在生产启用并进行真实验收；只有依赖尚不完整、启用会断链或产生错误数据的内部半成品（当前 F1 缺 B3B3/B3C）才暂不启用，并明确标记为未完成。
- 每个用户功能合并为一个 release candidate，一次启用、一次真实验收；push 后使用 manual CD 绑定精确 SHA，并回读生产 SHA、服务时间、ready 和部署健康日志。测试仍只用 TEST 账套和唯一单号，防止外部 ERP 产生副作用。

## 当前功能内并行

当前功能的三条代理线从同一份合同施工，文件 ownership 不重叠；后续功能不得提前施工：

1. service/route 实现；
2. schema/Alembic/真实 PostgreSQL；
3. contract、RLS、并发和定向 unit 测试。

独立审查在实现冻结后进行。文档只由一个 owner 在生产回读后收口；不得重复派发或各自改写接口。

## 单一合同与验证顺序

合同必须先写清场景、范围、错误码、权限、状态机、锁序、文件清单和测试矩阵。代理交付必须同时给出真实 PG、HTTP boundary、定向 unit、`git diff --check` 和未解决问题；不能先用 mock 代替真实事务。

主控按以下顺序推进：本地分层验证 → 当前用户功能合并为单一 release candidate → push → manual CD 精确 SHA → 生产启用与回读 → 在该生产 SHA 上执行主控真实浏览器/真实环境预验收与 ERP report readback → Zihao 真机明确 OK → 才进入下一个功能。

## 证据与指标

每批记录：功能/批次、合同版本、各代理和 ownership、candidate SHA、`CI state=disabled`、manual CD run/result、本地验证时间、manual CD 时间、生产部署时间、用户等待时间、PG/HTTP/unit/E2E 结果、生产 SHA/时间/ready、主控真实浏览器/真实环境预验收、Zihao 真机明确 OK、ERP report 证据、feature flag 状态、用户 OK 原话。

同时记录首轮交付数、真实缺陷数、返工轮次、返工原因、代理、审查发现时间、本地验证时间、manual CD 时间、生产部署时间和用户等待时间；只有因真实缺陷修改才计入返工率，正常审查和补证据不计入。

本地分层闸、真实 PG/HTTP、功能边界真实 E2E、真机、ERP report、精确 SHA 部署和证据要求均不得因提速而降级；主控负责真实浏览器/真实环境预验收，Zihao 负责最终真机明确 OK。内部半成品不得发布或汇报为“完成但关闭”。
