# 交互性能诊断报告 · INTERACTION_AUDIT

> 2026-06-10 · 后端窗口 · 真测量数据(非估算除非标注)。下游执行:前端修复清单见 §6,交下个 src/home 窗口。

## 0. 一句话结论

**慢的根因不是某个端点的代码,而是两条系统性瓶颈叠加:① 应用服务器在日本、数据库在新加坡,每条 SQL 跨区往返 ~69ms;② 异步 handler 里直接做阻塞式 psycopg2 查询,2 个 worker 下首屏 22 个并发请求严重串行化。** 单个请求耗时 ≈ (该请求的 SQL 条数) × 69ms。**实测各 dashboard 端点仅 2–5 条 SQL、无 N+1(§3)→ 端点级没有可批量化的水分**;首屏 11.7s = 22 请求 × 跨区 RTT × 串行。最大杠杆:① **应用与 DB 同区**(顺带泰国用户更近);② **降首屏请求数**(去重 + 懒加载,前端);③ workers↑ / 鉴权-workspace 短 TTL 缓存(需签字)。

---

## 1. 测量环境(诚实标注)

| 层 | 方法 | 含什么 | 不含什么 |
|---|---|---|---|
| **服务端处理(干净)** | prod 本机对 `127.0.0.1:7860` 打端点 ×5 取中位(`scripts/_perf_probe.py`) | 纯服务端处理(含跨区 SQL 往返) | 机房↔用户网络 |
| **每端点 SQL 条数** | 计数游标 patch `get_cursor`/`get_cursor_rls`,直调 handler 数 `execute()`(`scripts/_perf_sqlcount.py`) | 真实跨区往返**条数**(区分 N+1 vs 慢单查) | — |
| **DB 往返** | prod 本机 `SELECT 1` ×10(psycopg2) | Japan↔Singapore 网络 RTT | — |
| **真浏览器端到端** | Playwright 注入 e2e_3 token 加载 prod `/home`(`scripts/_perf_browser.cjs` / `_perf_clicks.cjs`) | 网络 + 服务端 + 渲染 + worker 排队 | — |

⚠️ 真浏览器数字含**探针机位 → 日本机房**的网络往返(探针不在泰国),绝对值偏高;服务端处理的干净基线以"本机打 localhost"为准。渲染/有无 loading 反馈的观察与机位无关。

**基础设施实测**:
- 应用服务器:Vultr **日本(Tokyo/Saitama)**,2 核,负载 0.08,内存占用 191MB。
- 数据库:Supabase Postgres Pooler `aws-1-**ap-southeast-1**`(**AWS 新加坡**),事务级 pooler:6543。
- 连接池:`SimpleConnectionPool(minconn=2, maxconn=30)` per worker,**连接复用**(非每请求握手)。
- uvicorn:`--workers 2`,handler 多为 `async def`。

---

## 2. RTT 基线(决定要不要换区/上 CDN)

| 链路 | 实测/典型 | 说明 |
|---|---|---|
| 应用服务器 → DB(Japan→Singapore) | **69ms 中位 / 138ms p90**(`SELECT 1`),TCP connect 75ms | **每条 SQL 都付一次**。这是当前一切慢的乘数。 |
| 泰国用户 → 应用服务器(Bangkok→Tokyo) | 典型 ~70–95ms RTT | 每个 HTTP 请求付一次。 |
| 泰国用户 → 若服务器在新加坡(Bangkok→Singapore) | 典型 ~30–40ms RTT | **比东京更近**。 |

**结论**:把应用服务器迁到**新加坡(与 DB 同区)**是双赢——SQL 往返 69ms→~1ms(每请求省几百 ms),且泰国用户 RTT 也从 ~75ms 降到 ~35ms。优先级高于上 CDN(CDN 只解静态资源,解不了这里的动态 API 往返)。

---

## 3. 最慢交互 Top 10(用户视角)× 耗时分解 × 归因

服务端处理中位(本机打 localhost,干净):

服务端处理中位(本机打 localhost)+ **实测 SQL 往返条数**(计数游标 patch `get_cursor` 直调 handler·`scripts/_perf_sqlcount.py`·e2e_3):

| # | 用户交互 | 端点 | 服务端中位 | **实测 SQL 条数** | 归因 |
|---|---|---|---|---|---|
| 1 | 对账中心·VAT 导出列表 | `/api/vat_excel/tasks` | 1351ms | **5** | 请求级 RTT,非 N+1 |
| 2 | 知识库·文档库列表 | `/api/knowledge/bases` | 1155ms | **2** | 请求级 RTT |
| 3 | 首页·历史记录列表 | `/api/history` | 1140ms | **4** | 请求级 RTT |
| 4 | 对账中心·银行对账任务 | `/api/recon/bank-v2/tasks` | 1074ms | **4** | 请求级 RTT |
| 5 | 套餐/额度信息 | `/api/me/plan` | 789ms | **5** | 请求级 RTT |
| 6 | 账户余额/用量 | `/api/me/credits` | — | **5** | 请求级 RTT |
| 7 | 本月用量 | `/api/me/tenant-usage` | — | **4** | 请求级 RTT |
| 8 | 首页·异常数角标 | `/api/exceptions/stats` | 646ms | **3** | 请求级 RTT(且首屏被打 2 次) |
| 9 | 账套切换器加载 | `/api/workspace/clients` | 653ms | **2** | 请求级 RTT(enriched 仍单查·非 N+1) |
| 10 | 集成端点列表 | `/api/erp/endpoints` | 437ms | **2** | 请求级 RTT(且首屏被打 3 次) |

> 参照:`/api/me` **2 SQL** / `/api/clients` **2 SQL**;鉴权失败短路的 404/422 仅 **2–13ms**(不打 DB)。

**🔑 关键纠正(实测推翻早先估算)**:**dashboard 读路径没有 N+1**——每端点 2–5 条 SQL,且条数**与数据量无关**(无逐行循环查),代码也确认无循环内查询。早先"~17/~20 条"是「服务端中位 ÷ 69ms」的**错误估算**(把单查慢/序列化/连接获取也算成了往返数)。**已代码确认的固定开销**:每请求鉴权 `find_user_by_id` 1 条;workspace-aware 端点多 1 条 `default_workspace_id`。所以**端点级没有可"批量化"的 SQL**——首屏慢的真因在下面三条,不在单端点。

**首屏总 SQL ≈ Σ(各请求条数)≈ 22 请求 × 平均 ~3 = ~66 条往返**,跨区 69ms + 2-worker 事件循环串行(见 §4)→ 累积成 11.7s。**降首屏 SQL 的唯一杠杆是降「请求数」**(去重 + 懒加载),不是降单端点条数(已无水分)。

### 3-bis. 首屏冷启动(最痛点 · 真浏览器)

加载 `/home` 到 networkidle:**11.7 秒**,TTFB 3.2s。首屏一次性打 **22 个 `/api` 请求**。其中:
- **重复请求**:`/api/erp/endpoints` 被打 **3 次**、`/api/exceptions/stats` **2 次** —— 纯前端浪费。
- 22 个请求在 **2 个 worker** 上排队,且每个 async handler 做阻塞 SQL 时**冻结事件循环**(见 §4),并发度实际只有 ~2 → 串行累积成 11.7s。

### 3-ter. 温交互其实快(诚实)

登录后切换侧栏 tab:点击→首个 DOM 变化 **34–66ms**,网络静止 **64–152ms**——SPA 启动后缓存了数据,切视图给即时反馈。**用户痛点集中在 ①冷启动 ②触发新数据拉取的动作(翻页/筛选/打开单据/保存)**,不在 tab 切换本身。

---

## 4. 第二根因:async handler 里阻塞 DB(并发被锁死)

代码确认:`routes/me_routes.py`
```python
@router.get("/api/me")
async def get_me(request: Request):
    user = get_current_user_from_request(request)  # ← 同步阻塞 psycopg2,直接在 async 里调
    ...
```
`get_current_user_from_request` 是同步函数、内部 `find_user_by_id` 走阻塞 psycopg2。在 `async def` 里**直接调用**(非 `Depends` 不走 threadpool)→ 每条 SQL 的 69ms 都**阻塞事件循环**。`--workers 2` 时,全站真实并发 ≈ 2。首屏 22 请求只能两两挤过去 = 11.7s 的主因之一。

> 这是普遍模式(大量 `async def` handler + 直接调阻塞 DAL),非个例。

---

## 5. 后端修复建议(按杠杆排序 · 标注可否本窗口立即做)

| 优先 | 动作 | 杠杆 | 谁来做 |
|---|---|---|---|
| **P0** | **应用服务器迁新加坡(与 Supabase 同区)** | SQL 往返 69ms→~1ms,首屏与每个慢端点直接砍掉 90%+;泰国用户 RTT 也降 | ⚠️ 需 Zihao 拍板 + 运维迁移(换 Vultr 区/重部署)。**不在本窗口擅自动 prod 拓扑。** |
| **P0** | **前端首屏请求去重 + 懒加载**(降请求数=降总 SQL) | erp/endpoints ×3、exceptions/stats ×2 去重 + 非首屏端点推迟 → 22 请求可砍到 ~6 → 总 SQL 与串行同比下降 | **前端窗口**(本窗口禁碰 src/home)·见 §6 |
| P1 | uvicorn `--workers 2 → 4` | 缓解事件循环阻塞导致的串行(并发翻倍) | ⚠️ 改 prod systemd 单元,属运维决定 + 当前并行窗口活跃 → **建议 Zihao 确认后改**(内存够:4×~190MB)。 |
| P1（需签字） | 进程级**短 TTL 缓存** `find_user_by_id`(鉴权)+ `default_workspace_id` | 首屏 22 请求各 1 条 `find_user_by_id`(同一行)= ~22 条 → 缓存命中后 ~1 条;workspace 默认查同理。可砍首屏后端 SQL ~1/3 | ⚠️ `find_user_by_id` = **鉴权主路径**(铁律:改鉴权先报方案)·TTL 缓存会让改密/踢设备/权限变更有 N 秒延迟 → **必须 Zihao 拍板**才做 |
| P2 | 鉴权/DAL 改非阻塞(`run_in_threadpool` 或 asyncpg) | 根治事件循环阻塞 | 大重构,单列窗口 |

**❌ 没有 "Top N+1 端点批量化" 这一项**:实测(§3)各 dashboard 读路径仅 2–5 条 SQL、与数据量无关、无循环内查询 → **不存在可批量化的 N+1**。早先把它列为 P1 是基于错误估算,已纠正删除。**端点级 SQL 已无水分**——降首屏只能降请求数(前端 P0)或降单查往返成本(迁区 P0 / 缓存 P1)。

**本窗口未擅自施工**:P0 属拓扑/前端(非本窗口领地);P1 缓存触鉴权主路径需签字;无 N+1 可改。诚实结论 > 凑工作量。

---

## 6. 前端修复清单(交下个 src/home 窗口 · 本窗口不动 src/home)

1. **首屏请求瘦身(最高 ROI)**:
   - **去重**:`/api/erp/endpoints` 启动被打 3 次、`/api/exceptions/stats` 2 次 → 同一启动周期内做请求去重/共享 Promise。
   - **懒加载**:22 个启动请求里非首屏必需的(erp/xero status、settings/erp-push-mode、knowledge/bases、vat_excel/tasks、history 等)推迟到对应 tab 首次进入再拉,首屏只留 me / modules / 余额 / 异常角标。
2. **全局 `withLoading` 助手**:任何触发服务端往返的动作(保存/翻页/筛选/打开单据/切账套)统一包一层——按钮转圈 + 禁用 + 局部骨架,消除"点了没反应"的几百 ms 空窗(慢在网络不在前端,但**必须给反馈**)。
3. **乐观更新点位**:切账套、切 tab、标记已读/处理异常、勾选——本地先渲染,后台请求失败再回滚。tab 切换已是即时(34–66ms),保持;新增动作照此。
4. **innerHTML 局部化**:列表翻页/筛选只重渲染列表容器,不整段 `innerHTML` 重绘整屏(整段重绘会丢滚动位置 + 闪烁,放大慢感)。重点屏:进项单据列表、对账任务列表、历史记录。
5. **骨架占位**:冷启动与新数据拉取期间用 skeleton 顶住布局,别让内容区空白几秒。

---

## 7. 复现脚本

- `scripts/_perf_sqlcount.py` — **已入提交**·每端点真实 SQL 往返条数(计数游标 patch `get_cursor` 直调 handler)。**证伪 N+1 的关键件**,后续 perf 工作可复跑(prod 本机注入 `DATABASE_URL`/`JWT_SECRET`)。
- 一次性件(已删·方法见 §1):服务端 localhost 计时(`urllib` 打 `127.0.0.1:7860`)、真浏览器首屏 XHR 瀑布 + tab 点击时序(Playwright 注入 e2e_3 token 加载 prod `/home`)。
