# Express Push · 新事务所 onboarding runbook(0 → 能用)

> 一家新会计事务所从零接通 Express 自动记账的全步骤。给运维/PM 照着走。
> 前置:`ERP_PUSH_ENABLED` 已开(已上线);该客户的 express 端点已在 Pearnly 建好(adapter=express)。
> 安全总纲:账套误写 = 账务事故。**写入哪个账套由 Owner 逐端点审批**,未审批一律只 DATAT(测试)。

---

## 名词速记

- **小助手 / companion**:装在客户那台连得到 Express 的 Windows 机上的本地程序(`PearnlyCompanion-Setup.exe`)。出站拉取队列、直写 DBF、夜间 PACK。
- **配对码 `exp_<endpoint_id>_<secret>`**:在 Pearnly 网页「连接 Express」生成,把这台小助手绑到这个 express 端点。
- **账套(account set)**:Express 里一家公司的账(目录如 `\\accserver\ACCOUNT\70EXP\<账套>`)。测试账套 = `DATAT`;真客户用自己的。
- **审批(approve)**:Owner 从小助手上报的候选账套里**选一个**批准为该端点唯一可写账套。不批 = 只能写 DATAT。

---

## 步骤(7 步)

### 1. 装小助手 + 本地配对
- 客户在那台能访问 Express 的机器装 `PearnlyCompanion-Setup.exe`,装完弹**配对窗**。
- ⚠️ 安装包**未签名**(内部测试期):Windows SmartScreen 首次会拦「Windows 已保护你的电脑」→ 点**「更多信息」→「仍要运行」**即可继续安装。
- 填:① Express 账套目录(浏览选,如 `\\accserver\ACCOUNT\70EXP\<账套>`)② **Express 登录账号 + 密码**(本机输入,DPAPI 加密存本机,永不上云 · 见 T1 `15-t1`)③ 粘贴配对码。点「配对」。
- 配对成功 = 配对码有效 + 选的目录是真 Express 账套(有 `ISINFO.DBF`)+ 探测到的账套已上报云端。小助手转后台常驻。

### 2. 探测 + 心跳上报候选账套
- 小助手 `account_probe` 扫 `70EXP` 下所有账套(含 `ISINFO.DBF` 的目录),读公司名/税号,经 heartbeat 上报到云端 `endpoint.config.reported_account_sets`。
- 这就是 Owner 审批时能选的**候选名单**(网页/管理侧 `GET /api/erp/endpoints` 可见)。

### 3. 锁定客户账套(= 授权)
- 端点 `config.account_set` = 这家客户的真账套。**这就是授权**:云端白名单只放行 payload 账套 == 端点 `config.account_set`(逐端点·`account_set_allowed`),配哪个只许写哪个,跨账套一律拒;没配则一张也入不了队。
- 来源:**将来 T5** —— 客户在配对窗从小助手探测出的真实账套列表里**自选自家账套**(认准自家公司名),自动同步到 `config.account_set` + companion 本地锁定(见 §T2-B)。T5 落地前由 Owner/admin 在集成页配置(走现有 ERP 连接鉴权)。

### 4. 设直写方式 `method=dbf`
- DBF 直写是已验证主路(RPA 暂泊,见步骤 7 附注)。配对默认即 `method=dbf`,确认无误。

### 5. 首张真票冒烟验收
- 在 Pearnly 推一张这家客户的真发票:OCR → 置信闸门 → 高置信 + 账套匹配 → 入队 `pending`。
- 小助手 lease → 直写客户账套 DBF → ack `success`(回 Express 单号)。
- **夜间 PACK** 后(或手动触发一次),客户打开自己的 Express 报表/放大镜应能看到这张单(进项报表 241 / 销项 141)。— PACK 是可见性必需步骤,见 `13-pack-necessity-findings`。
- 对账核对金额/分录无误 = 冒烟通过。

### 6. 上线
- 冒烟通过即正式跑。小助手后台拉队列 + 夜间 PACK,无人值守。
- 出错(映射缺/置信低/账套不符)进异常审核队列,不会乱写、不会假成功(状态诚实)。

---

## 安全闸(每张单都过 · 任一不符即拒、零落盘)

| 闸 | 在哪 | 判定 |
|---|---|---|
| 入队白名单 | 云端 enqueue | payload `account_set` == 端点 `config.account_set`(逐端点)· 否则留人工不入队 |
| lease 白名单 | 云端 lease | 载荷账套 == 端点账套 且过逐端点白名单 |
| 写盘目录 / PACK | 小助手 | 写盘目标 + PACK 弹窗真实路径/公司名 == 配对锁定账套(端侧硬闸) |

> fail-safe:端点没配 `account_set`、或 payload 账套与之不符 → 拒(绝不"允许所有")。
>
> ⚠️ **端侧白名单对齐待办**:小助手当前账套白名单(C2/C3)仍按上一版「下发审批值」实现(companion 本地 commit `2634bbd`),与本版云端「端点 config.account_set 即授权」不一致 —— 在 companion 也对齐前,小助手对非 DATAT 账套会回落拒写。真客户端到端前需补一棒 companion 对齐(详见交接报告)。

---

## RPA 录入(暂泊 · 部署期与操作员一次性勘探)

- DBF 直写是当前主路。模拟录入(RPA)的真机键序需「会 Express 的操作员 + 真机」一次性勘探,**一套 Express 版本勘探一次、全客户复用**,定为部署期任务。
- 待 RPA 上线:登录凭证复用 T1 的「Express 登录」(同一份,不另起密码框)。在此之前 `method=dbf`。

---

## 真账套放开的边界(Owner 拍)

本 runbook + T2 机制让「审批某客户某账套」成为**可能且安全**;但具体批准动作仍是 Owner 逐个端点、逐个账套手动做的决定,不自动放开。默认所有端点仍只 DATAT,直到 Owner 显式审批。
