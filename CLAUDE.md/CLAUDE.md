# CLAUDE.md · Pearnly 项目大脑
> 每次启动 Claude Code 必须完整读完本文件再开始任何任务
> 本文件 = 项目宪法 · 优先级高于一切临时指令
> 最后更新:2026-05-29(模型升 Opus 4.8 1M · commit 署名 4.7→4.8 · 守门统一 6 道 · 铁律计数 30(2026-06-02 加 #29 大厂质量+收尾simplify / #30 目录重组最后做) · 整顿恢复 + 3 窗口并行 loop · 2026-07-01 封锁整顿期解除→正常产品开发·主线对话 Agent)

---

## 🟢 整顿模式已收官(2026-05-22 起 → 2026-07-01 解除)

**当前状态**:**封锁整顿期已解除(2026-07-01 Zihao 拍板)**。整顿核心(全文件 <500 / 模块化 / 防屎山闸 / 目录重组)已收官(`scripts/refactor_progress.py` 100%)→ 回到**正常产品开发**,当前主线 = **对话 Agent M1**。下方"整顿模式"段与铁律 #18(0 新功能)转为历史;**仍长期生效的是防屎山机械闸(铁律 #23/#27/#28)** —— 新代码照样不许塞巨石、超 500 行 CI 红。活地图只看 `CLAUDE.md/STATE_PEARNLY.md` 顶部状态卡。

<details><summary>历史:封锁整顿期原状态(2026-05-22 → 2026-07-01)</summary>

**当时状态**:**封锁整顿期** · 0 新功能开发 · 仅做工程标准化
</details>

**主计划**:[`CLAUDE.md/REFACTOR_MASTER_PLAN.md`](REFACTOR_MASTER_PLAN.md)(60+ task · 9 阶段 A-I · 单一权威源)

**Codex 协作分流规则**:[`CLAUDE.md/CODEX_COLLAB_RULES.md`](CODEX_COLLAB_RULES.md)(Zihao 说「继续」时先分流:测试项目 / 重整长跑文案)

**接力 agent 进窗口顺序**(治漂移版 2026-05-29 · 别一上来啃 7000 行):
1. 读 **`AGENTS.md`**(项目根 · 唯一一页入口 · 含文档地图 + 今天敲定的认知)
2. 跑 `python scripts/refactor_progress.py`(看**实时**数字 · 永不信文档手写行数)
3. 读 `STATE_PEARNLY.md` 顶部**「状态卡」**(分割线以上 ≤30 行 · 当前 task/最后 commit)
4. 找当前 task → `REFACTOR_MASTER_PLAN.md`「进度看板」· 本文件(铁律细节)按需查
5. 干活 → 6 道守门 → push → **重写** STATE 状态卡 + 主计划进度看板

**禁止**:任何 `MODULE_ROADMAP.md` 新功能 · 任何 P0-VAT 主线 · 任何 Phase 6 进项管理 MVP

**整顿期目标**:Pearnly 工程标准化到 "Google / Anthropic Claude code 级 90%+" · home.js < 200 行 · app.py < 500 行 · 测试覆盖 ≥ 70% · API p95 < 1s

---

## 🔥 2026-05-16 新铁律(高优先级)

### 1. 修一类不修一处(v118.32.5.5.7 拍板)
修 bug 前 **grep 同类 pattern** · 一次性把全项目同类问题全修。**禁止**「用户报一处修一处 · 留尾巴」。
- 例:z-index 修 1 处 · 实际 13 处都有 → 一次批量改
- 例:alert 改 toast 修 1 处 · 全项目搜出来一起改

### 2. ALTER TABLE 必须 `commit=True`(v118.32.5.5.12 踩坑)
`db.get_cursor()` 默认不 commit · DDL(ALTER / CREATE)在 with 块退出时回滚。
- ✅ 正确：`with db.get_cursor(commit=True) as cur:`
- ❌ 错误：`with db.get_cursor() as cur:` 然后 ALTER TABLE
- 现象：日志显示「字段就绪」· 但数据库里列没建上

### 3. Session 1 账号 1 设备(v118.32.5.5.10)
- JWT payload 加 `jti` uuid4 · `users.active_jti` 字段记录最新
- 校验：`token.jti != user.active_jti` → 401 `auth.session_revoked`
- 前端心跳 15s + window.focus / visibilitychange 立即 check
- 老 token(无 jti)或老用户(无 active_jti)= 兼容放行 · 下次登录自动迁移

### 4. PLG 反薅闸 5 道(Korn 拍板 🅱)
1. Trial 30 张 / 3 天(短)
2. 1 账号 1 设备(session 控制)
3. 24h 同 IP 限 3 邮箱(auth_signup 已有)
4. 24h 同 /24 子网限 10 邮箱(auth_signup 已有)
5. 员工共享老板额度(seats 不增配额)

> ⚠️ **不做「admin 审批制」**:฿299/月 价位审批制成本不可行 · 走 PLG 自助制 + 技术反薅是 SaaS 行业标准(Slack / Notion / Stripe / Figma)

### 5. 着陆页禁止真公司名(v118.32.5.5.15)
login.html 着陆页动画客户卡必须用**行业类目假名**(咖啡店/面包房/IT 公司/餐厅)· **禁止**用真实公司名避免商号冒用法律风险。

### 6. 每次部署写 4 语 release_notes(v118.32.5.5.17 拍板 · 2026-05-23 Zihao 升级:勿留历史 + 标准官方语言)
每次部署前 Claude **必须**在 `app.py` `/api/version` 返回的 `release_notes` 字段写 1-3 句 **4 语**更新说明:
- 用户语言:zh / th / en / ja 全 · 缺一不部署
- 大白话 · 让会计师看懂"我能用上啥"
- **禁止**出现 OCR / API / Gemini / batch / SDK / endpoint / lifecycle 等技术词
- 前端 `version-banner.js` 30 秒轮询 `/api/version` · 检测到版本变化 → 顶部弹窗 [查看更新内容] [现在刷新更新] [稍后更新]
- 用户点"稍后"= 30 分钟同版本不再弹
- 实现位置:`static/version-banner.js`(独立 IIFE · 不引 home.js)

**🔒 2026-05-23 Zihao 升级铁律(覆盖式 + 官方语言)**:
- ❌ **禁止 prepend 老版本说明**:每次部署 · `release_notes.zh/th/en/ja` 4 字段**完全覆盖** · 只保留本次更新内容 · 老版本说明全删
- ❌ **禁止口语化 / 卖萌词**:🚨 / 客户反馈 / 我们修了 / 紧急 / 不许 · 用**标准官方语言**(已优化 / 系统更新 / 修复已上线 / 即日生效)
- ❌ **禁止 commit message 风格的说明**:不要"根因" / "修法" / "测试" 等开发术语 · 不要列 commit hash
- ✅ **每条 1-3 句 · 通知体**:开头一句陈述事实(『系统已优化…』『已修复…』)· 后跟 1-2 句具体影响(『用户现在可以…』『此前因…导致…的问题已解决』)
- ✅ 写完先**自检 4 条**:① 是不是只剩本次更新内容(grep 不到 "v 旧版本号") ② 是不是 4 语完整 ③ 是不是用了标准官方语言(非口语) ④ 是不是用户能看懂没技术词
- ✅ 历史版本说明归档:如需保留 · 写到 `release_notes_archived_<vXXX>` 字段(不进公开返回)

**文案示例**(标准官方语言 · 通知体):
- zh: "系统已优化『收入对账』Excel 上传的日期识别。此前因日期格式兼容性不足导致部分账册显示『0 行』· 已修复 · 即日生效。"
- th: "ระบบได้ปรับปรุงการอ่านวันที่ในไฟล์ Excel ของ『กระทบยอดรายได้』· ปัญหาที่บางไฟล์แสดง『0 แถว』เนื่องจากความเข้ากันได้ของรูปแบบวันที่ ได้รับการแก้ไขแล้ว · มีผลทันที"

**禁止反例**:
- ❌ "v118.35.0.37 · 收入对账 3 个余额录入框..." + "— 以下面向用户(不变) —\n\nv118.35.0.36 · ..." (prepend 老版本)
- ❌ "🚨 紧急修复:客户反馈我们的 OCR 抽错..."(口语 + 🚨 表情 + 内部叙事)
- ❌ "根因:openpyxl 返 datetime cell · _parse_date split 4 parts"(技术术语)

### 7. ERP 集成 · 无 API 必走 Playwright · 反向工程代码不留废件(2026-05-18 拍板 · 架构铁律)

**无开放 API 的 ERP 一律走服务端 Playwright** · 不再做 HTTP 反向工程(老 PHP 系统 endpoint 抓包 + form 字段 + cookie session 重放)。

历史教训:v27.8.0 MR.ERP 反向工程虽然实测通了 5 步 endpoint(`mrerp_pusher.py` 430 行)· 但:
- 维护成本极高(MR.ERP 改一个 hidden field 就挂)
- 字节级 xlsx 兼容(sharedStrings vs inlineStr / `<c t="n"/>` 删除属性等)调试 3 天
- 错误信息只能 scrape HTML 关键词(`ไม่พบ` / `ผิดพลาด`)· 极脆
- 站点反爬升级一次 = 全废

Playwright 用浏览器引擎模拟用户 · cookie / JS / 跳转全自动 · 站点改 UI 也只是改 selector · 维护成本是反向工程的 1/10。

**反向工程代码不留废件**:
- ❌ **禁止**保留 `xxx.deprecated` / `xxx_legacy.py` / `xxx_old.py` 文件作"参考"
- ❌ **禁止**在新代码注释里写"参考 xxx_legacy.py 的实现"
- ✅ 抓包/反向工程产出的**先验信息**(URL / 表单字段名 / 数据格式 / 业务规则)全部转移到 `docs/integrations/<vendor>-known-facts.md`
- ✅ 老代码直接 `git rm` · 历史在 git log 里 · 不需要文件层留遗体
- ✅ 项目编年史(`CLAUDE.md/STATE_PEARNLY.md` · `BACKLOG.md` · `MODULE_ROADMAP.md`)可以留版本号记录"v27.8.0 做过反向工程"· 但**不留代码**

适用范围:MR.ERP(无 API · ✅ 适用) · FlowAccount(有 API · 不适用) · Xero(有 API · 不适用)。新接 ERP 评估时优先看是否有 OpenAPI / OAuth · 没有就直接 Playwright。

### 8. 老系统字节级规则 · 真样本 ground truth 铁律(2026-05-18 拍板 · 架构铁律)

反向工程老系统(PHP / .NET / Java legacy)的字节级 / wire-format 规则时,**必须以"verified import 成功的真样本"作 ground truth**,严禁靠文档规则盲调。

**触发场景**(任何 of):
- xlsx / docx / pdf / xml 等容器格式的 ERP 模板
- 老系统 form-encoded multipart 字段顺序敏感
- 字节级 OAuth 1.0a 签名 / TLV 协议
- 任何"格式描述对了但服务端拒收"的情形

**铁律执行**:
1. 取真样本(scp / SaaS export / 业务方提供的"已成功导入过的"原件)
2. **直接字节级解构** · 不靠文档描述(`zipfile` 解 xlsx · `xmllint` 解 XML · `xxd` 看二进制 · 等)
3. **逐字段对照**自己生成的产物
4. **真样本是唯一真理** · known-facts.md 写的是"我们的理解" · 跟真样本冲突时**真样本赢**
5. clone-based 生成 = 复用真样本 metadata(styles / namespaces / 隐藏字段)+ 仅替换业务字段

**历史教训**(v118.27.8 + 本轮 2026-05-18):
- 早期 known-facts.md §6.3 写"补完全空 cell `<c/>` 让 row 显式声明每列存在"
- 第一轮探测上传被拒 `จำนวนคอลัมภ์ข้อมูลไม่ครบ 18 คอลัมภ์`(数据列数不到 18)
- 本能反应想"改空 cell 写法"(盲调假设)
- 拿到 Korn 真样本对照后发现:**真样本就是用完全空 `<c/>`** · 旧规则没错
- 真因是 **styles.xml 索引** openpyxl fallback 用 s=1/2/3 跟 Korn 的 s=2/3/4/5/6 含义冲突 → MR.ERP 按 style 索引判"有效列"数错
- 若没拿真样本对照 · 我们会持续盲调空 cell 写法 · **永远找不到真因**

**适用反例**(以下场景不需要本铁律):
- 有 OpenAPI / GraphQL schema 的现代 API · 文档就是 ground truth
- 自家完全控制的格式 · 没历史包袱
- 已经走 Playwright UI 的 ERP(交互层不涉及字节级)

**操作建议**:
- 接入新老系统前 · 先问业务方拿 1-3 个"verified import 成功的"真样本
- 存到 `docs/integrations/templates/<vendor>_sample_*.<ext>` · 文档化它的来源 + 验证日期
- 写 generator 时优先 clone-based · 兜底再写"从零构造"路径

### 9. 老 PHP 系统响应码 ≠ 业务成功(2026-05-18 实测 · 架构铁律)

老 PHP 系统(MR.ERP 等)的 "process completed" 响应码 **不等于** "数据库真的写进去了"。

**触发场景**:
- `importpc.php` 返 `"2"` ≠ DB 写库成功 · 实际 row 全失败也可能返 "2"(语义是 "处理完毕 · 出报告")
- "Delete Success" splash 页 ≠ 真删了(test01 账号在 TEST2019 上 alldel.php 返成功但 row 还在)
- 任何 HTTP 200 + 自由格式 string body 都可疑

**铁律执行**:
1. 永远不靠老 PHP 系统的"成功码"判定业务结果
2. 业务结果**只看真出口**(报告 xlsx / listing 是否含 row / 重新查 detail 页)
3. adapter 写 verifier 路径:成功路径 + listing/report 二次确认
4. 错误场景写守门测试(整 fail xlsx · 验 adapter 真把 `หมายเหตุ` 翻成 FailedRow)

**适用范围**:MR.ERP(✅ 适用)· 任何无 OpenAPI 的老 PHP / .NET legacy 系统都套这条。

### 10. 所有路由分支必须有"async context not stub"守门测试(2026-05-19 拍板 · 架构铁律)

FastAPI async 路由调 sync 适配器(Playwright sync_api 等)· 单元 sync mock 不算 · **必须**写真 async tripwire 测试。

**触发场景**:
- 路由 handler 是 `async def`
- 路由内部调任何用 `playwright.sync_api` 的 helper(MRERPAdapter / Browser / list_*)
- 走 `await asyncio.to_thread(...)` 不是简单 sync 函数调用

**铁律执行**:
1. 路由必须 `await asyncio.to_thread(sync_helper, args)` · 绝不裸调
2. 守门测试 = 真 `httpx.AsyncClient` + 真 `asyncio.IsolatedAsyncioTestCase`
3. 测试里 patch sync_helper 成 tripwire · 检测 `asyncio.get_running_loop()` · 命中即 raise
4. 路由 = 200 + body.ok=True → 通 · raise = fail
5. sync pytest mock(无 event loop)证明不了"async 不阻塞" · 不算

**已落实**:
- AsyncLoopOffloadTests(test_erp_test_connection_route_dispatch.py)
- 覆盖 5 个路由:test-connection / per-endpoint test-conn / customers / products / push
- v118.34.10/12 修过的真 bug(Playwright sync_api refuses inside event loop)→ 加测试锁定

**历史教训**:v118.34.10 之前 5 个 async 路由全裸调 sync MRERPAdapter · 在 sync pytest 单测里全过 · 真生产里全 RuntimeError。

### 11. 任何外部 listing 拉取必须 retry ≥1 次 + 失败截图(2026-05-19 拍板 · 架构铁律)

调外部网站(MR.ERP / Xero / FlowAccount 等)拉列表 · **不许**一次失败就 fallback to "无法拉取 · 请手动输入"。必须 retry · 失败留证据。

**触发场景**:
- 任何 GET listing 路由(/customers /products /orgs 等)
- listing 抓取依赖 timing(networkidle 之类)
- 用户看到下拉抖动(第一次有数据 · 第二次空)

**铁律执行**:
1. 抓取层(`_fetch_listing` 类):
   - `goto` 后必须 `wait_for_selector(主结果选择器, ≥10s)`
   - timeout 走 `page.reload()` + 再 wait 一次
   - 仍失败 · 存截图 `/tmp/<vendor>_listing_fail_<kind>_<ts>.png` · 路径塞进 exception
2. 路由层:
   - transient 错(ERR_TECHNICAL / ERR_UNEXPECTED / ERR_NETWORK)retry ≥1 次 · 间隔 ≥2s
   - 非 transient(ERR_AUTH / ERR_CRED_DECRYPT / ERR_BUSINESS / ERR_NO_CREDS)立即 bail · 不浪费 login
   - 失败响应**不写缓存** · 解 sticky failure(用户点 2 次都是同样的失败)
3. 守门测试 3 条:
   - 第一次 transient 失败 · 第二次成功 → 路由总成功
   - 非 transient 失败 → 不 retry · 节省 quota
   - 失败响应不进缓存 · 同样 endpoint 重新点要重新 fetch

**已落实**:
- A3 (v118.34.18):services/erp/mrerp_{customer,product}_sync.py:_fetch_listing
- app.py:_fetch_listing_with_retry · /endpoints/:id/{customers,products}
- ListingRetryContractTests 守门测试 3 条

### 12. 状态字段单一 source of truth · 多处 UI 同步取(2026-05-19 拍板 · 架构铁律)

任何 "状态" 字段(推送 / 审批 / 异常等)· 全 UI 只准从**一个**后端字段取 · 不许多字段并存。

**触发场景**:
- 同一笔操作 · 3 处 UI 显示 3 种状态(已推送 / 失败 / 重试中)
- 后端有 `result["success"]` boolean · 但 UI 同时读 HTTP code + body + 自维护乐观字段
- 多个表存"同一个状态"(`erp_push_logs.status` + `ocr_history.last_push_status` + `invoice_records.pushed`)

**铁律执行**:
1. 后端先确定**单一权威源**(典型:`result["success"]` boolean)
2. 所有写库点用同一个 boolean 派生:
   - `erp_push_logs.status = 'success' if success else 'failed'`
   - `endpoint.success_count++ / failure_count++`
   - `ocr_history.last_push_status = 'success' if success else 'failed'`
3. 路由响应**始终带 body.ok 字段**(布尔)· 跟权威源对齐 · HTTP 状态码不传递业务结果
4. 前端**只读 body.ok** · 绝不靠 HTTP 状态码判 success/failure(200 + ok:false 是有效失败响应)
5. 守门测试:推送失败时 mock push_to_endpoint 返 success=False · 验证后端 3 处写入(logs / stats / history)全是 `failed` · response.body.ok 也 False · 不能错位

**已落实**:
- A2 (v118.34.17):home.js _pushOne 改读 body.ok · 不只看 resp.ok
- auto-push toast 文案 4 语调整 · 颜色 success → info
- PushStatusSourceOfTruthTests 守门测试

**历史教训**:v118.34.17 之前 _pushOne 看到 HTTP 200 就弹"已推送"绿 toast · 完全忽略 body.ok=false · 用户看到抽屉 "已推送" + 通知 "失败" + 日志 "失败" 三处矛盾。

### 13. 不许在 sync pytest mock 里证明 async 路由通(2026-05-19 拍板 · 架构铁律)

集成测试(尤其涉及 async FastAPI 路由 + sync 外部库)**必须**真 async + 真打外部 service(或真 tripwire)· sync pytest mock 不算证据。

**触发场景**:
- 测 async 路由(FastAPI `async def`)
- 路由内部跑 sync Playwright / sync `requests` / sync DB
- 测试用 `unittest.TestCase` + MagicMock 替换 sync helper

**铁律执行**:
1. async 路由测试 = `IsolatedAsyncioTestCase` + `httpx.AsyncClient`
2. mock 必须用 tripwire 形式 · 检测 `asyncio.get_running_loop()` · 模拟 Playwright sync_api 的真实行为
3. happy path 也要走真 async 路径(创建 endpoint / push 真发票)
4. sync pytest mock 只算"单元逻辑正确"· 不能 claim "async 路由通"
5. 任何 PR 声明"测试通过"但只跑 sync mock · 算违规 · 必须补 async 集成测试再合并

**已落实**:
- A1 (v118.34.16):PushMRERPAsyncContextTests + AsyncLoopOffloadTests
- 5 个 async 路由覆盖
- happy path / 失败 path / 真 tripwire 三选一

**历史教训**:v118.34.10 之前 138 个单元测试全过 · 但生产里 5 个 async 路由全报 "Playwright Sync API inside the asyncio loop" · sync mock 蒙人。

### 14. 每个窗口启动必须先 check 在 master · 不在就切回去(2026-05-21 拍板 · 最高优先级 · 防"部署撞墙"重复发生)

**症状**:连续几个窗口都遇到同一个 bug — 干完活想部署时撞到 `cleanup-01-v2` 分支挂在 master 前面 5 个 commit · webhook 在 master · push cleanup-01-v2 不触发部署 · cherry-pick 到 master 又撞 4 文件冲突 · 用户每次都崩溃。

**根因**:本地 `git checkout cleanup-01-v2` 留在那里没切回去 · 新窗口启动时 `gitStatus` 显示当前在 cleanup-01-v2 · AI 默认在这分支上干活 · 等部署才发现 push 错地方。

**铁律**:
1. **每个窗口开工前必须跑** `git branch --show-current` · 不是 `master` 就立刻 `git checkout master`(`gitStatus` 里 "Current branch" 写啥就读啥 · 不在 master 就警告 Zihao 然后切)
2. 部署前 push 也必须 `git push origin master`(不是当前 branch · 是显式写 master)
3. 长期保留的 feature branch 必须有明确生命周期 · 不要让一个 4 天前的"待 review" 分支变僵尸 · 要么 PR 合并 · 要么删

**当前僵尸分支**(2026-05-21 起,留在 remote 等 Zihao 决定):
- `cleanup-01-v2` · GPT 写的"旧订阅/BYO API Key 永久下线" v2 · 16 文件 -5684/+210 · 含 login "立即试用→立即注册"重命名 + 8 处 BYO key 代码删除等 · 4 天没 ship
- `feature/credits-system` · 同样 CLEANUP-01 第一版 · 更早的清理工作

**这两条分支处理方案**(等 Zihao 拍板,默认保留):
- A: 想 ship 就在 GitHub 上开 PR `cleanup-01-v2 → master`
- B: 不想 ship 就 `git push origin --delete cleanup-01-v2 feature/credits-system` 永久删除

**不要做的**:不要在 feature 分支上叠新工作(像 v118.35.0.0 OCR 我犯的错)· 永远从 master 开新分支或直接在 master 干。

### 15. 删后端字段必须同步删 Pydantic response_model(2026-05-21 拍板 · v118.35.0.15 踩坑 · 高优先级)

**症状**:v0.11 我从 `_build_user_info()` 删了 8 个老套餐字段(`plan` / `monthly_quota` / `trial_expires_at` 等)· 但**忘了同步改 Pydantic `UserInfo` model**(那些字段仍是 required)· 导致 `/api/me` 抛 `ResponseValidationError 500`(`type='missing', loc=('response', 'plan')`)· 前端 `_userInfo = null` → `renderSettings()` 早退 → "套餐&用量"面板空白。
我连改 3 次 CSS/i18n/渲染逻辑都没修好 · 真根因是 API 500 · 不是前端。

**铁律**:
1. 改后端返回 dict 的字段(增/删/改名)· **必须 grep `class XxxInfo` / `response_model=XxxInfo`** · 同步更新 Pydantic schema
2. 改 schema 时 · 兼容老调用者:**删字段先改 Optional + default None** · 一个迭代后再真删
3. 改完**用 token 直接 curl `/api/<endpoint>` 看 HTTP 状态** · 不要只看前端 UI 截图 · 500 是 backend 在喊救命
4. 前端报"渲染异常 / 数据空 / 早退"· 第一步:`curl -H "Authorization: Bearer $TOKEN" /api/<endpoint>` · 不是 grep CSS

**触发位置自检**(改 _build_xxx / dict 返回时必读):
- `class UserInfo(BaseModel)` · `class TenantInfo(BaseModel)` · 凡是 FastAPI 路由 `response_model=` 指向的 model
- 删 dict 字段 → grep `loc=.*'<字段名>'` 看是否有测试 fixture · grep `XxxInfo` model 类
- 改字段名 → 全局 grep 旧名(后端 + 前端)

**已落实**:
- v118.35.0.15 修了 UserInfo · 把 8 个老字段全改 Optional · 加了 4 个新 credits 字段
- 后续删字段:不直删 · 先 Optional 一版 · 部署后下版再删 schema 字段

---

### 16. 全档位 push 授权 · Claude 写完直接部署(2026-05-21 拍板 · C 档位 · Zihao 信任前提)

**背景**:之前每次 `git push origin master` 都要 Zihao 单独说"授权 push"· 因为 webhook 自动部署 = push 即上线。Zihao 在 2026-05-21 选择 C 档位(全部授权)· 取消每次询问。

**铁律**:
1. **Claude 写完代码 + 自测后 · 可以直接 `git commit` + `git push origin master`** · 不再每次问"授权 push"
2. **仍保留的红线**(必须问):
   - `git push --force` / `--force-with-lease` 到 master(可能擦掉 Zihao 在本地的未推 commit)
   - `git reset --hard` / `git revert` / 删除 tag / 删除 branch(任何破坏 git 历史的操作)
   - `git push --no-verify` 或绕过 pre-commit hook
   - 大于 30 个文件改动的"重构级" commit(让 Zihao 先 review)
   - 涉及 `db.py` schema migration · 删表 / 删字段 / `DROP` 任何东西
   - (登录/注册/OCR/计费等核心路径**不再要求改前汇报**:2026-06-12 起按铁律 #26 自做自检即 push · 自己跑对应真账号 E2E 验过即可)
3. **Claude 主动做的事**:
   - 每次 push 后 · 在回复里**告知用户 commit hash + 改了什么 + 部署 ETA**(约 15s 后用户能访问到新版本)
   - 失败的 webhook / 部署 · 主动检查 `/api/version` 看 cache_bust 是否更新 · 没更新就报警
   - 重大改动 push 前 · 主动跑本地测试(`pytest` / `curl` / `playwright`)· 测过再 push
4. **Zihao 的撤回权**:任何时候可以说"切回 A / B 档"· Claude 立即恢复每次询问机制

**适用反例**(以下场景仍要问):
- Zihao 明确说"先别 push" / "等我看看"
- Claude 自己**不确定**改动是否正确(预感有 bug)
- 改动会**影响生产数据**(charge / refund / 删用户数据 / migration)

**触发位置自检**(每次 push 前内心 checklist):
- [ ] 改动是否触发上面"红线"任意一条 → 是 → 停下问 Zihao
- [ ] 本地是否在 master 分支(铁律 14)
- [ ] 改动是否经过自测(至少 grep / curl / 编译过)
- [ ] commit message 是否说清楚 why(不是 what)
- 全过 → 直接 `git commit` + `git push origin master` + 汇报 hash

**已落实**:
- 2026-05-21 拍板 C 档位 · 取消每次"授权 push"询问
- 红线 6 条仍保留 · Claude 触发任意一条必须停下问

---

### 17. 新功能禁止塞巨石文件 · 必须独立模块(2026-05-22 拍板 · EXECUTION_PLAN 阶段 5 Task 5.3 落地)

**背景**:Pearnly 当前现状 — `app.py` 10k 行 · `home.js` 30k 行(单函数 12,694 行)· `home.css` 7k 行 · `db.py` 4k 行 · 改一处容易牵连 · 我用屎山治理铁律(2026-05-15)开始渐进翻新,但**新功能继续往巨石里怼**就治标不治本。这条铁律封死"再往大文件加内容"路径。

**铁律 · 4 不许**:
1. **新后端路由不进 `app.py`** · 必须建独立 router(`xxx_routes.py`)· 顶部 `from xxx_routes import router as xxx_router; app.include_router(xxx_router)`
   - ✅ 例:`billing_routes.py`(Task 5.1) · `report_routes.py` · `auth_signup.py` · `recon_routes.py` · `vat_excel_routes.py`
   - ❌ 反例:在 `app.py` L9XXX 新加 `@app.get("/api/new-feature")`
2. **新前端 JS 不进 `home.js`** · 必须独立 `.js` 文件(IIFE 模式 · 跟 `static/version-banner.js` 同款)
   - ✅ 例:`static/version-banner.js` · `static/admin/admin.js` · `static/admin/admin-i18n.js`
   - ❌ 反例:在 `home.js` 加新 module 函数
3. **新 CSS 不进 `home.css`** · 必须独立 `.css` 或 scoped 到组件 `.html`
   - ❌ 反例:在 `home.css` 加新 `.new-feature-card { ... }` 类
4. **新业务 SQL 不进 `db.py` 尾部** · 复杂业务封装到 `services/<domain>/<feature>.py`
   - ✅ 例:`services/erp/mrerp_product_sync.py` · `services/monitoring.py`
   - ❌ 反例:在 `db.py` L4XXX 加 `def get_new_feature_data():`

**例外条款**(允许暂塞 · 但必须留迁出计划):
- 必须在 commit message 显式说"暂存 app.py / home.js · 迁出 deadline = vXXX 或 YYYY-MM-DD"
- 必须建 `TECH_DEBT.md` entry 或 `EXECUTION_PLAN.md` 任务
- 超过 deadline 没迁出 = 下个窗口必须先迁再做新事

**自检清单**(Claude 每次开新功能前内心 checklist):
- [ ] 这是后端 API?→ 不许加在 `app.py`,建 `xxx_routes.py`
- [ ] 这是前端模块?→ 不许加在 `home.js`,建 `static/xxx.js` 或独立 `.html`
- [ ] 这是 db helper 函数?→ 简单 CRUD 可以加 `db.py`(数十行)· 复杂业务建 `services/`
- [ ] 全过 → 写代码;有任意一条违反 → 停下选独立文件 / 跟用户讨论

**为什么这条铁律拖到 5.22 才立**:屎山治理铁律(5.15)说"不推倒重来 · 渐进翻新" · 但"新功能去哪里"那时没说清。Task 5.1 抽 billing router 完成 · 验证了"独立 router + include_router" pattern 跑得通(本机 + CI + 生产三层验证)· 现在有信心强制要求。

**附:CONTRIBUTING.md**:同时新建项目根 `CONTRIBUTING.md` 给协作者(包括所有 Claude 窗口)看 · 是这条铁律的完整版本 + 真实文件结构示例。

---

### 18. 整顿期封锁 · 0 新功能开发(2026-05-22 拍板 · ⚠️ 2026-07-01 已解除 · 见文件顶部"整顿模式已收官" · 本条转历史)

**背景**:Zihao 2026-05-22 决策"封锁整顿 5-8 个月 · 路径 B 上 Vite + ES modules · 把项目工程标准化到 Google / Anthropic Claude code 级"。立项理由:
- 当前 1 个真实付费用户(mrerp@outlook.co.th) · 没大量真实用户 · 是工程整顿的黄金窗口
- 切换 3-5s 延迟 / BUG 反复修 / 砍掉功能死灰复燃 · 都是地基不稳的症状
- AI vibe-code 项目通病:前期快速跑业务 · 后期烂得改不动 · 现在不整顿后面更难

**铁律**:整顿期(2026-05-22 起到约 2026-12)**0 新功能开发**:
- ❌ **禁止**回 P0-VAT v4.9.6 主线(等整顿完再做)
- ❌ **禁止**开 Phase 6 进项管理 v118.40 MVP(等整顿完)
- ❌ **禁止**任何 `MODULE_ROADMAP.md` 里的新功能 task
- ❌ **禁止**为 LINE / Gmail / Gemini API 加新业务
- ✅ **只做**`REFACTOR_MASTER_PLAN.md` 里的 9 阶段 task
- ✅ **允许例外**:紧急 BUG 修复(影响付费用户 / 数据安全 / 服务中断)

**接力 agent 自检**:进窗口先 grep `MODULE_ROADMAP.md` 想做新功能 → **立即停** · 跟 Zihao 确认。

**例外条款**:Zihao 明确说"破例做某新功能" → 加到 REFACTOR_MASTER_PLAN.md 进度看板的 ❗ 例外段 + 入档原因。

---

### 19. 整顿期接力 agent 必读 4 文档(2026-05-22 拍板 · 防接力跑偏)

**背景**:9 阶段 100+ task 不在一个窗口能干完 · 跨窗口接力时如果文档不读全 · 必然跑偏(找不到下个 task / 重复做 / 跳过依赖)。

**铁律**(治漂移版 2026-05-29 · 必读顺序 · 由小到大别贪多):
1. **`AGENTS.md`**(项目根 · 唯一一页入口 · 文档地图 + 今天敲定的认知 · **先读这个**)
2. 跑 `python scripts/refactor_progress.py`(实时数字 · 不信任何文档手写行数)
3. **`CLAUDE.md/STATE_PEARNLY.md`** 顶部「状态卡」(分割线以上 ≤30 行)
4. **`CLAUDE.md/REFACTOR_MASTER_PLAN.md`**「当前进度看板」找下一个 task + 该 task"完成判定"段
5. **`CLAUDE.md/CLAUDE.md`**(本文件 · 30 条铁律 · 细节按需查 · 重点铁律 18-20 整顿段)(在主计划对应 task 行)

**进窗口前检查**(60 秒):
```
1. git branch --show-current → master(铁律 #14)
2. 读上面 4 文档
3. TaskCreate 创建本窗口任务列表(基于主计划下一个 task)
```

**触发"不读文档"违规**:
- commit message 没 REFACTOR-XX task ID → 没读主计划
- 改了 `MODULE_ROADMAP.md` 里的新功能 → 没读铁律 #18
- 没跑 6 道守门就 push → 没读铁律 #19 接力 protocol

---

### 20. 整顿期 commit message 必含 REFACTOR-<task-id>(2026-05-22 拍板 · grep 防偷懒)

**背景**:屎山治理需要可追溯 · 必须能 git log grep 出哪些 commit 在做整顿 · 哪些在偷做新功能。

**铁律**:整顿期 commit message **必含**对应 task ID:

格式:
```
<type>(<scope>): <subject> · REFACTOR-<task-id>

<body 说改了什么 · 为啥 · 怎么验证>

守门 6 道全绿:format / unit / imports / i18n / node / build

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```

**例子**(整顿期标准 commit):
- `refactor(frontend): 装 Vite + 配 esbuild · REFACTOR-A1`
- `refactor(backend): 抽 settings router · REFACTOR-B1`
- `test(e2e): 加登录 E2E · REFACTOR-D1`
- `chore(ci): 加 black + ruff lint · REFACTOR-A5`
- `docs(adr): ADR-001 选 Vite 不选 Webpack · REFACTOR-G1`

**唯一例外**(整顿期允许不带 task ID):
- 紧急 BUG 修复(影响付费用户)· commit message 必须以 `hotfix:` 开头
- 文档微调(typo / 链接修)· commit message 以 `docs:` 开头即可

**审计**:每月末 Zihao 跑 `git log --since='1 month ago' --grep='REFACTOR-' --oneline | wc -l` 看整顿 commit 数 · grep 不出 task ID 的 commit 单独看 · 不该出现"偷做新功能"。

---

### 22. CI 状态可视化能力(2026-05-23 拍板 · 接力 agent 入门必读)

**触发**:Zihao 2026-05-23 装 gh CLI + 登录 · Claude 可以直接看 GitHub Actions CI 状态(之前没装 · 一直靠用户贴日志)

**能力**:在 Claude Code session 用 PowerShell tool 调 gh CLI:
- 路径:`C:\Program Files\GitHub CLI\gh.exe`(absolute · 不依赖 PATH 刷新)
- 已登录账号:`skin306152-star`(token 存 keyring · 跨 session 持久)
- Repo:`skin306152-star/pearnly-app`(私库 · gh 已认证)

**关键命令**(接力 agent 进窗口可直接用):

```powershell
# 1. 看 master 最近 N 个 CI run 状态(快速排查 push 后是不是绿)
& "C:\Program Files\GitHub CLI\gh.exe" run list --repo skin306152-star/pearnly-app --branch master --limit 5

# 2. 看某个 failed run 的详细日志(找哪 step 挂了)
& "C:\Program Files\GitHub CLI\gh.exe" run view <RUN_ID> --repo skin306152-star/pearnly-app

# 3. 看 failed step 的具体错误输出
& "C:\Program Files\GitHub CLI\gh.exe" run view <RUN_ID> --repo skin306152-star/pearnly-app --log-failed | grep -E "FAIL|ERROR|AssertionError" | head -20

# 4. 列所有 open PR + CI 状态(查 dependabot 等堆积)
& "C:\Program Files\GitHub CLI\gh.exe" pr list --repo skin306152-star/pearnly-app --state open --json number,title,statusCheckRollup

# 5. 关 PR(如 dependabot 红 PR · 加 ignore 规则后清理)
& "C:\Program Files\GitHub CLI\gh.exe" pr close <NUMBER> --repo skin306152-star/pearnly-app --comment "<reason>"

# 6. 重跑 CI(transient checkout fail / network 抖动)
& "C:\Program Files\GitHub CLI\gh.exe" run rerun <RUN_ID> --repo skin306152-star/pearnly-app
```

**优先用 PowerShell tool 调** · 不用 Bash(bash session PATH 没刷新到 gh)。

**典型场景**:
- 用户问 "CI 红了什么意思" → 跑命令 1 + 2 + 3 · 一次性给报告
- Push 完想 verify → 跑命令 1
- Dependabot 红 PR 堆积 → 跑命令 4 + 5(改 .github/dependabot.yml 加 ignore 后关 PR)
- CI transient fail(`/usr/bin/git exit 128` · 网络抖动)→ 跑命令 6 重跑

**bash 调用兜底**:gh.exe 在 git bash 也能用 · 用绝对路径 `/c/Program\ Files/GitHub\ CLI/gh.exe ...`(注意 escape 空格)。但 PowerShell tool 调更稳。

**已知 dependabot 配置**(2026-05-23 状态 · 接力 agent 接手时确认):
- `.github/dependabot.yml` 含 ignore 规则 · 排除 `google-ai-generativelanguage`(防 google-generativeai 0.8.x pin 冲突)
- 8 个 open dependabot PR 堆积(2 红 + 6 绿)· 6 绿需要本地 `pip-compile` regen lock 才能 merge(REFACTOR-A7 流程 · CONTRIBUTING.md §依赖管理)
- Node 20 deprecation 2026-09-16 到期 · #2/#3/#4 PR 已开升级 actions/checkout@v5+ / setup-python@v6 等 · 留给 REFACTOR-A5/A6 整顿期统一升

---

### 21. 整改期不污染未来整顿(2026-05-23 拍板 · 整改期专属 · 防整改变新整改对象)

**背景**:2026-05-22 启动 OCR + 对账 4 模块整改(`docs/audits/2026-05-22-ocr-recon-audit.md`)· 整改优先级 > 整顿。但整改本身要写新代码 / 改老代码 · 如果不严格执行 · 整改完 home.js + app.py 又胖一圈 · 等于给未来整顿期 +2 月。本铁律就是『整改新代码必须按整顿期"理想形态"写』· 一次写对 · 整顿期省事。

**触发**:整改期(Phase 0-3 期间 · 大约 2026-05-22 → 2027-02)所有 commit 必守。

**7 条执行规则**:

1. ❌ **新 DB 业务函数禁止进 `db.py`** · 必须进 `services/<domain>/*.py`(如 `services/memory/field_correction.py` / `services/ocr/template_memory.py`)
2. ❌ **新路由禁止进 `app.py`** · 必须建 `*_routes.py`(如 `memory_routes.py` / `correction_routes.py`)· 用 `app.include_router()` 接入
3. ❌ **新前端模块禁止进 `home.js`** · 必须独立 IIFE 文件(如 `static/correction-panel.js` / `static/memory-feedback.js`)· 跟 `static/version-banner.js` 同款
4. ❌ **新 CSS 禁止进 `home.css`** · 必须独立 `.css`(如 `static/correction-panel.css`)或 scoped 到组件 HTML
5. ✅ **新 DB schema 走 Alembic**(借整改 P1.1 之机激活 A2.2 + B3 第一次真迁移 · 不再 `ensure_*` 偷渡 · 同步加 git-deploy.sh 钩子)
6. ✅ **删字段先 Optional + default None · 一个迭代后再真删**(铁律 #15 渐进删除范式 · 老 `_anchor_overrides` 等不直删)
7. ✅ **每个 BUG-FIX-P 任务必加守门测试**(契约测试 + 集成测试 · 给整顿期 D 阶段免费加分)

**遇到"不进巨石不会"怎么办**(2026-05-23 Zihao 拍板):
- **Claude 自判断**:能独立尽量独立(优先)· 真的不行(比如改老 modal 现有 DOM)就在巨石里加 · **但必须在 commit message 透明说明**:
  ```
  ⚠️ 暂塞 home.js L29630-29812(+183 行) · 原因:本次改老 settings modal 现有抽屉 ·
  抽出新 IIFE 要重写 250 行 vendor binding 逻辑 · 工时超本 task 2 倍
  迁出 deadline:REFACTOR-C1 阶段拆 home.js 时一并搬出
  ```
- 透明 = 整顿期 grep 能找到 · 不偷渡
- 不透明 = 算违规 · 接力 agent 看不出 · 等于偷渡新债

**整改期净增长账(每月跑 1 次)**:
```bash
# 整改 Phase 0-3 启动前 baseline:
home.js  33254 行 · home.css 16124 行 · home.html 6566 行 · app.py 9212 行 · db.py 9255 行

# 整改完判定(预期):
home.js  35000 行(+1750 容忍范围 · 全部走铁律 #21 透明记录)
home.css 16500 行(+400 容忍 · 同上)
home.html 7200 行(+650 容忍 · 同上)
app.py   9500 行(+300 容忍 · 严守独立 router)
db.py    9500 行(+250 容忍 · 严守 services/ 化)
```

超出容忍 = 整改没按铁律 #21 走 · Zihao 拉回。

**整改帮整顿提前的部分**(reward 不只是损失):
- **REFACTOR-A2.2 + B3 第一次 Alembic 真迁移**:借整改 P1.1 schema 完成 · 整顿期 -2 个 task
- **REFACTOR-D1 集成测试 +5-10 个**:整改加守门 = 整顿测试覆盖率提升 3-5%
- **REFACTOR-C 模块化目标 +3-5 个文件**:`services/memory/*.py` / `memory_routes.py` / `correction-panel.js` 等

净账目预期:整改完 · 整顿期 deadline 顺延约 3 月(原 2026-12 → 2027-02-03)· 不是 6 月。

---

### 23. 整顿期 8 条硬门槛(2026-05-23 Zihao 拍板 · 比一般规矩更硬)

**背景**:Zihao 2026-05-23 在 A5(CI lint)收尾时拍板,把 8 条工程标准升级为整顿期"硬门槛"——违反任意一条 = 偷渡新债。**权威详版见 `REFACTOR_MASTER_PLAN.md` 顶部"🔒 整顿期 8 条硬门槛"段**,本条是浓缩索引。

**A. 止血(不让旧债继续长)**
1. `app.py` 封死:不许新增 `@app.*` 路由 · 新路由进 `*_routes.py`(强化铁律 #17 / #21)
2. `db.py` 封死:不许新增 `ensure_*` · 新 schema 只能 Alembic(强化铁律 #21 #5)
3. `home.js` 封死:不许新增业务模块 · 新前端业务逻辑只能进 `src/home/*`(Vite ES 模块)
   - ⚠️ **此条更正铁律 #17 / #21 旧措辞"放 static/xxx.js IIFE"**:自 A1 上 Vite 后,新业务逻辑一律 `src/home/*`;只有完全独立的小组件(version-banner 类)才留 `static/*.js`。

**B. 测试(每动一处留网)**
4. 每拆一个模块,必须带一个守门测试(无测试不算拆完)
5. 每个核心业务路径至少一个 E2E / integration 测试(登录 / 注册 / 上传识别 / 销项核查 / 收入对账 / ERP 推送 / 充值)

**C. 度量(数字不许造假)**
6. coverage 不死磕 70% · A8 先建 baseline · 之后**每月只准升不准降**(棘轮 · 降了 CI 红)
7. `/ready` 必须能真实失败(B4 落地时)· 任一依赖挂 → 返非 200 · 永远 ok = 没有
8. `scripts/refactor_progress.py` 必须诚实(数对位置 `src/home/*` · 不写死指标 · 每类按目标封顶)· ✅ A5 已修

---

### 24. 部署磁盘卫生 · 防 /tmp 撑爆硬盘(2026-05-24 拍板 · 血泪根因 · 高优先级)

**背景**:2026-05-24 付费用户 mrerp 银行对账报 `Unexpected token '<', "<html>..." is not valid JSON`。一路彻查(排除超时/大文件/内存/代码 bug)· 真因 = **服务器 52G 硬盘 100% 满**(`df -h /` 显示 `Avail 0 / Use% 100%`)→ Nginx 写不下上传文件请求体(`/var/lib/nginx/body/` `pwrite() failed (28: No space left on device)`)→ 直接返回 HTML 500 → 前端 `res.json()` 解析 HTML 抛 `Unexpected token '<'`。罪魁 = `/tmp` 堆了 28G 的 `pip-unpack-*` / `pip-install-*`(每次部署 pip 解压 torch ~2.7G 不清理 · ~9 次部署累积撑爆)。

**铁律**:
1. **每次部署前看一眼磁盘**:`ssh root@45.76.53.194 "df -h /"` · 用量 > 85% 必须先清理再部署(别等 100% 崩)。
2. **每次部署后清 pip 临时残留**:部署流程 / git-deploy.sh 末尾 `rm -rf /tmp/pip-*`(pip 解压 torch 残渣,删了下次自建)。
3. **报"上传/对账 500 + `Unexpected token '<'`"第一反应查磁盘**:`df -h /` + nginx error.log 找 `No space left on device` —— 这是头号嫌疑,**不是代码 bug、不是超时、不是文件大**。
4. **排障经验值**(2026-05-24 实战):① 500 而非 504 = 不是超时;② uvicorn 日志里查不到那个 POST = 请求卡在 Nginx 没到应用;③ nginx 默认日志 `/var/log/nginx/{access,error}.log` 半夜轮转后可能 0 字节(logrotate 没 `nginx -s reopen`)· 真错误在 `error.log.1` 里;④ `du -sh /tmp/* | sort -rh` 一眼看出谁吃光磁盘。

**根治措施(2026-05-24 起落地)**:git-deploy.sh 加部署后 `rm -rf /tmp/pip-*` + 每日 cron 清 1 天前 pip-* 残留 + 磁盘 85% 告警。

---

### 25. Claude 自己跑测试-修复-验证全闭环(2026-05-24 拍板 · 不再把命令丢给用户)

**背景**:Zihao 2026-05-24 原话「下次自己跑测试,自己跑日志,自己修复,自己复测,自己修复」。以前 Claude 把 ssh/测试命令贴给用户手动跑,来回慢且割裂。现在 Claude 端到端自驱。

**铁律(改 bug / 验功能时全程自己来)**:
1. **自己 SSH 进生产抓真因**:报 500/异常 → `ssh root@45.76.53.194 "journalctl -u mrpilot --since '5 min ago' | grep -iE 'Error|Traceback'"` 抓真实栈,**不猜根因**(本轮 DOCX 500 即如此抓到 `ModuleNotFoundError: docx`)。只读诊断(查日志/查库/git push/跑脚本)自己跑;**仅 prod 写操作**(装包/重启/改数据)被安全闸拦时才请 Zihao 点一下。
2. **自己跑真站点验**:真 token(找 Zihao 要·用完即弃·别提交)+ 真文件 + 真账号打 `pearnly.com` 真接口,自己读返回/扣费/余额/日志,**不靠 sync mock 蒙**(呼应铁律 #13)。
3. **复测必在「重启后的新进程」上**:后端改动部署慢,`/api/version`=200 ≠ 新码生效 → 用 `systemctl show mrpilot -p ActiveEnterTimestamp` ≥ push 时间再复测(本轮踩过:旧进程上测出假结果)。
4. **测真扣费/写库用唯一内容**:防文件指纹缓存命中导致复验失真(塞 nonce)。
5. **测→修→复测→修,直到真站点真账号端到端 PASS**才算完。测出真 bug 必加守门测试(铁律 #21.7)。
6. **诚实**:做不到/没测到直说,不画饼。
> 详细测试方法论模板见 `docs/refactor/adr-006-universal-importer.md` §9(每片都照做)。

---

### 26. 所有改动自做自检即 push(2026-06-12 Zihao 拍板 · 取代旧「高敏区·Zihao 在场」两档制)

**背景**:旧版本把改动分「🟢安全区自动 / 🔴高敏区永远需 Zihao 在场」两档,是整顿期(没真用户、怕动核心路径)的产物。Zihao 2026-06-12 拍板:**整顿已收官,这套在场闸不再需要 —— 所有改动一律自做、自检 OK 即 push,不分高敏低敏、不等任何人在场。**

**统一政策**:任何改动(含登录/注册/计费/OCR/auth/session/LINE/POS 离线等过去算「高敏」的)→ 自己写 → 自己跑全套自检 → 绿了直接 `git commit` + `git push origin master`。**不再「开 PR 留草稿等 Zihao 在场」。**

**自检标准(push 前必须真绿 · 这才是闸,不是「谁在场」)**:
1. 13 道机械闸全绿(见 `docs/GATES.md` · pre-push 本地硬拦)
2. 改了的核心路径**自己跑真账号 E2E**验过(登录/计费/OCR/POS 离线等改了就验对应流程,别只信单测)
3. 改坏了**自己回滚**:E2E / 线上冒烟红 → `git revert` + push,绝不把红的留在 master

**仍保留的少数硬线(与「在场」无关 · 是数据/历史安全)**:
- **不碰真付费用户余额**:Pearnly 无自动支付通道,充值=真实银行转账+截图+人工审核→只改内部额度台账(`tenant_credits` 数字),系统不自动移动真实金钱、无自动退款路径。测试可自由跑充值/扣费/审核全流程(只改测试账号台账·Earn 可重置),**唯一边界=只动测试账号,绝不碰 mrerp 真余额**。
- **破坏 git 历史的操作仍问**:`--force` 推 master / `git reset --hard` / 删 tag / 删 branch(沿用铁律 #16 红线)。
- **删表/删字段/DROP 仍谨慎**:schema 改只走 ensure_*/Alembic 双跑(铁律 #5),删字段先 Optional 一版(铁律 #15)。

---

### 27. 防屎山 4 条机械闸(2026-05-28 Zihao 拍板 · 窗口 C 拍 · 单一权威)

**背景**:Pearnly 巨石史(home.js 33k → 6k · app.py 10k → 4.5k · db.py 9k → 1k · home.html 6.5k → 4.4k)证明:**靠人自律不靠谱**,必须把"不许再涨"做成 CI 机械闸,否则下一波 vibe-code 又会糊回去。本条 4 件套是窗口 C 给整顿期落地的硬门槛 · 跟铁律 #17 / #21 / #23 配套(那 3 条是"不许塞" · 本条是"塞了就 CI 红")。

**4 条机械闸**(脚本在 `scripts/check_file_size.py` + `scripts/check_line_ratchet.py` · CI `lint-size` job 跑):

1. **任何代码文件超 500 行 = push 失败 · 必须先拆**
   - 监控清单(可在 `scripts/check_file_size.py` 顶部改):`app.py` / `db.py` / `home.js` / `home.html` / `home.css` / `auth_signup.py` 等历史巨石 · 加上**所有** `*_routes.py` / `services/**/*.py` / `src/home/**/*.{js,css}`(新建的也算)
   - 例外白名单(可显式豁免 · 必须写注释为啥):暂时不拆 home.html 1000 / home.js 200 等目标值 · 走"per-file ceiling"
   - 触发:`python scripts/check_file_size.py` exit 1 → CI red
2. **任何 commit 让被监控文件行数比上一 commit 多 = push 失败**(棘轮 · 只许减不许增)
   - 实现:`scripts/check_line_ratchet.py` 跑 `git diff HEAD~1 HEAD --numstat` · 监控文件 +N > 0 即 fail
   - 例外:必须在 commit message 显式写 `RATCHET-EXEMPT: <file> +<N> · <理由>` · 脚本 grep 跳过(同铁律 #21 透明记录范式)
3. **新功能必须新建独立文件 + 带 1 个测试 · 否则 push 失败**
   - 落地依赖 PR 模板自检 + reviewer 拍门 + CI 端只能做"测试目录新增"软提示(无法真验"是不是新功能" · 主要靠人 + 铁律 #28 4 问)
   - 强化措辞:新增 `xxx_routes.py` 必带 `tests/unit/test_xxx_routes_contract.py`(已有 30+ 例 · pattern 是 `*_routes_contract.py` / `*_store_contract.py`)
4. **替换旧功能 · 旧代码必须同一 PR 删掉 · 不许两套并存**
   - 例:抽 `services/billing/charge.py` 出 db.py · 同一 commit 必删 db.py 老 `charge_ocr` 函数(本会话 B2 拆搬删模式)
   - 反例:新建 `services/X/store.py` 但 db.py 老函数留着 + 加 re-export shim 假装"零调用点改"——shim 必须打 `# 兼容 re-export · 删除 deadline = vXXX` 注释,deadline 过了下个窗口必须删 shim 才能开新事

**CI 模式**(窗口 C 阶段):
- **当前(2026-05-28 起)**:`continue-on-error: true` warning 模式 · CI 红但不挡 push · 等窗口 A/B(Loop 1)拆完巨石(app.py / home.js 等都到目标 < 500/< 200)再切 fail 模式
- **切换条件**:`python scripts/refactor_progress.py` 显示代码规模平均 ≥ 80% + Zihao 拍板"切硬门" · 把 `.github/workflows/ci.yml` `lint-size` job 的 `continue-on-error` 删掉
- **切完之后**:整顿期任何新 commit 涨监控文件 = CI 红挡 push · 这条铁律就活了

**与铁律 #17 / #21 / #23 的关系**:
- #17 / #21:不许新东西塞巨石(预防 · 全靠人自律 + reviewer)
- #23:8 条硬门槛(预防 + 度量 · 部分有 script 兜底)
- **#27(本条)**:塞了就 CI 红(机械闸 · 不靠人 · 是 #17 / #21 / #23 的"自动化兜底")

**完整设计决策见**:`docs/refactor/adr-010-anti-bigfile-mechanism.md`

---

### 28. 新功能 4 问流程(2026-05-28 Zihao 拍板 · 窗口 C 拍 · AI 写代码前必答)

**背景**:窗口 C 复盘 Pearnly 屎山史 · 共识:AI vibe-code 写"先实现再说"是巨石主要源头(home.js 单函数 12,694 行就是这么来的)。本条是**写代码前 30 秒强制问答** · 卡在 AI 拿起键盘那一刻 · 4 个问题答不出来不许开写。

**触发**:写**任何新功能**(新路由 / 新前端模块 / 新 db helper / 新 service)前 · AI(包括 Claude / Codex / Copilot 抓人)必须在思考链里**显式回答 4 问**(不一定要写到 commit · 但要写到 PR 描述或思考里 · 可被 grep / reviewer 检阅)。

**4 问**:

1. **【领域】这是什么领域?**(billing / auth / OCR / recon / erp / line / archive / settings / 其他)
   - 答不出来 = 跨领域设计没想清楚 · 不许开写
   - 答出来后:本功能要进对应 `services/<领域>/` 或 `<领域>_routes.py`

2. **【新建什么文件】不许塞巨石 · 必须独立**(对应铁律 #17 4 不许)
   - 后端 API:`<新名>_routes.py` 或并入已有 `<领域>_routes.py`(原则:能独立尽量独立)
   - 后端业务:`services/<领域>/<feature>.py` · 不进 db.py
   - 前端:`src/home/<feature>/*.js` · 不进 home.js
   - 写出**确切路径**(不准说"就放 utils 吧")

3. **【测试在哪】每个新文件必带 ≥ 1 测试**(对应铁律 #23 / 硬门槛 #4)
   - 后端契约测试:`tests/unit/test_<名>_contract.py`(pattern 见 30+ 现存例)
   - 后端集成:`tests/integration/test_<feature>.py`(API + 真 DB + Mock 外部)
   - 前端关键路径:`tests/e2e/<NN>-<name>.spec.js` 或 `tests/visual/<name>.spec.js`
   - 写出**确切测试路径** + **至少 1 个测试用例名**(不准说"等会儿加")

4. **【删什么旧文件】替换旧实现的必须同一 PR 删**(对应铁律 #27.4)
   - 如果是全新功能(无旧件)· 写 `N/A · 全新功能`
   - 如果是替换(老 `_extract_summary_fields` 抽到 services 等):**列出要 `git rm` 的旧文件 / 老函数行号** · 同一 PR 内删干净
   - **禁止**留两套并存"先观察一阵子再删" — 那一阵子永远不到

**自检**(AI 开写前内心 checklist):
```
[ ] 1. 这功能属哪个领域?      → ____
[ ] 2. 新建什么文件?(确切路径) → ____
[ ] 3. 测试在哪?(确切路径 + 用例名) → ____
[ ] 4. 删什么旧文件?(N/A 或 git rm 列表) → ____
4 问全填 → 开写
任意 1 问填不出来 → 停 · 跟 Zihao 讨论或先做拆解
```

**违反场景**:
- AI 直接在 `app.py` 加 `@app.post("/api/new-thing")` → 没答问 2 → 违反 → revert
- AI 抽 `services/X/foo.py` 但 db.py 老 `foo` 函数没删 → 没答问 4 → 违反 → 同一 PR 删干净
- AI 加新功能但没建 test 文件 → 没答问 3 → 违反 → 补测试再 push

**与 PR 模板的关系**:`.github/PULL_REQUEST_TEMPLATE.md` 已有"是否塞巨石自检" · 本条 4 问可作 PR 模板下个版本的扩展段(窗口 C 暂不强加 · 等铁律 #27 切硬门时一并加)。

**完整设计决策见**:`docs/refactor/adr-010-anti-bigfile-mechanism.md`

---

### 29. 大厂质量常驻 + 收尾跑 simplify(2026-06-02 Zihao 拍板 · 任何窗口任何任务都执行 · 非一次性)

**两条常驻铁律**,不是某次任务的要求,是**每个窗口、不管做什么活都默认带着干**:

1. **所有源码去 AI 味 · 注释按大厂走 · 所有"路数"(做法/工程实践)按大厂走。**
   - 去 AI 味(新旧码都要):无废话注释 / 无"我注意到·顺便·让我们" / 无 emoji 注释 / 无防御冗余 / 无泛化命名(`data`/`temp`/`result2`)/ 无调试残留(console.log/print)。
   - 大厂注释:**解释 why 不解释 what** · 简洁 · 必要才写 · 别逐行翻译代码。
   - 大厂路数:命名 / 结构 / 错误处理 / 测试 / 提交都按 Google/Anthropic 级习惯 · 别 vibe-code 凑合。**写新代码当下就做到**,不是事后补。
   - 机械兜底:pre-push 第 7 道 `check_ai_smell.py` 只拦注释 emoji + console.log(本次改动文件)· **能机械的归机械,其余靠人主动做全**。全套 Definition of Done = `docs/ENGINEERING_STANDARD.md`。

2. **每次 Zihao 说"收尾"(今天到这 / 换窗口 / 下班 / 睡觉 / 总结一下 等收尾词)→ 主动先跑 `/simplify`**(扫本窗口改动做 reuse/简化/效率/altitude 收口)**再出收尾报告**。别等 Zihao 点。

**Why**:Pearnly 是 AI vibe-code 项目,屎山史就是 AI 味 + 凑合路数堆出来的;整顿期要把质量拉到大厂级,这两条是常驻质量闸。同步写进全局 `~/.claude/CLAUDE.md` + `AGENTS.md`(§2.6/§7)+ 记忆 [[standing-rules-bigtech-quality-simplify]],三处每窗口必读。

---

### 30. 代码目录重组 = 最后做(2026-06-02 拍板 · 2026-06-03 ✅ 执行上线)

**✅ 已完成(方案B · Zihao 2026-06-03 拍板)**:根目录 122 个平铺 .py 搬入包结构 · app.py 留根(入口 `uvicorn app:app` 不变):
- `routes/`(58):全部 `*_routes.py` + `recon_routes_*` 分拆 + `erp_routes_access`
- `core/`(4):`db` `auth` `route_helpers` `kms_helper`(横切基础设施)
- `services/<域>/`(60):复用**已存在的**顶层 `services/` 包(212 文件按域分)· root 业务模块归进对应域 + 新建 `vat`/`report`/`excel` 子域
- **方案B 而非 `app/` 外壳**:顶层已有成熟 `services/`(db 业务下沉产物)· 建 `app/` 需连搬 212 文件 import(blast radius 翻倍)· 故顶层新建 `routes/`+`core/`、业务复用现有 `services/`(只动 root 122 · 现有 212 文件 import 纹丝不动)。
- **变换范式**(854 处机械改写 · verbatim):`import M`→`from PKG import M`(保 `M.attr` 用法)· `from M import`→`from PKG.M import`· patch/setattr/import_module 参数位的 module path 字符串(收窄到调用内 · 杜绝误伤 i18n key `"auth.x"`/文件名 `"db.py"`)· `sys.modules["M"]` key 同步。前缀重叠按模块名长度降序处理。
- **三类测试修复**:① sys.modules 注入未恢复(`.get/.pop` 漏改 key → fake 模块毒化全局)② f-string 动态 patch `patch(f"recon_routes.{k}")`③ 静态审计 `open(ROOT/"x_routes.py")` 硬编码路径 → 加 `routes/`。
- **守门脚本同步**(否则盲区假绿):`check_file_size`/`check_line_ratchet` 加 `routes/**` `core/**` glob · `refactor_progress` `db.py`→`core/db.py`。
- **验证**:全量 2176 单测全绿 · `ruff F821` 零漏改 · `import app` 275 路由全注册 · 守门 4 道绿。mrerp live integration 测试(连真实 MR.ERP·缺凭证则 skip)与重组无关。

---

## 🧭 导航 IA 铁律(2026-05-15 拍板 · 最高优先级 · 覆盖所有 UI 重排)

**Pearnly 全局导航 = 跟着 `D:\Users\Skin\Desktop\pearnly_project\pearnly_nav_prototype_final.html` 走**

**唯一基准文件**:`pearnly_nav_prototype_final.html`(Zihao 提供 + 头像菜单升级版)
**核心 PRD 文件**:
- `CLAUDE.md/NAV_IA_PRD.md`(导航 IA 主 PRD · 8 Phase 路线)
- `CLAUDE.md/MODULE_EXPENSE_PRD_v2.md`(Phase 6 进项管理模块 · 对标 Paypers 一比一+超越 · 3 周)
**优先级**:P1 平行主线 · 不抢 P0-VAT 资源 · 嵌入 P0-VAT 间隙跑

**4 类账号 + 看到啥**(详见 NAV_IA_PRD §2.2):

| 角色 | 看付费按钮 | 看测试中心 | 看管理员后台 | 进哪个 layout |
|---|---|---|---|---|
| 员工(tenant_role=employee) | ✗ | ✗ | ✗ | home.html |
| 老板(tenant_role=owner) | ✓ | ✗ | ✗ | home.html |
| skin(老板 + 测试白名单) | ✓ | ✓ | ✗ | home.html |
| Earn(超管) | — | — | ✓ | **/admin layout 独立** |

> ⚠️ **Earn 铁律不变**:永远只看 /admin · 不进 home.html UI

**8 Phase 切片**(详见 NAV_IA_PRD §4)· **2026-05-15 全部完成**:
- Phase 0 · 文档体系建立 ✅
- Phase 1 · 顶栏三件套(头像菜单 + 搜索框 + Cmd+K) ✅ v118.33.1.0
- Phase 2 · sidebar 重复入口清扫 ✅ v118.33.2.0
- Phase 3 · sidebar 集成一级入口 ✅ v118.33.3.0
- Phase 4 · "即将" badge 大清扫 ✅ v118.33.4.0
- Phase 5 · sidebar 业务流分组(销项▾/进项▾)✅ v118.33.5.0
- Phase 6 · 进项管理完整模块 🚫 永久跳过(等独立开 v118.40 · 子 PRD `MODULE_EXPENSE_PRD_v2.md`)
- Phase 7 · 集成模块独立化 ✅ v118.33.7.0
- 视觉皮肤对齐 11 轮 ✅ v118.33.7.1 → v7.11
- Phase 8 · **Admin Layout 独立**(admin SPA 完全独立 · 不引 home.js)✅ v118.44.0 → v118.44.0.7

**NAV-IA 主线已收官** · 接下来等 Zihao 拍板:回 P0-VAT 收尾 / 开 Phase 6 进项管理 v118.40 / 其他

**Earn 铁律精确化**(2026-05-15 拍板):**不工作 · 只管账户 + 看成本** · Admin layout sub-nav 砍剩 2 项(成本追踪 + 用户管理)· 原 PRD 的"平台概览/操作日志/API 健康度"全删

**铁律不变项**:
- ❌ 不改后端 API(`/api/auth/me` 已返 3 个 flag · 不动)
- ❌ 不动 P0-VAT 主线代码
- ❌ 不破坏现有功能(只重排入口)
- ❌ 不动 i18n 字典 zh→en→th→ja 顺序(新 key 按 th→en→zh→ja 加)

**冲突优先级铁律(2026-05-15 v118.33.7.3 拍板)**:
- 🥇 **prototype_final.html 实物视觉** > 📄 PRD 文字描述
- PRD §3.2 写"加 CTA 上传发票" · 但 prototype 没这按钮 → 按 prototype · 不加(我 Phase 3 加了又在 v7.3 撤掉)
- 视觉/交互冲突时 · 一律以 prototype 为最终基准 · PRD 写错的地方就是 PRD 错 · 不是 prototype 错
- 不需要问 Zihao "PRD 跟 prototype 哪个对" · 默认 prototype 对

**视觉对齐铁律(2026-05-15 v118.33.7.x 累积)**:
- ~~主色:纯黑 `#111111`(不用深蓝)· active / 主按钮 / focus 都黑~~ **【2026-05-29 Zihao 改判·覆盖】全站统一按钮系统:主按钮 = 品牌蓝 `#2563EB`(hover `#1D4ED8`/active `#1E40AF`)· 强调=琥珀橙 `#F59E0B`(仅充值/升级 1 转化按钮)· 标准见中央 `static/home-38-buttons.css`(REFACTOR-WB-C)。**【2026-06-05 Zihao 拍板·定调】全站按钮/切换(.btn-primary / toggle / switch / filter active / .xxx-act-btn 等)一律品牌蓝 `var(--btn-blue)` `#2563EB`,不用黑;**只有左侧导航栏(sidebar)保黑作当前位置指示**。机械硬闸:`check_ui_consistency.py` D2(按钮/切换黑底基线 0),进 pre-push 拦推送。**【2026-06-23 Zihao 拍板·覆盖】① D1「禁新增抽屉 `.drawer`」闸已取消(抽屉右侧滑出·边看原图边改字段·比弹窗好用·当初加错)·抽屉/弹窗按场景自由选。② 按钮/品牌色**以 CSS 令牌为准**:走 `var(--btn-blue)`/`var(--brand)`,**值看 `static/home-01-base.css`(当前主题是紫 `#7C4DFF`·暗色 `#A974FF`)**——上面写的 `#2563EB`(蓝)是早期标准、已过时,别再当真值引用,只认令牌不认写死 hex。**
- 背景:暖灰 `#f4f4f0`(应用主背景)
- 卡片:白 `#fff` + 淡边框 `#e8e8e3`(浮在暖灰背景)
- 浅蓝 info 提示色保留 `#DBEAFE` + `#1E40AF`(prototype 也这样)· 其他蓝色一律去
- drop 区:浅暖灰底 + 灰虚线 → hover 黑虚线(不变背景)
- 字号:body 13px(不用 14px)· nav-item 13px · 顶栏 48px(不用 56px)

**接力 sequence**:任何窗口开"继续"→ 读本段 + STATE_PEARNLY.md NAV-IA 当前 Phase → 读 NAV_IA_PRD §4 Phase X → 干 → 自动推到 Phase X+1

---

---

## 🌐 4 语并重铁律（2026-05-13 · 最高优先级 · 覆盖之前"泰语主语言"版本）

**Pearnly = 4 语言 SaaS（中 / 英 / 泰 / 日）· 4 语都是真正的产品语言 · 都要做扎实**

- 泰国是 **GTM 首发市场** · 不是唯一市场 · 未来有中国 / 英语 / 日本客户 · 都是真用户
- Zihao 交流继续中文（母语）· 但**中文界面是给中文客户用的** · 不是调试键

**默认语言策略：**
- 浏览器 `Accept-Language` 检测 → 用户母语优先
- 检测不到 → 默认泰语（首发市场 GTM 起点）
- 用户登录后可设语言偏好 · 存数据库

**i18n 字典顺序（开发优先级 · ≠ 重要性）：`th → en → zh → ja`**
- th 第一：首发市场 GTM 用
- en 第二：国际通用
- zh 第三：中文市场
- ja 第四：日本市场
- ⚠️ 这只是字典里的字段顺序 · 不代表"其他不重要"
- 📌 **工程备注**：home.js 存量 i18n 字典块顺序为 `zh→en→th→ja`（历史原因 · 重排风险高 · 不动）· 新增 key 在各自语言块内按 `th→en→zh→ja` 原则写入即可

**文案设计规则：**
- 每条新文案 · 4 语并重思考：泰国会计师 / 国际标准英文 / 中国会计师 / 日本会计师
- ❌ 禁止"中文写完直接谷歌翻译"
- 不确定的术语 · 用 Gemini 出本地标准词
- 关键术语参考：対账 = กระทบยอด · 销项税 = ภาษีขาย · 进项税 = ภาษีซื้อ

**UI 排版规则：**
- 按最长语言留宽（通常泰语 / 日语）
- 4 种语言切换都不能出现溢出 / 折行 bug
- 验收必须切到所有 4 语言检查

> ❌ 禁止：任何功能"先做一语 · 其他语言留空" = bug
> ❌ 禁止：默认语言写死 `zh`（除非是中文专属功能）
> ✅ 每个功能必须 4 语完整 · 缺一个 = 立刻修

---

## 🧹 屎山治理铁律(2026-05-15 启动 · 渐进翻新)

**Pearnly 当前现状 · 大白话**:home.js 1.3 MB / 3 万行 · 一个函数 12,694 行 · `showToast` 同名定义两次(真 bug)· 106 处错误吞咽 · 0 测试 · 是个"盖到 30 层的违章楼"

**不推倒重来**(里面住着 mrerp / BAKELAB / TIPCO 等真实付费客户)· **改用渐进翻新**:
- 每个接力窗口在干主任务前 · **挑 1 件 P0 或 P1 债务修了**(0.5-2 小时)
- **新功能不再往 home.js / home.css / home.html 里塞** · 全部独立文件
- 老代码不动 · 等某模块完全被新版替代后再删

**完整路线图 + 待修清单 + 新代码标准**:见 `CLAUDE.md/TECH_DEBT.md`

**接力 agent 必读 TECH_DEBT.md 的 3 段**:
- §2 待修清单(挑 1 件做)
- §3 新代码标准(写新代码必须遵守)
- §5 已修清单(修完后打勾 + 写日期 + 写窗口名)

**测试机制**(skin 账号是测试账号 · 改了 UI 必给清单):
- 接力窗口完成时 · 如果改了 UI 或加了新功能 → **给一份 skin 账号专属测试清单**(用户手动跑)
- 有 Playwright 自动测试覆盖的项 · 跳过手动清单(自动跑就行)
- 目前 Playwright 0 项 · 全部靠手动 → P0 第一件就是补 Playwright 烟测

---

## 项目一句话定位

Pearnly = 泰国会计事务所 + SME 老板的 AP 自动化 SaaS
强项：多语言 OCR（泰中日）+ 全管道自动化（LINE/邮件/文件夹）+ ERP 中立中间件 + 一页多发票拆分
核心口号：「不让用户换 ERP · 让 Pearnly 适配所有 ERP」

---

## 服务器 & 基础设施

| 项 | 值 |
|---|---|
| 域名 | https://pearnly.com |
| 服务器 | root@66.42.49.213 · Vultr **Singapore** · Ubuntu 24.04 · /opt/mrpilot/ ·(2026-06-11 迁同区·DB 1ms·仅 SSH key 登录·**东京 45.76.53.194 回滚兜底留至 ~06-18 勿动**)|
| 数据库 | Supabase PostgreSQL · AWS ap-southeast-1 |
| 邮件 | Gmail SMTP · hello@pearnly.com |
| LINE Bot | @pearnly · Channel ID 2010309291 |
| SSH | 免密已配置（id_ed25519）· 不再需要密码 |

---

## 本地文件结构

```
D:\Users\Skin\Desktop\pearnly_project\
├── CLAUDE.md                        ← 本文件（项目宪法）
├── STATE_PEARNLY.md                 ← 当前状态（每次会话末尾自动更新）
├── BACKLOG.md                       ← 任务清单
├── MODULE_ROADMAP.md                ← 12 模块路线图
├── DESIGN_SYSTEM.md                 ← UI 设计规范
├── MODULE_SALE_VAT_RECON_PRD.md     ← P0-VAT 需求文档
├── app.py · auth_signup.py · db.py  ← 后端源码
├── home.html · home.js · home.css   ← 前端源码
├── login.html                       ← 登录页
├── _pkg\                            ← 打包临时目录（自动清理）
└── yichang\                         ← Zihao 截图存放
```

服务器路径：后端 .py → /opt/mrpilot/ · 前端 → /opt/mrpilot/static/

---

# 🧠 核心工作模式（最重要）

## 1. 文件地图 · 按任务类型自动读

每次启动必读：
- **CLAUDE.md**（本文件 · 规则）
- **STATE_PEARNLY.md**（当前状态 · 下一步任务）

按任务类型加读：
- 选下个任务 / 排期 → 加读 **BACKLOG.md**
- 改 UI / 样式 / 新组件 → 加读 **DESIGN_SYSTEM.md**
- 新功能 / 改模块 / 新业务逻辑 → 加读 **MODULE_ROADMAP.md**
- P0-VAT 销项税相关 → 加读 **MODULE_SALE_VAT_RECON_PRD.md**
- 涉及多模块 / 不确定 → 全读

**动态学习：**
- 每次完成版本后，自动更新 STATE_PEARNLY.md
- 新铁律 / 架构决策 / 重要 bug 修复 → 自动追加到对应 .md
- 项目根目录任何 .md 都是真相来源
- Zihao 扔进新 .md / .pdf / .json → 启动时扫一遍，识别用途告知

---

## 2. 自动推进模式（Zihao 只说"继续"时）

如果 Zihao 开窗口只说"继续"或不指定任务：

1. 自动读 CLAUDE.md + STATE_PEARNLY.md + BACKLOG.md
2. 找当前最高优先级下一个任务（P0 > P1 > P2）
3. 一句话告知："接下来做 X · 预计 Y 分钟 · 影响 Z 文件"
4. 等 5 秒（Zihao 输任意字 = 暂停讨论 / 不输 = 默认同意）→ 自动开干
5. 干完自动打包部署
6. 给出**核心场景必测清单**(项数不限 · 每项 ≤30 秒能验证完 · 重大版本可分段测)
7. Zihao 测完说"过" → 自动接下一个任务
8. Zihao 测完说"有问题" → 暂停修 bug，不继续推进

**需要先讨论的情况（必须先问 Zihao）：**
- 改架构 / 加新模块 / 改数据库表结构
- 涉及付费功能 / 套餐配额
- 改影响多客户核心逻辑（OCR / ERP 推送）
- Zihao 提了多个可能方案需要选

简单 bug / 文案 / 样式调整 → **直接干，不问**

---

## 3. 沉默原则（绝对重要）⭐⭐⭐

**默认沉默 · 不主动喷专业知识**

除非以下情况，否则不要主动告诉 Zihao 一堆技术细节：

✅ **可以主动提的（仅限）：**
- 重大事件（数据丢失 / 服务挂了 / 严重 bug）
- 影响模块功能（某功能即将被破坏 / 兼容性问题）
- 影响用户体验（用户会困惑 / 流程不顺 / 性能问题）
- 影响产品未来（架构债 / 安全隐患 / 商业风险）
- Zihao 的方案有明显问题（避免他踩坑）

❌ **绝对不主动说：**
- 用了什么算法 / 框架 / 库
- 代码内部实现细节
- "顺便科普一下..." 这种主动展开
- 同一个问题反复解释
- 用专业词显示自己懂
- "我注意到..." 这种没人问的观察

**Zihao 是产品经理 + 编程小白**，他要的是：
- 这个功能好了没？
- 用户用起来顺不顺？
- 下一步做什么？

## 4. 详细展开的时机（仅限关键词触发）

**只有 Zihao 主动说以下话术，才详细科普：**
- "调研" / "对比" / "分析"
- "科普" / "解释" / "为什么"
- "教我" / "讲讲"
- "深入" / "详细"

平时**话越少越好** · 让 Zihao 专注测试和决策。

---

## 5. 收尾模式 · 关键词触发

当 Zihao 说以下话术，启动收尾流程：
- "今天到这" / "今天就到这"
- "明天再做" / "明天继续"
- "换窗口" / "新窗口"
- "下班" / "睡觉" / "结束"
- "总结一下" / "保存进度"

**收尾流程（自动执行 · 不要问）：**

1. 扫描本次会话做了什么：完成的版本号 / 新功能 / 修的 bug / 新决策 / 遗留问题 / 改过的文件

2. 对照每个 .md 判断是否需要更新：
   - STATE_PEARNLY.md → 几乎每次都要更新
   - MODULE_ROADMAP.md → 模块进度有变化才更新
   - BACKLOG.md → 完成版本 / 新增任务才更新
   - DESIGN_SYSTEM.md → 有新 UI 规范才更新
   - MODULE_SALE_VAT_RECON_PRD.md → 需求有变化才更新
   - CLAUDE.md → 有新铁律才更新

3. 不需要更新的跳过（省时间）

4. 需要更新的：直接改 · 给 diff · 默认通过 · 自动保存

5. **收尾报告（最后一条消息固定格式）：**
```
┌─────────────────────────────────────┐
│ ✅ 本次会话总结                       │
├─────────────────────────────────────┤
│ 完成版本：v118.32.X.X                │
│ 主要产出：（3 行内 · 大白话）        │
│ 已更新文档：STATE / BACKLOG          │
│ 未更新（无变化）：DESIGN / ROADMAP   │
│ 下次启动直接说：继续                 │
│ 遗留 bug：（如果有 · 列前 3 条）     │
├─────────────────────────────────────┤
│ 🟢 可以安全关窗口了                  │
└─────────────────────────────────────┘
```

6. 出完报告就停手 · 不要继续做新任务

---

# 🚀 部署 & 打包铁律

## ✅ 新部署方式：Git Push（2026-05-17 拍板 · 永久替代 scp）

**彻底绕开 fail2ban · 代码自动备份到 GitHub · 服务器自动重启**

### GitHub 信息
- 私库：`https://github.com/skin306152-star/pearnly-app`
- 服务器 remote：`pearnly`（via SSH key `/root/.ssh/github_pearnly`）
- Webhook secret 存于服务器 `/opt/mrpilot/.env` → `GITHUB_WEBHOOK_SECRET`

### 每次部署流程（Claude 自动执行）

```
1. git -C "D:\Users\Skin\Desktop\pearnly_project" add -A
2. git -C "D:\Users\Skin\Desktop\pearnly_project" commit -m "vXXX · 说明"
3. git -C "D:\Users\Skin\Desktop\pearnly_project" push origin main
   → GitHub 收到 push → webhook 触发 pearnly.com/internal/deploy
   → 服务器自动 git pull + cp 到 static/ + systemctl restart mrpilot
4. sleep 6 → curl https://pearnly.com/api/version 验证
```

**注意：本地 remote 名叫 `origin`，指向 GitHub `pearnly-app` 私库。**
**本地 branch 名：`master`（历史原因 · 不改）**

### 备用方案（git push 失败时用 scp）

如果 GitHub 暂时不可用，回退 scp 方式：
```
1. tar -czf /tmp/deploy.tar.gz home.html home.js home.css app.py auth.py auth_signup.py db.py [其他改动.py]
2. scp /tmp/deploy.tar.gz root@45.76.53.194:/tmp/
3. ssh root@45.76.53.194 "cd /tmp && tar xzf deploy.tar.gz -C /opt/mrpilot/ && cp /opt/mrpilot/home.* /opt/mrpilot/static/ && systemctl restart mrpilot"
```

### Webhook 接口
- 路径：`POST /internal/deploy`（app.py 已实现）
- 鉴权：GitHub HMAC-SHA256 签名验证
- 执行：`/opt/mrpilot/git-deploy.sh`

**Zihao 视角看到的只有：**
```
✅ v118.32.X.X 已上线
核心场景必测(项数不限 · 每项 ≤30s · 重大版本可分段)：
1. xxx
2. xxx
...
```

**禁止：**
- 多步 mv / 手动 systemctl restart
- 输出 deploy.sh 内部细节
- 长篇技术解释
- 任何单项 >30 秒能测完的清单

---

## 版本号规则

- 格式：`v118.主模块.子任务.微版本`（如 v118.32.4.0）
- 每次发版 cache bust 必须递增（home.js?v= 和 home.css?v=）

## 路径规则

- Zihao 本地：`D:\Users\Skin\Desktop\`
- 项目目录：`D:\Users\Skin\Desktop\pearnly_project\`
- 打包目录：`D:\Users\Skin\Desktop\pearnly_project\_pkg\`
- 截图目录：`D:\Users\Skin\Desktop\pearnly_project\yichang\`
- 绝不使用占位符（<xxx> / [VAR] / TODO / FILL）
- 不确定路径 → 先问

---

【部署后输出 · 严格遵守】

每次部署成功，只输出这两块：

1️⃣ 核心场景必测清单(2026-05-13 拍板新规则)：
   - **数量**：覆盖本版改动就行 · 项数不限 · 重大版本可分段测
   - **原则**：每项 ≤30 秒能验证完
   - 只写本版新加/改动的核心路径
   - 不写老路径、测试中心已覆盖的、4 语切换
   - 用大白话写（不写"验证 XX API 返回 200"，写"点 XX 按钮看有没有反应"）
   - 每项格式:"测试 X · 路径 XXX · 看 YYY · 预期 ZZZ"

2️⃣ 其他什么都不说

【重大问题处理规则】

部署后如果发现"重大问题"（仅限以下）：
- 数据可能丢失
- 影响付费用户体验
- 安全漏洞
- 影响产品商业模式
- 破坏现有功能

→ 不要自动修
→ 告诉 Zihao：①问题是什么 ②在哪个文件/位置 ③建议怎么改
→ 让 Zihao 决定怎么处理

【自动改 vs 报告 Zihao 自己决定】

✅ 直接改（不打扰 Zihao）：
- 文案错别字 / 翻译错
- 样式微调（颜色 / 间距 / 字号）
- 小 bug 修复（非核心流程）
- 文档自动同步（STATE / BACKLOG 等）

❌ 只报告位置 · Zihao 自己改：
- 重大架构调整
- 影响多用户的核心逻辑
- 涉及付费 / 配额 / 权限
- 数据库表结构
- 任何"重大问题"

改完给我看 diff

---

# 🎨 UI & 设计铁律

## 语言（i18n · 史上最严铁律 · 漏一个都算违规）

### 4 语必须全覆盖

任何用户能看到的文字必须有 4 语：中文 / 泰文 / 英文 / 日文
默认语言是泰文（用户主要是泰国人）

### 必须翻译的"全部"清单（一个都不能漏）

✅ 所有按钮文字（保存 / 取消 / 上传 / 删除 / 重试...）
✅ 所有标签文字（label / form 字段名）
✅ 所有占位符 placeholder（输入框灰字提示）
✅ 所有 tooltip / hover 提示
✅ 所有错误信息（红色报错 / "xx 字段必填"）
✅ 所有成功提示（绿色 toast / "保存成功"）
✅ 所有空状态文字（"暂无数据" / "还没有客户"）
✅ 所有 modal 弹窗标题 + 内容 + 按钮
✅ 所有小字提示（"支持 PDF · 单次 500 个" 这种灰色辅助文字）
✅ 所有状态 chip（"进行中" / "已完成" / "异常"）
✅ 所有菜单项 + 子菜单
✅ 所有 confirm 弹窗（"确定要删除吗"）
✅ 所有日期格式 / 数字格式（泰文用佛历？还是公历？默认公历）
✅ 所有验证规则提示（"密码至少 8 位"）
✅ 所有进度条文字（"AI 识别中..." / "上传 3/10"）
✅ 所有引导文字（onboarding 步骤说明）
✅ 后端返回给前端的错误码对应文案

> **【4 语 i18n 完整性铁律】** 任何用户能看到的文字都要 4 语化(中/英/泰/日)：
> - 文件名（下载 / 上传文件命名）
> - 文档内容（Excel sheet 名 / 表头 / 使用说明）
> - 邮件 / Slack / LINE 通知文案
> - 错误提示
>
> **不许写死中文 · 一旦发现 = bug · 立刻修**

> **【i18n 区域分级铁律】（2026-05-13）**
>
> | 区域 | 适用 | 语言要求 |
> |---|---|---|
> | 🌍 **对外功能**（vex / sv / sale / recon / upg / pay / line / plan / team / sidebar / dashboard / 异常栏 / 客户模块 / 上传识别 等） | 所有用户可见 | **th / en / zh / ja 4 语必须完整** |
> | 🔒 **对内功能**（`adm-*` 超管后台） | Zihao（中文）+ 泰国合作伙伴（泰语） | **zh + th 2 语即可 · 不需要 en / ja** |
>
> 新增 `adm-*` key 时只写 zh + th · 不许写 en / ja 浪费时间
> 节省约 274 个翻译工作量（137 key × 2 语）

### 实现方式（缺一不可）

每段文字必须做完两件事：

1. HTML 里用 `data-i18n` 绑定：
   ```html
   <button data-i18n="btn-save">保存</button>
   <input data-i18n-placeholder="ph-search" placeholder="搜索...">
   ```

2. home.js translations 对象里 4 语都补齐：
   ```js
   'btn-save': { zh: '保存', th: 'บันทึก', en: 'Save', ja: '保存' },
   ```

### subscribeI18n 注册（动态内容必须）

任何 JS 动态生成的内容（用 `t()` 函数取文字的）→ 必须注册：

```js
if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('module-name-唯一标识', _rerenderAll);
}
```

漏注册 = 切语言时该模块不刷新 = 半中半泰的尴尬画面

### 部署前自检（强制）

每次打包前自动跑：

```bash
python3 scripts/check_i18n.py static/home.js --strict
```

退出码 0 才能打包
非 0 → 必须先补齐缺失翻译再打包
不允许"先发版后面再补"

### 历史教训（绝不重犯）

之前换窗口经常出现：
- 新加功能只写了中文，泰英日漏了 → 用户切语言看到中文夹泰文
- 新加 modal 标题翻了，按钮没翻
- 新加 toast 提示只翻了一半
- 占位符 placeholder 全是中文
- 切语言时新模块文字不刷新（忘记 subscribeI18n）

新窗口接手时：
- 任何新加文字 → 第一反应是"4 语翻了吗"
- 改完任何 HTML / JS → 自检脚本必跑
- 报告给 Zihao 时主动说"已 4 语 + 已注册 subscribeI18n"

## 📱 手机网页端铁律(2026-05-13 拍板 · 最高级)

**Pearnly 没有 App · 只有手机网页端**:用户在手机浏览器访问 pearnly.com

**所有 UI 改动必须默认适配手机端**:
- 桌面优先布局 + `@media (max-width: 800px)` 降级
- 左右分栏 → 手机上下堆叠或横向滚动(参考现有 `.auto-layout` 移动端规则 home.css:2911)
- 表格 → 横向滚动或卡片化(不能让用户左右滑找列)
- 模态 → 全屏化 / 底部 sheet
- hover-only 操作必须有 click 备选(手机无 hover)
- 触控目标 ≥ 44×44 px
- 字号最小 12px · 主体内容 14-16px · 不能太小

**新模块 / 新页面 / 新组件验收前**:
- 必须在 chrome 开发者工具切到 iPhone 12 / Pixel 5 视口检查
- 没适配 → 不算完成

**报告改动时要说明**:每次部署 UI 改动 · 必测清单加 1 项"手机端打开 X 页看是否能正常用"

## 图标

- 只用 SVG line 风格（lucide / feather）
- **禁止 emoji 当图标**

## 色板（严格遵守）

| 用途 | 色值 |
|---|---|
| 主色 | `var(--brand)`（当前紫 #7C4DFF · 值以 home-01-base.css 为准）|
| 成功 | #16A34A（绿）|
| 警告 | #D97706（橙）|
| 危险 | #DC2626（红）|
| 文字主 | #111827 |
| 文字次 | #6B7280 |
| 背景 | #F9FAFB |
| 卡片 | #FFFFFF |
| 边框 | #E5E7EB |

## 参考产品对标

- 列表 / 批量操作 → Gmail 风格（hover 才显示⋮ · 勾选后就地切换工具栏）
- 金额列 → QuickBooks / Xero（右对齐 · tabular-nums）
- 设置弹窗 → DeepSeek / ChatGPT（modal · 左侧 tab · 右侧填满）
- 状态 chip → Notion / Linear（居中 · 颜色语义）

---

# 👥 终端用户视角（决策标尺）

**目标用户：** 泰国会计事务所 / 个体会计师 / SME 老板

**核心标准：** 每个新功能必须能帮会计师省 1 个手动步骤

**禁止开发没有明确省时价值的功能**

每次改动问自己：
1. 这个对会计师有用吗？
2. 用户用起来卡不卡？
3. 月底 800 张发票场景下顶得住吗？

---

# 💬 沟通规则总结

0. **【默认 Plan Mode】** 大任务先 plan · 用户确认再 execute · 改 1-2 行小 bug 可 shift+tab 切 auto
1. **回复用中文 · 大白话 · 简短直接**
2. **默认沉默** · 不主动喷专业知识
3. 命令 1-3 行 · SSH 不要 && 链接多条
4. 标 🌐（ssh 命令）/ 🖥（本地 PowerShell 命令）
5. 不等确认直接给方案（除非"需要先讨论"的情况）
6. 只有 Zihao 主动问"调研/对比/科普/教我/为什么"才详细展开
7. 截图存 yichang 文件夹 → Zihao 说"看截图"就读

---

# 📂 当前版本状态（2026-05-12 · 外部窗口核实重写）

**线上版本：** v118.32.4.9.5（已 ssh 核实 · /api/version 返回 11832495 · systemd active）
**当前主线：** P0-VAT 销项税对账模块（最高优先级 · Excel 公式对账内测中）
**cache bust：** home.js?v=11832495 · home.css?v=11832495

> 2026-05-13 本窗口连推 5 版：v4.8.1 入口整合 → v4.9 核对表重构 → v4.9.1 分组+原文件列表+进度条美化 → v4.9.2 左右分栏+手机端铁律 → v4.9.5 Excel 公式对账内测(skin306152 only)。下个 v4.9.6 = 5 bug + UI 美化 + 真实 PDF 504 fix。

## 已完成

- LINE 登录 ✅
- 用户/团队管理 ✅
- 异常栏（5类规则引擎）✅
- 识别中心（OCR 核心）✅
- ERP 适配器（Xero 全链路 ✅ · MR.ERP 搁置等 bridge API · 2026-05-14 全删）
- 自动化 6 通道 ✅
- P0-VAT 基础架构（A 阶段）✅
- P0-VAT B 速度优化：并行 10 路 ✅
- P0-VAT C 进度反馈业务化（v4.0-v4.7）✅
- P0-VAT F1 金额字段对齐 ✅
- P0-VAT F2 Excel 表头 4 语 ✅
- P0-VAT v4.8 OCR prompt 严格规则 + B 方案校对兜底 ✅
- **v4.8.1 销项税对账 + 批量识别入口整合**(2026-05-13)✅
- **v4.9 核对表重构**(逐字段对照·砍归一化判定·此次汇总区·第 3 动作"两边都对"·OCR 完整性)✅
- **v4.9.1 分组 bug 修复 + 原文件列表 + 进度条现代化**✅
- **v4.9.2 对账中心改左右分栏 + 文案通用 + 手机端铁律**✅
- **v4.9.5 Excel 公式对账内测**(skin306152 only · 完全独立模块 · 4-sheet 公式 Excel)✅

## 正在进行 / 待做（P0-VAT 剩余 · 2026-05-12 主线推翻）

🔥 **最高优先级 · 核对表重构 v4.9 / v4.10 / v4.11**（Zihao 拍板 · 推翻"匹配判定"模式）
  - 用户用 19 张 BAKELAB 发票实测 v4.8：1✓ 16⚠ 严重对不上 → 主线推翻
  - 新模式：Pearnly = **核对表生成器**（不是匹配判定器）→ 不替用户做决定
  - 详见 STATE_PEARNLY.md "v118.32.4.9 核对表重构"段

⏸️ 暂时延后（不影响准确率）：
- 🟡 6 张文件卡 10 分钟（速度问题 · 降级到 v118.32.5）
- D 后台异步 + LINE/邮件通知（v118.32.5）
- E OCR prompt 深化（v118.32.6）

## 暂停（等 P0-VAT 完成后接）

- 银行对账 v118.26.x ⏸️
- 用户管理深化 v118.29.x ⏸️
- 老板看板 v118.30.x ⏸️

---

# 🎯 下一个任务（明天接手就做）

**v118.32.4.9.6 Excel 公式对账 bug 修复 + UI 美化**（4.1 天 · 已评估完 · 等"开干"）

📋 详细工时拆解 + 影响文件 + 6 个 bug 描述见 STATE_PEARNLY.md "下个版本规划"段
🎨 UI 美化基准模板:`异常/vat_recon_BEAUTIFIED_demo.xlsx`
📦 v4.9 多场景测试数据:`异常/测试/v4_9_多场景/`(1 报告 + 12 发票)
📦 真实国税局测试 PDF:`异常/测试/รายงานภาษีขาย 03.69 - 001 033.pdf`(33 行 · 跑 v4.9.5 会 504 timeout)

---

# 📌 历史任务

~~v118.32.4.9 核对表重构~~（最高优先级 · 1.5 天 · Zihao 拍板推翻）

核心改动：**对账模式从"匹配判定"改成"逐字段对照 + 用户兜底"**
- 后端：reconciliation_matcher.py 改逐字段对照 · 不归一化 · 如实展示两边
- 前端：对账中心改对照表 UI（参考 `异常\ขั้นตอนการตรวจรายงานภาษีขาย.pdf` 底部表格）
- 7 个必识别字段（PDF 编号 3-9）：日期 / 发票号 / 客户名 / 买方税号 / 买方分公司 / 净额 / VAT
- 每行差异提供 3 动作："改报告" / "改发票" / "两边都对是同一笔"
- **UI 顶部加汇总区**：总行数 / 完全一致 / 数据差异（细分）/ 🔴 OCR 没识别完整 / 散客无发票
- 4 语 i18n × 全部新词条

接力：
- v118.32.4.10 7 项 OCR 准确率底线（1 天）
- v118.32.4.11 Excel 4 语对照表导出 + 列表时间戳（0.5 天）
- v118.32.5 D 后台异步 + 通知 + 6 张卡死根因
- v118.32.6 E OCR prompt 深化

详细拆解见 STATE_PEARNLY.md "v118.32.4.9 核对表重构"段

---

# 📌 模块优先级

| 优先级 | 模块 | 状态 |
|---|---|---|
| 🔥🔥 P0 | 销项税对账（P0-VAT）| 进行中 |
| 🔥 P0 | OCR 速度优化 | 进行中 |
| P1 | 仪表盘 | 待做 |
| P1 | 客户模块增强 | 待做 |
| P2 | 银行对账 | 暂停 |
| P2 | 凭证中心 | 待做 |
| P2 | 云盘同步 | 待做 |

---

# 📜 版本历史

- v118.20-21：异常栏完整上线
- v118.22-24：自动化 6 通道全通
- v118.27-28：MR.ERP 全链路 + 管理后台
- v118.32.0-2.5：P0-VAT 基础架构
- v118.32.3.0-3.9：P0-VAT BCDEF 优化
- v118.32.4.0-4.7：C 进度反馈业务化（5 阶段 + 失败明细 + 业务错误码 + 金额格式化 + 防覆盖）
- v118.32.4.8：B 方案校对兜底（accept-invoice / accept-report / 视觉等同 matched）+ Gemini prompt 严格规则升级

---

# 🚨 P0-VAT 产品哲学铁律（2026-05-12 Zihao 拍板 · 最高级）

**Pearnly = 核对表生成器 · 不是匹配判定器**

1. **OCR 准确率 = 第一底线**
   - 准确率 100% 的真实定义 = **OCR 抽出来的字段跟原文 100% 一致**（不是匹配率 100%）
   - 频繁识别不准 → 用户失去信任 → 会计师宁可自己眼睛核对 → 产品失败
   - 宁可慢一点，不能识别错；宁可标"识别不完整"让用户重传，不能瞎填一个错的塞进去

2. **我们只核实 · 不替用户做决定**
   - 不要"INV ↔ IV 自动归一化"——如实展示两边写的内容 + 标差异
   - 不要"客户名缺 ์ 符号自动算同一人"——同上
   - 不要"金额接近就认作匹配"——同上
   - 任何"模糊匹配"都是替用户做决定 · 违反这条铁律

3. **明显错系统主动标 · 用户兜底确认**
   - 系统能算出来的硬错（净额 + VAT ≠ 总额 / 税号不是 13 位 / VAT ≠ 7%）→ 主动 ⚠️ 标
   - 但只是"提醒"不是"判定" · 改不改用户说了算

4. **此次汇总区是必备**
   - UI 顶部 + Excel 顶部都要有"此次汇总"
   - 让用户一眼看出：完全一致 X 行 / 数据差异 Y 行 / 🔴 OCR 没识别完整 Z 行
   - 区分"业务差异"和"我们的 OCR 问题"很关键 · 后者是我们的责任

---

# ✅ 核心信条（记住这 5 条 = 不会出错）

1. **Zihao 是产品经理 · 不是工程师** → 说大白话
2. **默认沉默** → 除非影响产品/用户/未来，否则别主动喷
3. **部署完核心场景必测** → 项数不限 · 每项 ≤30 秒能验完 · 不要科普
4. **能自动跑的不要让 Zihao 手动** → scp/ssh/验证/清理全自己来
5. **关键词触发收尾** → 自动更新文档 → 报"可以关窗口了"

---

*本文件由 Claude（claude.ai）与 Zihao 共同维护 · 项目地址 https://pearnly.com*
*下次更新触发条件：新增铁律 · 架构决策 · 工作流变化*
