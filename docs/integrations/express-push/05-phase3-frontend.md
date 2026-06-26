# P3 施工单 · Express 接入前端(长进现有集成页 · 非另造模块)

> 先读 `00-master-plan.md`(真相/边界)+ `01-ui-design-brief.md` + `prototype.html`(**交互/流程蓝本**,不是配色蓝本)。P1 后端已上线(flag off)。
> 本棒目标:让用户能在 Pearnly 里**接通 Express、看到 Agent 在不在线、看到一张票将记成的分录** —— 全部用 Pearnly 现有设计系统,**完全不碰客户的 Express**。
> 先做 **P3a(接通向导 + Agent 状态卡)**,P3b(分录预览抽屉 + 设置)末尾列。

## 0. 最重要:复用现有集成页,别造平行模块
现有 `src/home/page-integrations.ts` 已有三 Tab(cards 卡片 / logs 推送日志 / push-exc 推送异常),`erp-integration.ts`(endpoint 管理)、`erp-exceptions.ts`(失败复核)。**Express 的推送日志/异常/统计会自动出现在这些里**(同走 `erp_push_logs`),**不要重做**。
- **Express 接通向导放新文件** `src/home/erp-express-connect.ts`(**照搬现有 `erp-mrerp-dms-connect.ts` 的隔离范式** —— 每个 ERP 的连接向导各自一个文件),`page-integrations.ts` 只加一个"连接 Express"入口卡,**最小改动**,避开与并发集成页窗口撞文件。
- prototype 的 4 Tab(连接/推送中心/异常/设置)→ 映射到现有:连接=cards、推送中心=logs、异常=push-exc、设置=现有 + 一个 Express 设置区。**不新增顶层 Tab**。

## 1. 边界 / 红线
- **设计令牌**:用 Pearnly 全站令牌(`.rcx`/TOKEN_CSS/home-NN.css 那套),暗夜走令牌不一处处改;**禁用 prototype 里硬编码的颜色**(`#1f6feb` 等)。prototype 只定"长什么交互/几态",不定配色。
- **不碰**:P1 后端、登录、计费、`home.js` 核心、客户 Express。后端契约已定(见 §3),前端只接不改。
- 改 `src/*.ts` 必 `npm run build` + 一起提交 `static/dist`;`home.html`/`home.css` 是 CRLF,禁 sed/prettier 盲写,bump `?v=` 用 Edit/字节替换(见 [[eol-crlf-trap-home-i18n]])。
- 单文件 <500、≥1 测试、去 AI 味、过 `lint-ui` 闸。
- **隔离 worktree** 施工(现有集成页窗口可能并发);rebase 最新 master;只碰自己文件,撞共享件停下报 PM。

## 2. P3a 要做的屏(照蓝本 · 现有令牌)
**A. 连接 Express 入口 + 连接卡**(在 cards Tab)
- 一张"Express"卡:状态徽章(🟢已连接 / 🟡Agent离线 / 🔴异常 / ⚪未完成)、账套名(DATAT)、迷你统计(今日已推/待推/失败,**取自按 status 派生的统计,排队中不算已推 · 状态诚实**)、Agent 在线靠 `config.agent_last_seen_at` 判(近 N 分钟有心跳=在线)。离线显黄条"N 单等待,Agent 上线自动补推"。

**B. 接通向导**(`erp-express-connect.ts` · 分步,照 01 brief Step 1–7)
1. 选 Express(其它 ERP 置灰"即将支持")。
2. **装 Agent**:下载按钮(占位即可,装包 P2 产出)+ **生成连接密钥**(调 `POST /api/erp/endpoints/{id}/agent-token` → 明文只显一次 + 复制)+ "等待检测到 Agent…"(轮询连接的 `agent_last_seen_at`,一旦近时有心跳→✅自动进下一步)。⚠️ 该 token 接口受后端开关保护,**开关 off 时返 404**:UI 要**优雅处理**(提示"推送功能未启用,请联系管理员开启"),别白屏。
3. **选账套**:列出 Express 账套,**本期锁定只能选 DATAT**(其它置灰 + 提示"真账套暂不开放");真账套选项显红字警示(照 brief)。
4. **录入方式**:RPA(推荐/默认)/ DBF(高级,选它弹**风险确认弹窗**,勾选才放行 · 照 brief P7)。
5. **字段映射**:默认"已自动匹配 ✅",高级可展开 —— **复用现有 mappings UI / `/api/erp/mappings/*`**,别重写。
6. **测试/完成**:测试连接清单(Agent 在线/账套可写/映射完整)→ 完成页 + **"开启自动推送"开关默认关**(状态诚实,让用户主动开)。

**C. 四态 + 暗夜 + 泰语**:每屏空/加载/错/有数据;暗夜与亮色等质量;文案泰语为主(中/英可切),走现有 i18n 系统不硬编码。

## 3. 后端契约(P1 已就绪 · 前端只调)
- 建/改 Express 连接:`POST/PATCH /api/erp/endpoints`(adapter=`express`,config:`account_set`/`method`/`threshold`/`fallback_acc`/...)。读连接(含 `agent_last_seen_at`):`GET /api/erp/endpoints`。
- 生成 Agent token:`POST /api/erp/endpoints/{id}/agent-token`(flag-gated → off 时 404)。
- 日志/异常/统计/重试:`GET /api/erp/logs`、`/api/erp/exceptions`、`/api/erp/stats/today`、retry —— **全复用**。
- 映射:`/api/erp/mappings/*` —— 复用。
- ⚠️ 线上 `ERP_PUSH_ENABLED` 当前 off → agent/token 接口 404;前端按"未启用"优雅降级即可,真联调待开关开(Owner 控)。

## 4. 验证(写清楚 · 施工窗口跑齐交 PM 判 · PM 不自己跑)
- **真浏览器验收**(你们标准:`isVisible`+`getComputedStyle`+截图,**grep 类名不算**):向导七步走通(token 步 404 时优雅提示)、连接卡四态、账套锁 DATAT、DBF 风险弹窗门槛、暗夜、泰语;手机视口。
- 截图存 `outputs/`;`npm run build` 后 view-source 只见 minified 外壳;`lint-ui` 绿。
- 汇报:截图 + 真浏览器断言结果 + 改动文件 + build/dist 提交确认。**不 push master**,PM 判。

## 5. P3b(后做)· 分录预览 + 设置
- **分录预览抽屉**(信任关键屏):点一张推送记录 → 抽屉显"将记入 Express 的分录"(Dr 采购/Dr 进项税 = Cr 应付 · 借贷平衡 · 照 brief P6),数据取 `erp_push_logs.request_body` 载荷;已推送显 Express 单号 + 状态时间线。
- **Express 设置区**:自动推送置信阈值滑杆 / 兜底科目 / 付款规则 / 通知。
- 单独续单,P3a 你验完再起。

## 6. 交付(P3a)
- 新 `src/home/erp-express-connect.ts`(<500)+ `page-integrations.ts` 最小接入 + 对应 home-NN.css(令牌)+ i18n 键 + build 后的 `static/dist` + 真浏览器截图。
- 不 push master;汇报含截图 + 断言 + 文件清单。
