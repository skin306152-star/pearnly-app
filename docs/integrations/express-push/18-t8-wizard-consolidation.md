# T8 施工单 · 网页「连接 Express」向导收口(下载不强制 + 选账套只在小助手)

> 来源:Owner 真机(2026-06-22)。两处 UX 病:① 已装过小助手仍被逼每次重下 124MB 才能生成密钥;② 选账套网页和小助手各一份(重复)。
> 决策(Owner 拍):**账套只在本地小助手选(登录已被迫本地·顺手选·不跳转);网页只显示状态。下载是一次性、可跳过,不挡生成密钥。**
> 施工窗口:pearnly-app(FE `erp-express-wizard.ts`/`erp-express-steps.ts` + 小补后端 heartbeat)。改 `src/*.ts` 必 build + 提交 dist + bump `home.html ?v=`。

---

## 1. 病灶(PM 已读真码)

- **下载强制**:`erp-express-wizard.ts` 进度 = `downloaded + connected + account`(`:147`)。`downloaded` 只有真点下载拉完 124MB 才 true(`:316`)。`_genToken()` `:329` 硬拒 `!S.downloaded`→"请先下载"。已装客户被逼重下。
- **选账套重复**:网页 step3(`erp-express-steps.ts:89` + `_fillAccounts` `erp-express-wizard.ts:233`)渲染可点账套列表;T5 又在本地小助手做了同样的选。两处撞。

## 2. 改法

### 2.1 下载不强制(已装即可直接生成密钥)
- **去掉 `_genToken` 的 `!S.downloaded` 硬拒**(`:329-333`):不下载也能生成密钥。
- **step1 完成判定放宽**:`downloaded || connected` 即算 step1 done —— **小助手能连上(heartbeat)本身就证明装好了**,无需再逼下载。
- step1 加一个次级动作「**我已经装过了 / 跳过下载**」→ 置 `S.downloaded=true`(只是标记 done,不触发下载)。下载按钮保留作便利(没装的人用)。
- **"完成"按钮就绪条件**从 `downloaded && connected && account` 改为 `connected && account`(`:228`)——下载不再是硬门。

### 2.2 选账套只在小助手 · 网页 step3 改"状态镜像"
- 网页 step3 **不再渲染可点列表**,改为**只读状态**:
  - 小助手已上报所选账套(`cfg.account_set`)→ 显示「已选账套:**XXX**(在小助手里选/改)✓」,badge=done,`S.account` 取这个值。
  - 未选 → 显示提示「请在小助手窗口里选择你的账套」,badge=waiting。
- 删 `_fillAccounts` 的点选交互(`:233`)及账套 grid 点击设 `S.account` 的逻辑;`S.account` 来源改为 `cfg.account_set`(`_checkAgent` 轮询里取)。
- `_finish()`(`:406`)**不再用网页选择写 account_set**:`account_set` 以小助手上报为准(镜像 `cfg.account_set`);finish 只存 `auto_push` + 确认连接。

### 2.3 后端小补(让网页有东西可镜像)
- heartbeat(`routes/erp_agent.py`)接收小助手上报的**所选账套** → 存 `endpoint.config.account_set`(现仅存候选 `reported_account_sets`)。即:小助手是账套选择的唯一真相源,云端存它、网页显示它。

## 3. 跨窗依赖(必须对齐 · 否则镜像空转)
- **窗口1(小助手)**:T5 客户在本地选账套后,除锁本地 config,**还要把所选账套随 heartbeat 上报**(→ 云端 `cfg.account_set`)。本单后端(§2.3)接收它。**给窗口1 补一句:选完账套上报 selected account_set。**

## 4. 测试 / 验收
- 已装客户(`downloaded=false`)能直接生成密钥、不被拦;点「我已装过」step1 转 done。
- 没装客户:下载按钮照常工作。
- 小助手连上 → step1 自动 done(无需下载)。
- 小助手里选了账套 → 网页 step3 显示「已选:XXX」只读、不可在网页改;`S.account` 跟上、"完成"可点。
- 小助手未选 → 网页 step3 提示去小助手选、"完成"不可点。
- heartbeat 上报所选账套 → `cfg.account_set` 落库、网页镜像。
- i18n 4 语补齐新文案(已装跳过 / 在小助手里选 / 已选状态)。FE build + dist + `home.html ?v=` bump。≥1 测试。

## 5. 交付
- pearnly-app:`erp-express-wizard.ts` + `erp-express-steps.ts` + heartbeat 小补 + i18n + dist。**未验收不 push**。
- 报告:真机(已装跳过下载生成密钥 / 选账套只在小助手 / 网页镜像)截图 + 单测 + commit。

> 与并行的 T2-A(去白名单·同 pearnly-app)同窗口可一起做(都碰 express 云端·不撞)。窗口1 加"上报所选账套"一句。
