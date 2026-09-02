# ERP LINE 目标、套账与主档一致性合同

> 状态：`P3C_PROD_VERIFIED / FEATURE_FLAG_ALL / P4_CAS_PENDING`
> P3a 底座：`fc9e48b9`；LINE polling 止血：`34606115`；durable refresh + Express
> canonical ingestion：`9247c615`；应用即时派发闸：`fc57650b`；Companion 协议最低版本：`1.1.76`。
> 本文只定义连接、套账、主档与 LINE 选择的一致性边界；第三方 ERP 推送状态继续唯一来自
> `erp_push_logs`，不在这里建立第二套推送状态。

## 1. 用户场景与产品结果

会计可能在同一个 LINE 账号中录入任意客户的采购或销售单。每张新单开始前，系统必须先让
会计明确选择：

1. 业务方向：采购或销售；
2. ERP 连接：MR.ERP 或 Express；
3. 目标套账：MR.ERP 的年度套账，或 Express 的年度/数据根与账套；
4. 记账模式：MR.ERP 的现金/赊账，或 Express 的库存/非库存。

选定后，上传、OCR、编辑、确认、网页推送、小助手领取和第三方 ERP 写入必须使用同一份目标
快照。编辑器显示已锁定的 ERP，不再出现另一个 ERP；套账仍可在确认前显式切换，切换后必须
重新加载该套账的主档和校验结果。

## 2. 2026-09-01 已确认的现状问题

### 2.1 Companion Profile 只有本地身份

`ProfileRecord` 只保存随机 `profile_id`、DPAPI token 密文和 Express 路径，没有 endpoint id、
Pearnly 账号、入口产品或安全 token mask。因此两个 Profile 指向同一公司/目录时，用户无法判断
哪条属于 Cowork、哪条属于 `/erp`。

新增、编辑或暂停 Profile 会停止整个旧 worker。旧 worker 在退出时把所有 Profile 上报离线，
新 worker 再整组启动；所以配置一条连接会让其它连接短暂全部离线。年度/数据根和科目扫描仍是
同步操作，并按 Profile 重复扫描同一个网络目录。WDS 的 `v1.1.69` 日志显示看门狗约每 4–5 分钟
持续重启，说明多 Profile 配置已经存在，但运行时还不是可用的多 Profile 架构。

### 2.2 云端连接与 LINE 目标不是同一身份模型

- Express token 按 endpoint id 独立鉴权，云端没有“同一用户只能一个 token”的限制；生产中
  Cowork 与 `/erp` 两个 endpoint 也是两行不同记录。
- MR.ERP 允许重复创建同凭据、同 `comidyear/seldb` 的 endpoint。生产老板账号目前确有两条
  MR.ERP endpoint 都指向 `15/1`，LINE 因而显示两个相同的 TEST2020。
- ERP LINE 没有 Cowork/DMS 同款 rich menu 资源；菜单在所有 ERP 未 ready 时会把采购、销售
  入口一起隐藏，用户只能看到错误卡。
- 对话选择 target 后直接进入记账模式，没有独立的“年度/数据根 → 套账”步骤。共用编辑器虽有
  套账下拉基础组件，但依赖 target projection 是否提供完整 choices。

### 2.3 主档没有统一 revision

- MR.ERP 商品/客户 listing 按 endpoint 缓存 600 秒；普通读取不会知道第三方已经新增、修改或删除。
- legacy Express 每 1800 秒扫描并上报一份商品/客户快照；最快也可能滞后约 30 分钟。
- managed/shared Express heartbeat 目前只保存在线 Profile，忽略 `account_sets`、科目、映射和
  catalog，因而根本没有可供 LINE 使用的完整主档。
- 当前 draft 只保存 endpoint/account_set 文本，没有保存主档 revision；确认时也没有对“被删的
  商品/客户/科目”做 revision 复核。

结论：现状不能承诺“下一张新单使用第三方 ERP 最新主档”。离线、缓存命中或 heartbeat ACK
只能表示技术链路存在，不能表示主档最新或第三方 ERP 已成功写入。

## 3. 唯一目标模型

### 3.1 四类身份

| 实体 | 稳定主键 | 责任 |
|---|---|---|
| ERP connection | `endpoint_id` | 凭据、adapter、owner/tenant 范围；不能拿显示名当身份 |
| ERP account set | `(endpoint_id, account_set_key)` | MR.ERP `comidyear:seldb`；Express 规范化数据根 + 账套路径 |
| Companion Profile | `profile_id` + `endpoint_id` | 本机 DPAPI token、可访问路径、进程运行态；不得只靠路径识别云端账号 |
| Master snapshot | `(endpoint_id, account_set_key, revision)` | 商品、客户、科目等同一次完整观察结果 |

Connection 的安全展示字段固定为：Pearnly 账号标签、入口产品、endpoint 名称、endpoint id 短码、
token mask。mask 只显示 token 前 3 位和后 4 位，中间统一为 `***`；完整 token 不进日志、不由
云端回读、不以明文写配置。

### 3.2 主档快照

每个套账只有一个 current snapshot，至少包含：

- `revision`：服务端单调递增版本；
- `source_hash`：稳定排序后的完整快照哈希；
- `observed_at`、`last_refresh_attempted_at`、`source_status`、adapter 与采集设备；
- account sets，以及 products、customers、suppliers、units、branches、accounts 的稳定 source id、
  显示标签和 active 状态；
- 表单字段、字段类型、必填状态、选项来源，以及当前可用按钮/动作；
- account sets、master、form schema、capability 四个独立 component revision；
- 完整快照语义：本次缺失的旧行视为删除，不做无限 merge。

`erp_push_logs` 不承载这些字段。主档 snapshot 是选择/校验投影，不是推送队列。
刷新失败只推进 `last_refresh_attempted_at`，不得覆盖最后一次成功来源的 `observed_at` 或 current
snapshot；同一内容重复上报只更新 freshness，不生成假 revision。

### 3.3 单据目标快照

新 draft 必须保存：

- actor、tenant、`connection_workspace_client_id` 与 `workspace_client_id`；
- endpoint id、adapter、account set key；
- 业务方向与记账模式；
- `master_revision`；
- 用户选中的商品/客户/科目 source id 及当时 label snapshot。

历史单保留 label snapshot，不因主档后续改名而篡改历史。新单只使用 current snapshot。

### 3.4 连接授权与单据归属不变量

- `connection_workspace_client_id` 是所选连接的授权与确认前重验锚点 A，不代表票面主体。
- owner 可见但尚未绑定套账的 legacy endpoint 没有 A；确认时必须在同一锁内重验它仍未绑定，
  不能因 A 为空阻断单据归入 B。
- `workspace_client_id` 是票面单据主体 B，统一作为 OCR 历史、采购/销售正式单、Stock Card 与
  `erp_push_logs` 的归属；A 与 B 可以不同。
- legacy 的 endpoint 与 account set 可以作为 B 的推送目标，但 endpoint 原有的 A 绑定不得迁移、
  覆盖或复制到 B。
- managed Express 必须使用 B 自己绑定的 endpoint/Profile，不得跨 workspace 复用 A 的 Profile。
- Cowork 确认只结束 OCR 草稿并按 B 记录推送日志，不创建采购/销售正式单；`/erp` 确认才按方向
  创建正式单，库存商品继续进入 B 的 Stock Card。

## 4. 刷新与确认协议

### 4.1 触发点与性能边界

连接检查与主档刷新是两个状态：ERP online 不等于 master fresh。普通菜单、draft GET、LIFF
打开/保存和状态 polling 只读服务器 current snapshot，绝不在高频交互请求里同步访问第三方 ERP。

当前新单协议固定为：

1. 选择 ERP 类型时创建 endpoint-scope refresh request，立即返回“正在更新”；
2. 用户点击“再次检查”只读 request 状态；成功后从 canonical snapshot 显示最新套账 quick replies；
3. 选择精确套账时创建 account-set-scope refresh request；
4. MR.ERP 云端 worker 或 Express Companion 在后台完成采集并原子发布 snapshot；
5. 确认入账只读 refresh 状态，只有 `succeeded` 才继续，`requested/leased/failed` 均 fail closed。

同一 endpoint/account-set 同时只保留一个 active request；重复点击合并请求，不制造扫描风暴。

### 4.2 MR.ERP

MR.ERP endpoint refresh 只更新套账目录，account-set refresh 才采集该套账的商品与客户；两者均由
云端后台 worker 执行，LINE/Web 请求本身不等待外部 API。成功后原子发布新 snapshot；失败时
保留旧 snapshot 供只读展示，同时 refresh request 标记 failed，确认动作 fail closed。

### 4.3 Express

云端向对应 Companion Profile 发 durable refresh request，并在正常 Agent lease/poll 响应中下发，
所以不必等 60 秒 heartbeat。Companion 对同一 account_dir 只执行一次共享后台扫描；endpoint scope
扫描全部可用套账，account-set scope 扫描精确套账的商品、客户与科目，再随 heartbeat 回传 request
id、scope、目标套账和结果。managed 与 legacy heartbeat 共用同一 canonical ingestion，普通心跳
缺少 catalog 时不得清空上次主档。

该严格协议只对 Companion `>=1.1.76` 启用。旧版本继续原有 snapshot/30 分钟 catalog 行为，保持
可用但不宣称“下一张立即最新”；网页手动 strict refresh 对旧版本返回 update-required。

### 4.4 确认前 CAS

P4 将让确认请求携带 draft 的 `master_revision`，服务端拿 current revision 做 compare-and-swap：

- revision 相同且所选 source id 仍 active：允许继续；
- 仅标签修改：返回最新标签，要求用户确认刷新后的内容；
- 商品/客户/科目已删除或归属套账改变：阻断并要求重新选择；
- 新增了无关主档：可以刷新 revision 后继续，不破坏用户已选行；
- 第三方不可达：诚实显示“无法确认主档是否最新”，不假成功。

适配器写入前再验证 endpoint、account_set 和 revision；第三方返回 HTTP 200、Agent lease/ACK 都
不能替代写后 report/detail readback。

## 5. LINE 和网页交互合同

对话顺序固定为：

`菜单 → 采购/销售 → ERP → 后台刷新/再次检查 → 年度或套账 → 套账主档刷新 → 现金/赊账或库存/非库存 → 上传`

- ERP rich menu 永远可呼出，使用 Cowork/DMS 同款品牌图标与 2×3 六宫格；ERP 不 ready 时入口
  仍在，点击后显示对应连接、配置、套账或主档错误，不用一张总错误卡覆盖整个菜单。
- 目标 picker 按 connection 分组。完全相同凭据/套账的重复 endpoint 显式标为冲突，不生成两个
  看起来相同的选项；迁移只能由 owner 选 canonical endpoint，再迁 workspace/log 归属，禁止静默
  删除或自动合并 token。
- 编辑器锁定对话中选定的 adapter/endpoint，只显示它的套账。允许在该 connection 的合法套账内
  切换；切换即清空旧套账映射和校验结果并强制刷新。
- 商品明细名称占整行、数量/单价/金额另起两列或三列；长名称换行，不能截断为省略号后失去可审计
  内容。

## 6. 分批施工与真机门

### P1 Companion 身份与多 Profile 稳定性

- Profile schema 增加 endpoint/Pearnly 账号/入口产品等安全展示身份，配对成功时由鉴权后的 heartbeat
  返回并持久化；列表显示账号和 `exp***1234` 形式的 mask。
- Profile 增删改不整组上报 offline；只替换受影响 runtime，或在重载交接完成后再关闭旧 client。
- 同 account_dir 的 roots/accounts/catalog 扫描按路径去重、后台化并共享结果；watchdog 能记录准确
  profile 与阻塞阶段。
- 真机：同一 Windows、同一 Express 套账同时绑定 Cowork 与 `/erp`，两边连续 10 分钟 heartbeat
  在线，各自能 lease/ack 且不串 token。

P1 获得真机 `USER_ACCEPTED` 后才进入 P2。

### P2 连接注册表、重复连接治理与 ERP rich menu

- 建立 connection/account-set 投影和 exact-duplicate conflict；先处理现有两条 TEST2020。
- ERP rich menu、六宫格和菜单卡与 Cowork/DMS 对齐；每次入口刷新全部目标状态。

### P3 统一 master snapshot 协议

- **P3a 已实现**：immutable snapshot、current head、normalized items、原子发布、稳定 hash、component
  revision、freshness、租户 RLS 与只读 API。
- **P3b1 已实现并全量打开**：MR.ERP 已接套账、商品、客户 canonical snapshot。同步 live fetch 曾误接
  到 LINE 高频 polling，已由生产 hotfix `34606115` 移除；普通交互恢复 snapshot-only，生产 draft poll
  实测 68ms/61ms。
- **P3b2 待实现**：MR.ERP 供应商、单位、分支、科目及第三方动态字段/按钮尚无已验证 live collector；
  当前 form schema 对这四类明确标 `collector_not_connected`，不得宣称六类已全量同步。
- **P3c 已生产验证**：`9247c615..fc57650b` 增加 durable coalesced request、MR.ERP 后台 worker、
  Express lease/poll 命令、legacy/managed canonical ingestion、LINE 两级 refresh gate 与旧 Companion
  兼容闸。Companion `v1.1.76` 从每次约 3 秒 poll 接收刷新命令，并把 endpoint refresh 限定为 SCCOMP、
  account-set refresh 限定为商品/客户/科目，避免 60 秒 heartbeat 等待和无关 posting 扫描。
- **MR.ERP 生产证据**：endpoint/account 后台刷新分别 1.135s/19.382s；刷新期间 LINE polling
  109/91ms、83/78ms，最终快照 300 商品、111 客户。普通菜单、draft 和状态 poll 未访问第三方 ERP。
- **应用生产证据**：code-bearing SHA `1445fe4c04cef723360d516d58ced957b0943f3b`，Manual CD
  `33614767574`；部署日志 `health check OK after 20s`，production HEAD、systemd service、`/api/health`
  和 `/api/ready` 均回读通过。精确生产 SHA 上协议闸拒绝 1.1.75、接受 1.1.76，功能 flag 仍为 all。
- **Express 真机证据**：Companion commit `4243ee6f`，release run `33613228324`；生产安装包
  62,900,788 bytes，SHA-256=`a0bb4a23e3858e61befbb73cf5b2092148dfa647c44c54b57e89450e9fae645c`。
  Windows 登录用户 session 1 的两个 endpoint 均回报 1.1.76。LINE 绑定 endpoint 的 endpoint/account
  refresh 分别 9.967s/9.986s，期间 LINE snapshot polling 69–87ms；快照含 3 套账、276 商品、552 客户、
  225 科目。内容哈希未变化时 immutable revision 保持不变，但 freshness 的 attempted/observed 时间和
  source 已更新为本次 Companion 1.1.76，不能把“不增 revision”误判为“未刷新”。

### P4 LINE 选择、编辑器和确认 CAS

- 补完整对话中的数据根/套账步骤；编辑器锁 endpoint、可切同连接套账；商品行重排。
- load/save/confirm 全部按 current revision 复核，复用 DMS 编辑器 `force_refresh + invalid_master`
  的成熟 fail-closed 模式。

### P5 推送与第三方写后回查

- 网页、Cowork、`/erp` 使用同一 push reservation 和成功反馈；成功后 LINE 返回单号、ERP、套账、
  方向、金额与外部单号摘要。
- MR.ERP 以 listing/report，Express 以本地表和 Express 报表做写后验收。

每个批次独立完成本地验证、精确 production SHA、Companion 版本和真机证据；未获用户真实设备
OK，不得提前施工下一批。
