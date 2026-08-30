# F1-B3B3 · Managed Agent Live Profile Dispatch

> 状态：设计/派单合同，未实现、未部署、未完成用户功能验收。\
> 前置证据：`pearnly-companion` 默认分支 `master`，HEAD\
> `72a92b8b31ac953bc8e0bbdae15461995d1396e8`，版本 `1.1.64`。\
> 本文只处理 managed endpoint 的认证、心跳和 live profile；B3C 队列 reservation/finalize/lease/ack 及所有 push 明确排除。

## 1. 目标与不可变裁决

B3B3 的目标是：B3B2b-2 promotion 后 `binding_generation >= 1` 的 endpoint 可以继续使用现有 Windows Companion token 发送心跳；云端记录 typed live 状态并执行 profile mismatch fail-closed。旧 `generation = 0` 的 auth、reporting、lease、ack 完全不动。

已裁决的硬边界：

1. 只为 heartbeat 增加独立 managed auth seam，严禁把所有 Agent 端点整体放宽到 managed。B3C 前 managed lease/ack 仍拒绝，所有 push 继续拒绝。
2. Companion 协议零改。服务端读取现有顶层 `account_set` + `account_dir` 计算 `profile_key`，不接受客户端提交的 `profile_key`。
3. promotion 不绑定 profile；首次 managed heartbeat 不 TOFU、不自动建立 bound profile。
4. 合法 managed heartbeat 只写 typed `live_account_set`、`live_profile_key`、服务端 `agent_last_seen_at`、`agent_version`。字段缺失或非法时清空 live pair，返回 `needs_attention`；profile mismatch 则保留并写入观察到的合法 live pair/last_seen，返回 `mismatch`，不写原始路径到新字段或错误详情。
5. B3B3 后端必须提供 owner 显式确认当前且新鲜 live pair 的能力：可确认 unbound，或明确切换到当前合法新鲜 live pair；不要求 `profile_ready=true`。必须有 expected-generation CAS、显式 confirm、busy-free、审计和 generation+1。绑定后 mismatch 仍记录 live/last_seen，但 `profile_ready=false`，绝不推送。
6. heartbeat HTTP 200 只表示设备已连通，不表示 ERP 可推；响应必须包含 `profile_status` 和 `profile_ready`。
7. managed reader 只用 typed 字段判断 online/unbound/mismatch/offline；gen0 reader 继续读取 config JSON。
8. revoked 或 disabled endpoint 拒绝 managed heartbeat；不泄露 endpoint/config/token 存在性细节。
9. B3C queue reservation/finalize/lease/ack、所有 `erp_push_logs` 写入和所有 ERP push 不在本批施工范围。

## 2. 现有 Companion 协议事实

真实代码位置：

- heartbeat body：`src/companion/queue_client.py:78-125`
- 周期调用：`src/companion/worker.py:248-312`
- 配对 token/body：`src/companion/pairing.py:80-125`
- 版本：`src/companion/version.py:10`

当前 heartbeat 顶层已有 `account_set`、`account_dir`、`account_company`、`account_set_row`、`companion_version`、`device` 等字段。`account_set` 实际是所选账套路径；`account_dir_resolved` 不在 heartbeat，只在单据 ack meta 中出现，不能假定为 heartbeat 字段。

因此协议零改的条件是：服务端兼容这份已有 body；不新增客户端字段、不要求客户端发送 profile key。旧客户端未收到新响应字段也不得因此被判成功推送。

## 3. 固定接口合同

### 3.1 heartbeat

继续使用：`POST /api/erp/agent/heartbeat`。

认证 seam 必须按 endpoint generation 分流：

- gen0：沿用现有 `exp_<endpoint_id>_<secret>` 认证和所有旧 writer；
- managed：仅 heartbeat 允许使用同一现有 token hash，且必须验证 endpoint 为 Express、generation ≥ 1、未 revoked、tenant/workspace 状态有效；
- managed lease/ack 等其它 Agent API 在 B3C 前继续返回既有拒绝错误，不得因 heartbeat seam 顺带放行。

managed heartbeat 成功响应最少包含：

```json
{
  "ok": true,
  "connected": true,
  "endpoint_id": "...",
  "profile_status": "unbound|ready|mismatch|needs_attention|offline",
  "profile_ready": false,
  "account_set": "..."
}
```

`profile_ready=true` 仅表示 live profile 与已绑定 profile 完全一致且数据新鲜；不表示有 lease、可写 Express 或 ERP 推送成功。

### 3.2 错误码

- 无效/不存在/revoked token：`401 erp.agent_unauthorized`；不区分 endpoint 是否存在；
- disabled endpoint：`403 erp.endpoint_disabled`；
- 合法 managed heartbeat 的字段缺失或非法路径：HTTP 200，`profile_status=needs_attention`、`profile_ready=false`，同时清空 live pair；profile mismatch：HTTP 200，`profile_status=mismatch`、`profile_ready=false`，保留观察到的合法 live pair/last_seen；两者都只表示设备在线，不表示 ERP 可推；
- B3C 前 managed lease/ack 仍由 gen0 认证路径拒绝，继续使用明确的未启用/不允许错误，不得返回 jobs 或接受 ack。

## 4. Live profile 与绑定合同

服务端使用现有 `services/erp/shared_express_profile.py:69-74` 的 `profile_key(account_set, account_dir)`。规范化和校验失败不得回显原始路径，也不得把它写入新的审计字段。

heartbeat：

- 每次合法请求都以服务端时间更新 typed `agent_last_seen_at` 和 typed `agent_version`；
- account_set/account_dir 均合法时写 typed live pair；
- 缺失或非法时清除 typed live pair，保留连通时标并返回 needs_attention；不匹配时保留观察到的合法 typed live pair/last_seen 并返回 mismatch；
- 不修改 `bound_account_set/bound_profile_key`，不创建绑定，不改变 generation。

owner confirm（属于 B3B3 后端范围，且不在首次 heartbeat 内自动发生）必须：

- owner + `erp.endpoint.manage`；
- 当前 live pair 新鲜、完整、且由 owner 明确确认；允许确认 unbound 或切换到当前合法新鲜 live pair，不要求此前 `profile_ready=true`；
- 显式 confirm；
- expected_generation 精确 CAS；
- endpoint busy-free；
- typed bound pair 与 live pair 原子写入；
- generation +1；
- required operation audit 失败则全事务回滚。

## 5. 三路无冲突 ownership

### A · Managed auth seam（新模块优先）

优先新建 managed 专用 auth seam/module；不得放宽或污染 legacy `services/erp/express_push/agent_store.py` 的 gen0 查询、token、lease、ack 或 push writer。仅 heartbeat 可调用该 seam。

### B · Typed live schema/writer + PG

负责新建 B3B3 live schema/writer、SECURITY DEFINER heartbeat SQL、PG/RLS/ACL 和 profile 计算：typed live pair、server time/version、缺失/非法清理、mismatch 保留。`services/erp/express_push/agent_reporting.py` 保持 gen0 不改；如确需改动，必须重新裁决。不得改 B3C 队列状态机。

### C · Owner confirm + HTTP boundary/reader

负责新 owner-confirm service/route，以及 `routes/erp_agent.py` 的 heartbeat generation 分流、请求/响应/错误码和 managed reader 的 typed online/unbound/mismatch/offline 映射。不得放行 managed lease/ack，不得修改 push 行为。

三路优先使用新模块，避免污染旧文件；不得同时编辑同一文件的同一函数。schema writer 的 SQL contract 由 B owner 提供，A/C 只调用固定 seam。

## 6. 真实反证矩阵

### PostgreSQL/RLS/trigger

- gen0 heartbeat 仍更新旧 config JSON，typed live 字段不被污染；
- gen1 合法 heartbeat 更新四个 typed 字段，触发器不允许绕过其他 lifecycle 列；
- managed writer 跨 tenant、错误 workspace、错误 endpoint、revoked、disabled 均拒绝；
- 直接 SQL 修改 typed live 或 bound 字段（无 heartbeat gate）失败；
- SECURITY DEFINER 函数固定 `search_path=pg_catalog`，PUBLIC execute 被撤销，应用角色 ACL 明确；
- heartbeat 与 rebind/revoke 并发时无半写、无 generation 回退、无 bound/live 错配；
- 旧 gen0 writer、token、lease、ack 回归不受影响。

### 协议/真实 Companion

- 用现有 1.1.64 body（不加字段）发送合法 `account_set + account_dir`，managed heartbeat 200；
- 缺 account_dir、非法 Windows path 均 200 needs_attention 且 live pair 清空；合法但与 bound 不一致时 200 mismatch，保留观察到的 live pair/last_seen；
- 现有 `companion_version` 被写入 typed agent_version；
- `account_dir_resolved` 不发送、不依赖；
- revoked token 401、disabled 403；
- managed lease/ack 在 B3C 前仍由 gen0 认证拒绝，绝不返回 jobs、绝不接受 ack；heartbeat 200 mismatch 仅表示设备在线；
- Companion 对 200 response 的兼容性和连续 heartbeat 真实验证，不能只做 mock。

### 并发/安全

- 两个 heartbeat 同时到达，last_seen 单调可接受且 live pair 不混合；
- heartbeat 与 owner bind 同时到达，只有新鲜 live pair + 精确 CAS 的 bind 成功；
- heartbeat 与 revoke 同时到达，revoke 后不得继续接受 heartbeat；
- 不同 tenant 使用相同 endpoint/token/字段不能读写彼此状态；
- 所有错误响应不含原始 account_dir、token、config、hash 或内部 SQL。

## 7. Definition of Code Verified

本批只有同时满足以下条件，才可称 B3B3 代码 verified：

- 三路 ownership 的 targeted tests、真实 PG/RLS/trigger smoke、真实 HTTP contract 均通过；
- 基于 `pearnly-companion` 1.1.64 源码的协议 fixture 使用现有 body 通过；
- managed mismatch、unbound、offline、revoked、disabled 的响应报告已留存；
- B3C queue/reservation/finalize/lease/ack 和所有 push 仍明确关闭并有反证；
- 本地真实 PG + 协议 fixture 通过即完成本内部切片的 Code Verified；不单独部署、不称用户功能完成；
- 真实 Windows/production 验证统一留到完整 F1 candidate/B5，最终用户真机 OK 前不得称功能完成。
