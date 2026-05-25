# 📊 STATE · Pearnly 项目状态

> **最近更新**:2026-05-25(**第二十会话 · B1 续**)· **🟢 app.py 再拆 3 模块 · 4888→4459(-429)。pages_routes(静态页面+公开 meta 12 路由)/ me_routes(/api/me 家族 3 路由+UserInfo · 铁律 #15 敏感区 verbatim 搬+字段快照)/ line_binding_routes(LINE 绑定+偏好语言 4 路由)· unit 634 passed · ⚠️ 3 commit 全未 push(auto-mode 拦了 push to master · 需显式授权)。**
> ⚠️⚠️ **下个窗口:① 先 push 这 3 commit(`d73f21f`+2 · 需 Zihao 授权 · push 后验 /api/me、/api/line/binding、/(根)返 200/401 非 404 + CI 双 job 绿)· ② B1 易摘果实已【全部】摘完(pages/me/line_binding 是最后 3 块干净的)· 剩 22 个 @app 全是【安全敏感】(login/Google+LINE OAuth/email-code/line_complete_email 含 JWT 颁发+账号合并)或【勿碰】(OCR recognize 850 行/LINE webhook)或【故意留】(/api/version)。**app.py < 500 无法靠安全搬家达成** · 要继续压必须开 auth 专窗口(需 Zihao 在场 · 铁律 #16 登录关键路径)或转 C 前端拆 home.js(收益最大)。详见 `HANDOFF_REFACTOR_BC.md` §0/§5。开工 baseline:push 后 `origin/master...HEAD` = 0 0。**
>
> **(第十九会话)app.py 拆 6 模块 · 10075→4888**:categories/erp/admin_users 3 router(已 push)+ exception_checks+history 组(`b264790`/`c5af58e`/`1835bce` · 已于本会话前 push · origin 同步)。详见下方原记录。
>
> **(第十九会话后半)history 组拆分完成(两步法 · 纯后端搬家 · 0 业务逻辑改 · ⚠️ 3 commit 未 push)**:
> - **步骤 A · exception_checks.py**(`b264790`):OCR 异常检测(5 类规则)+ LINE 智能提醒整条链(378 行:EXC_RULE 常量 / `_parse_money` / `_is_valid_thai_tax_id` / `_async_run_exception_checks` / `_notify_exception_high` / `_notify_large_invoice` / `_format_thb` / `_user_lang_safe` / `_rule_belongs_to`)从 app.py 搬出。此前在 app.py · 被 OCR/LINE 上传路由 + history PUT 共用 · 不搬出直接拆 history 会循环 import。`line_client` 防御式 import(未部署降级 None)。
> - **步骤 B · history_routes.py**(`c5af58e` 10 路由 + `1835bce` assign_client 并入 = 11 路由):list/detail/update(编辑后重跑规则)/delete/pdf/batch-delete + 4 个 v1 别名 + assign_client · `_check_history_access` 随组走 · history PUT 从 exception_checks import `_async_run_exception_checks`/`_parse_money`(单一来源)。app.py 删 6 个随之 unused 的 import · 单一来源断言跟到新消费者(exception_checks/history_routes)· tenant contract 的 assign_client 断言语义更新。
> - **守门**:每 commit black/ruff(F)/imports/i18n(0/0)/unit 全绿 · unit 612→**622**。app.py 5530→**4888** · CRLF=0。
> - **停止原因**:history(文档标的"唯一剩的大组")已完成 · 剩余全核心耦合/安全敏感 · 上下文消耗可观 · 按「不在预算偏紧时硬开核心耦合区 · 不留半拆」收尾。
>
> ---
> **(第十九会话 · B1 续)app.py 拆 router 长跑(纯后端搬家 · 0 业务逻辑改 · ✅ 已 push + CI 全绿 + 生产验证)**:
> 模式 = 接力自主长跑「每完成一个安全 slice 本地 commit · 不 push · 只拆边界清晰组 · 纠缠太深跳过」。本会话从 app.py 抽出 3 个 router:
> - **categories_routes.py**(`af9a2f4`)· 1 路由 `/api/categories`(供应商分类自动补全)· 用 `_tid`(route_helpers)· 完全自包含。
> - **erp_routes.py**(`c81f609`)· 15 路由 `/api/erp/{endpoints,test-connection,customers,products,push,logs,stats,retry,batch}` + `_check_push_access`(独占)+ 6 model + `_strip_endpoint_for_response`/`_fetch_listing_with_retry` + 3 个 TTL 缓存。**铁律 #10 async tripwire**(test-connection/customers/products/push 调 sync Playwright 的 `asyncio.to_thread` offload)随路由体完整搬走 · offload 测试 33 passed。**自动推送后台 cluster**(`_auto_push_*` · OCR hook 触发 · 非路由)留 app.py · 两段 splice 绕开。**`_record_500`/`_read_last_500`/`_last_500_event`** 三件套(app 异常处理器 + erp + admin_diagnostics 三方共享 mutable 状态)搬到 route_helpers 做单一来源。启动缓存 flush 加 `flush_test_connection_caches()` 封装。
> - **admin_users_routes.py**(`eadc121`)· 15 路由 admin users/employees(列/建/详情/删/改密/日志/quota/status/csv/cascade + 员工启停/改密/删)+ 4 自有 model + CascadeDeleteRequest · 复用 `_require_super_admin`/`_log_op`(route_helpers)+ `AdminUpdateTenant*`(tenant_routes)+ `EmployeeToggleRequest`(team_routes)· app.py 去掉随之 unused 的 5 个 import · 单一来源断言跟到新消费者(改 route_helpers/team/tenant/admin_logs 4 个 contract test)。
> - **范式**:字节级 splice(ReadAllLines + 边界 assert + `@app.`→`@router.` + UTF8-no-BOM)· 每组带 contract test · app.py LF 全程干净(CRLF=0)。
> - **守门**:每组 imports / i18n(0/0)/ unit / black / ruff(F)全绿 · unit 597→**612**(+2 新 contract · 改 4 既有)。
> - **当前行数**:app.py **5530**(-1745)· db.py 10661 · 已有 **24** 个 `*_routes.py`(home.js/css/html 本会话未动)。
> - **push + 验证**:Zihao 授权后 push(`e3a42bc..8ef6779` 3 router+docs)· 生产 webhook 部署 · `/api/version` 200 · 抽查 `/api/categories`、`/api/erp/{endpoints,logs}`、`/api/admin/{users,employees,users.csv}` 全返 401(非 404/500)= 零丢路由。
> - **顺手修 CI lint 红(`9ee3a6d`)**:验证时发现 CI lint job 自第十八会话起一直红 · 根因 = recon/salesvat 修复(`575767f`/`eb87429`)提交时漏跑 black(7 文件 py311-black 脏)+ 2 个未用 import(black 先挂 ruff 没跑到)。本窗口 black 格式化 7 文件 + ruff --fix 清 2 个 F401 · 纯格式化 0 逻辑改 · 推后 **CI 双 job 全绿**(lint 58s + test 2m49s)。
> - **停止原因**:3 个干净 slice 后 · 唯一剩的大组 history 纠缠最深(需先做 `_async_run_exception_checks` 整条链迁移子工程)· 本窗口已大量分析 + 3 次提取(含 erp 共享状态迁移)· 按「上下文不足不硬开下一大组 · 不留半拆 app.py」收尾 · 非测试失败非阻碍。**详见 `CLAUDE.md/HANDOFF_REFACTOR_BC.md`**。
>
> ---
> **(第十八会话 · 修复插曲)codex 测试报告驱动的 3 批回归修复(打断 B1 冻结期 · 已全部上线 + 部署)**:
> 来源 = Zihao 转的 codex 实测报告。整顿期原则上 0 新功能,但生产回归 bug 优先于重构。本批修复均"修一类不修一处 + 守门全绿 + 4 语 release_notes + 部署后留 codex 生产复测"。
> - **GL CSV 整侧失败不再静默完成(`672f748` + 前端 `0daebf6`)**:GL/VAT 任一侧 0 收入行原被吞成"完成" → 改 needs_mapping / failed 失败分流 · cache_bust 11835074→11835075。
> - **销项税对账 6 项回归修复 + 旧流程清理(`eb87429` + `15241bd`)**:正常匹配发票不再误判差异 · 支持 Excel/CSV/Word 发票与报告 · 跨月报告提示不静默合并 · 图片识别加超时保护 · 删旧客户期间流程 + 批量分类残留(P2)。
> - **收入对账 M3 + ERP 推送 6 项(`575767f` · 本会话)**:① M3-1 成功后历史列表立即刷新(`_loadHistory`)· ② M3-2 失败改 `__failed__` sentinel 带 error_code → worker 透传 → 前端 4 语可读文案(复用 bank 基础设施)· ③ M3-3 计费漏洞修复(gl_vat 按量扣费 · 图片/PDF 按 OCR 页 · Excel 按字符 · 闭掉免费入口)· ④ ERP-1 list/get endpoint SELECT 补 user_id(不再误报 `ERR_NO_CUSTOMER_MAPPING`)· ⑤ ERP-2 `ensure_erp_push_logs_status_constraint` 放开 status CHECK 接受 `skipped_dup` + insert 失败显性 `log_write_failed`(防重日志落库)· ⑥ ERP-3 核实 reset-password 故意 410 · 前端无按钮调用 · intended 无需改。
> - **守门 + 部署**:全量单测 596 passed · py 语法/导入全绿 · 浏览器冒烟(GlVatRecon 模块/三 tab/设置弹窗 零页面报错)· cache_bust→11835078 · `/api/version` 4 语 release_notes 已覆盖式更新(只留本次:收入对账历史即时刷新 + 失败具体原因)· 生产已落地 11835078。
> - **待 codex 生产复测**:① 收入对账成功后历史即现/前缀错显原因/GL Excel+VAT PNG 扣费链 · ② ERP 自动推送 success(不再 mapping 误报)+ 重复推送 skipped_dup 落 /api/erp/logs。
>
> ---
> **(第十七会话)整顿 B1 · app.py 拆 router 长跑续(纯后端搬家 · 0 业务逻辑改 · 7 commit · ✅ 已随后续部署 push · origin 同步)**:
> 模式 = 接力自主长跑「每完成一个安全 slice 本地 commit · 不 push · 只拆边界清晰组 · 纠缠太深跳过」。本会话从 app.py 抽出 6 个 router + 搬 1 个 helper:
> - **bank_recon_routes.py**(`faaa536`)· 11 路由 `/api/bank-recon/*`(上传/会话/匹配/候选/客户绑定/dev seed)· _TEST_USER_IDS 随组搬 · 自包含(仅 db + auth)。
> - **admin_migration_routes.py**(`b33dd58`)· 7 路由 `/api/admin/{migration,rls}/*`(超管多租户迁移/RLS)· 仅 _require_super_admin + db。
> - **admin_cost_routes.py**(`13eded7`)· 10 路由 `/api/admin/{cost,credits,monitoring}/*`(成本/收入/监控面板 · 只读聚合 + CSV)· 仅 _require_super_admin + db。
> - **tenant_routes.py**(`fac5f62`)· 6 路由 `/api/admin/tenants/*` + `/api/me/tenant-usage` + 3 model · 被 history 组 assign_client 夹断 · 两段 splice · AdminUpdateTenantQuota/Status model 被 app.py admin user 路由复用 · import 回去(单一来源)。
> - **admin_logs_routes.py**(`574c92d`)· 4 路由 `/api/admin/logs(.csv)` + `/api/me/access_log(.csv)`(操作/审计日志)· users.csv 留 app.py。
> - **`_tid`→route_helpers.py**(`4755af7`)· 取 user tenant_id 的纯函数 · 37 调用点不变 · 解锁 categories/connectors/xero。
> - **erp_xero_routes.py**(`569b534`)· 8 路由 `/api/erp/connectors/status` + `/api/erp/xero/*`(OAuth 连接器聚合 + 推送)· _ensure_fresh_xero_token 随组搬(app.py 自动推送复用 · import 回去)· _require_owner_or_super 最后消费者搬走 · app.py 去掉该 import(更新 route_helpers contract 单一来源断言)。铁律 #10 核对:Xero 走 requests 非 Playwright · 无 async tripwire 适用。
> - **范式**:字节级 splice(ReadAllLines + join`n` + UTF8-no-BOM · 边界 assert)· `@app.`→`@router.` · 每组带 contract test · app.py LF 全程干净。
> - **守门**:每组 imports / i18n(0/0)/ unit / black / ruff(F)全绿 · unit 552→**580**。
> - **当前行数**:app.py **7263**(-1326)· db.py 10620 · home.js 33867 · home.css 16131 · home.html 6726(db/前端本会话未动)。
> - **停止原因**:剩余组(history/erp-endpoints-push/admin-users)都纠缠较深(各需先搬 `_async_run_exception_checks`/`_check_push_access`/多 helper)· 按「安全第一 · 纠缠太深跳过 · 上下文不足不硬开下一组」收尾 · 非测试失败非阻碍。**详见 `CLAUDE.md/HANDOFF_REFACTOR_BC.md`**。
>
> **(第十六会话)整顿 B1 · app.py 拆 router 长跑(纯后端搬家 · 0 业务逻辑改 · 6 commit 全留本地 · ⚠️ 未 push)**:
> 模式 = Zihao 指示「每完成一个安全 slice 就本地 commit · 不 push · 不因 push 权限拦截停下」。本会话从 app.py 抽出 5 个 router + 1 个 helper 搬家:
> - **team_routes.py**(`b95372d`)· 7 路由 `/api/team/employees*`(列/分配/加/改密/删/启停)· EmployeeToggleRequest 被 admin 410 stub 复用 · app.py import 回去(单一来源)。
> - **erp_mappings_routes.py**(`0e17fa4`)· 12 路由 `/api/erp/mappings/{clients,accounts,taxes,products}` CRUD · ErpProductMappingReq + _tid 本地副本。
> - **email_ingest_routes.py**(`8358b72`)· 6 路由 `/api/email-ingest/*`(IMAP 邮箱抓取)· 2 model + _email_presets · email_ingest 懒 import。
> - **`_plan_permissions`→route_helpers.py**(`870290c`)· 已是扁平化纯静态函数(忽略 plan 入参返全开权限)· 搬到 route_helpers · 13 处调用点不变 · **解锁 rd/archive/history**(它们 _check_*_access gate 在 _plan_permissions · 之前绑死 app.py 会循环 import)。
> - **rd_routes.py**(`8fa55f7`)· 4 路由 `/api/(v1/)rd/{verify,lookup}`(泰国 RD 税务)· RdQueryRequest + _check_rd_access。
> - **settings_routes.py**(`7686259`)· 5 路由 `/api/archive/{settings,rename-preview}` + `/api/settings/dup-check`(智能归档+查重设置)· 3 model + 2 archive helper · gemini-key 墓碑注释留 app.py。
> - **范式**:每组 APIRouter() + 从 auth 拿 current_user + 从 route_helpers 拿公共 helper · `@router` 注册 · app.include_router · app.py 留 marker 注释指向新文件。原 URL/权限/返回格式/业务逻辑 100% 不动。
> - **每组带 contract test**(路由 path+method 契约 + include_router 挂载 + 单一来源/字段契约)· unit 530→**552**。
> - **守门**:每组 imports / i18n(0/0)/ unit / black / ruff(F)全绿 · **app.py 全程 LF 干净**(每次 splice 后校验 CRLF=0 · 不重蹈 clients 那次 CRLF→LF 全文件 diff)· 改 app.py 用 ReadAllLines+join`n`+UTF8-no-BOM 字节级 splice · 不用 Edit 大块匹配。
> - **✅ 已 push master**(会话末 Zihao 授权)· `ad00b3c..fb68a6b`(7 commit:6 code + 1 docs)· webhook 自动部署 · ~5s 内 `/api/version` 恢复 200(版本 11835074 不变 · 无 UI 改)· **5 个搬出的 GET 路由全返 401(路由在 · 非 404)· `/api/rd/verify` 返 422** = 搬家零丢路由 · 生产验证通过。CI run 26370466959(commit fb68a6b)✅ completed success。
> - **当前行数**:app.py **8589** · db.py 10620(未动)· home.js 33867 · home.css 16131 · home.html 6726(前端本会话未动)。
> - **下一组候选**(B1 续):history(7 路由 · `_plan_permissions` 已解一半 entangle · 评估 `_async_run_exception_checks`/`_check_history_access` 是否也要搬 route_helpers)· `/api/bank-recon/*` · `/api/erp/*`(endpoints/test-connection/push/logs · 注意铁律 #10 async tripwire)· `/api/admin/*` 大组(cost/credits/monitoring/tenants/users)。**详见 `CLAUDE.md/HANDOFF_REFACTOR_BC.md`**。
>
> ---
> **(第十五会话)**· **🟢 ① 对账UI 5盲区修4个 ② Earn后台诊断报告整改 ③ 成本页UI重做+监控独立模块+列表分页搜索 · 全上线 · CI 全绿。**
> ⚠️⚠️ **下个窗口:回归工程整顿 `CLAUDE.md/REFACTOR_MASTER_PLAN.md`(从当前阶段续 · 见该文件进度看板)。BUG/整改主线本会话告一段落。**
> ⚠️ **唯一未验(跨整个第十五会话)**:Earn admin UI 浏览器实际渲染观感(成本页引擎卡/趋势图/抽屉/充值排版/监控独立页/分页)——前端均过语法/lint/逻辑+路由全通+后端活数据真验,但**没在浏览器点一遍**,需 Zihao 以 Earn 超管登录 `pearnly.com/admin` 扫一遍,或给超管 token 我来 Playwright 验。
>
> **(第十五会话·尾)成本追踪页UI重做 + 系统监控独立 + 列表分页搜索(commit `7dd4a82`+`9889cbd` · 已上线 · admin cache_bust 11841102 · admin-only · 仅UI/前端聚合 · 不改扣费)**:
> - **引擎计费入口卡片化**:两入口改与花费统计卡同款(白底/边/圆角/hover阴影/左图标+标题说明CTA+右箭头)· "以官方为准"移卡片下方小提示。
> - **30天趋势重做**:黑粗柱→SVG 堆叠柱(按引擎归一)+总花费折线+Y轴฿刻度+X轴每5天+hover tooltip+彩色图例(可点切)+segmented(花费/调用/页)+空状态卡+异常峰值红点(>日均2x)。后端 `db.get_cost_daily_by_engine` 只读聚合 · 端点加 `by_engine`。
> - **成本构成排行**:文字堆→排行列表(引擎名|金额|调用|彩色占比条)。
> - **系统监控独立模块**:从成本页搬出→`page-admin-monitor`+sidebar导航+`/admin/monitor`路由(catch-all+resolveRoute/switchView/renderMonitorPage 全通·已验 /admin/monitor 返SPA 200)。
> - **风控可疑活动并入监控**:从用户页搬进监控模块。
> - **列表分页+同款搜索**:统一组件(_pgSlice/_pgBar/_listFilter·每页20·客户端)。用户管理(+分页)、公司余额清单(+搜索+分页)、按用户分组(+搜索+分页)。
> - 守门:全量529 passed · black/ruff/eslint(0err)/prettier 全绿 · 上批CI success。
>
> **(第十五会话·下半)Earn 后台诊断报告整改(commit `de048d3` · 已上线 · CI 全绿 · admin-only zh+th · 不碰客户端)**:
> 来源 `Earn后台诊断报告_20260524`(Codex)。逐条核实后整改 5 块(单一权威源见该报告 + 本段):
> - **A 删 Google "实际余额" 卡整套前后端**:手动录入值会被误认成自动余额。删 `/api/admin/billing/balance` GET/POST + `/history` + `BalanceUpdateRequest` + `db.get_balance_summary/add_balance_log`。换成两个引擎计费**直达入口**(查清 pipeline_v1 = Google Cloud Vision(OCR文字层·Cloud计费) + Gemini Flash(AI Studio计费) 两套面;对账 gemini-vex 走 AI Studio)。表 `billing_balance_log` + `get_latest_balance` 保留(vat_excel 用 calibration 兜底)。生产 `billing/balance` 已返 404。
> - **B 用户详情抽屉重设计(前后端)**:修一堆**前后端字段名错位**(前端读 `ocr_used_month/ocr_total/signup_fingerprint`,后端返 `used_this_month/cumulative_ocr/device_fingerprint` → 累计OCR/设备指纹/本月用量恒0恒空)。新增「余额与计费」段(余额+本月扣费+本月页数+累计充值,来自 `db.get_tenant_credit_summary` 新函数,**生产真验返活数据**)。删 credits 模式无意义的「本月用量0/无限」配额 + 死字段 `signup_source`。空字段/空段隐藏(不做空壳)。加员工段。后端 `/api/admin/users/{uid}` 补 `credit`。
> - **C 趋势图+金额**:趋势恒"暂无数据"(后端返 `{days:[]}` 前端只读 `points/data`)→ 读 `d.days` + tooltip 字段 `p.day`;金额 `฿10.6,067`(`_fmt` toFixed 后正则给整串加千分位连小数也加逗号)→ 改 `Intl.NumberFormat`。
> - **D 充值审核**:右侧(金额/日期/状态/截图/操作/审批备注)重排成对齐竖列 + 备注独占一行(class 化);加"隐藏测试数据"开关(默认开 · 名称模式过滤 QA/Codex/test/ui_recon · 不动 schema)。
> - **E**:用户列表本月用量改真实 `used_this_month`(旧恒0)+列名"本月识别";"引擎占比/主备引擎"→"内部识别成本构成·非用户可选引擎";监控"今日识别总数"→"本进程识别数"(内存统计·重启清零)。
> - 守门:全量 **529 passed** · black(py311)/ruff/eslint(0err)/prettier 全绿 · CI 双 job 绿 · admin cache_bust 11841099→11841100。
> - **⚠️ 唯一未验**:admin UI 浏览器实际渲染(抽屉/卡片/充值排版)需 Zihao 以 Earn 登录看,或给超管 token;前端代码已过语法/lint/逻辑 + 后端活数据真验。
>
> **(第十五会话·上半)对账UI 5盲区**:见下方原记录(②③④①⑤ · commit `661c82a`/`9b48c83`/`a3aee96` · CI 测试 job 绿;后顺带清 CI lint 积压债 black/bandit/prettier · CI 现完全绿)。
>
> **本会话(第十五)成果(已上线 · 后端纯逻辑修 · 本地实跑+CI测试 job 双绿 · commit `661c82a`+`9b48c83`)**:
> 触发 = Zihao 给的 `对账UI全量测试报告_20260524`(Codex 跑 23 个触发条件素材)。生产 JSON + 本地实跑双核实根因,修 4 个(⑤为验证项非bug)。单一权威源 [`docs/refactor/adr-006-universal-importer.md`](../docs/refactor/adr-006-universal-importer.md) §10.1。
> 1. **②③ GL 认不出列不再静默"完成"**:无日期列 GL(A/B/C/D)原返 `gl_headers_not_found` → 对账当"0行GL"显示"完成"(XLSX);CSV 还降级 Gemini 把无表头硬读成 `gl_date=null` 行参与匹配(凭空造 matched=1)。修:`parse_gl_excel` 文件可读但认不出列且仍是张表 → 返 `needs_mapping`(原始表头+预览)· submit 预检弹"确认列"· CSV 不再降级 Gemini。
> 2. **④ PDF 页脚合计写错触发 S8**:`_audit_completeness._sum_reliable` 用 0.1% 宽容差把"合计≈期初/期末"当误填余额跳过 · 测试件 Total Deposit=9999 恰落期初 10000 的 ±10 内被静默放过。修:误填判定改 0.5 元近精确容差 → 9999 正常触发 `credit_sum_mismatch`→S8 · BAY『两合计相同』主防护不动。
> 3. **① 怪表头+余额链正确自动识别**:小文件存/取列各只2值被 `_fill_by_shape`『≥3行有钱』阈值漏掉 → 方向列没识别 → 余额链没跑 → 弹映射。修:`infer_stmt_col_map` 加方向列救援搜索(仅余额链验证不过时,枚举单列净额/存取两序 · 验证选最优 · 安全闸 · 零回归)。连带 S7 stmt AI fixture 调整。
> 4. **⑤ 2行PDF走Gemini**:非bug · 本地证免费路径0行→生产必走Gemini · 日志已有 · 生产SSH确认待授权。
> 5. **附带清 CI lint 债**:`9b48c83` black 格式化第十四会话遗留的 6 个文件(CI Python3.11 black 一直红的根因)· 纯格式化。
>
> **守门**:新增 5 个守门测试 · 全量单元 **529 passed**(+1 skipped)· black(py311)/ruff(F)/i18n(0/0)/app import 全绿 · CI 测试 job 绿。纯后端 · 不动前端(不bump cache_bust/release_notes · 版本横幅不重弹)。
> **遗留(诚实)**:① 生产真站点 UI 复测需 token(本次靠本地对精确素材实跑验证后端逻辑 · 强于UI)· ② 生产 journalctl 确认 ⑤ 需授权 SSH。
>
> ---
> **(第十四会话)** · **🟢 大量计费/导入器整改完成并上线验证。**
> ⚠️⚠️ **下个窗口:别急着回整顿期(REFACTOR_MASTER_PLAN)· Zihao 还有整改要做 · 继续 BUG/整改 > 整顿。**
>
> **本会话(第十四)成果(全部已上线 + 生产真验)**:
> 1. **充值真因修复**:`/api/me/credits` 用 `row[0]` 取 RealDictCursor → KeyError 被吞 → **所有老板余额恒显 0**(钱在/能用/就是看不到)· 改 `row["balance_thb"]` · AK UI 实测显示正常。
> 2. **充值审核模块重建**:Earn 后台 `/admin/topup`(CLEANUP 误删前端 · 重建接 billing_routes credits/topup/*)· tab 样式按设计语言重做。
> 3. **ADR-006 S7 上线**:AI 低信心列映射建议 · 真 Gemini 实证(线上 GL medium→AI 补 doc_no→形状校验 1.0→存 source=ai)。
> 4. **ADR-006 S8 上线**:PDF/扫描件「逐行核对纠错」· 真扫描件 BBL2697 端到端通(needs_review→confirm-rows→重对账)。
> 5. **OCR 改纯 credits 按量扣费**(Zihao 拍板:全平台只此一个套餐·0起步)· 删旧 plan/quota/key/trial 双闸 · 准入只看余额 · 新账号默认 plan='credits' · 图片按页扣 · 扣费传 history_id(usage-history 显示文件名)· 非发票不扣费 · 5 个 QA 验收问题全修+真账号验。
> 6. **根因/数据修**:PyMuPDF 1.20.2→1.24.10(根治部署 pip 中断→python-docx 装不上→DOCX 500)· ocr_history.tenant_id 补存 · ensure_credits_tables 加 advisory lock 防 deadlock · make_searchable_pdf 守门降噪 · 异步对账进度副文案语言修(泰语界面显示中文)。
> 7. **新铁律 #25**:Claude 自己跑测试-日志-修复-复测全闭环(不再把命令丢用户)· 详见 ADR-006 §9。
> 8. 加了 `Bash(git push:*)` 权限(免每次「授权 push」)。
>
> **遗留(未做·诚实记录)**:① 200页后 ฿0.75/页 仅本地函数验证·未烧真实 OCR ② ocr_history 旧记录 tenant_id 仍 NULL(不回填·新记录已修)③ 整改审计 Phase1 剩余/Phase2-3 = Zihao 早前拍板暂缓/不做。
>
> ---
> **(第十三会话)** · **🟢 通用模板学习层 ADR-006 S1–S6 全部完成并上线(v118.35.0.71 · recon-mapping.js?v=11835072)· 账单/总账 · Excel/CSV 新格式不再"解析失败" → 确认列一次 → 记住 → 下次自动 · 真站点 UI + 12 个大文件压测全过(抓修 5 个真 bug)· KTB/小现金零回归。**
>
> **⚠️ 下窗口接 S7/S8:单一权威源 = [`docs/refactor/adr-006-universal-importer.md`](../docs/refactor/adr-006-universal-importer.md)**(§6 进度+代码地图 · §7 S7 AI 建议接手指南 · §8 S8 PDF/图片接手指南 · §9 Zihao 测试方法论必照做 · §10 已修 bug 编年)。**S7=AI 低信心自动建议一次(hook 已留 `suggest_mapping_with_ai`)· S8=PDF/图片扫描件确认/纠错(机制不同 · 先摸现有 PDF 路径)。**
>
> **(早些)🟢 ADR-006 S1–S5(v118.35.0.70 · home.js?v=11835070)· 新格式 Excel 银行账单不再"解析失败" → 弹"确认列对应"面板确认一次 → 保存 → 自动重跑出结果 → 下次同格式自动 · 真站点端到端 UI 验证通过(面板正确识别表头+预选列+保存重跑出结果)· KTB 1332行零回归 · 全程不烧 Gemini。剩 S6(CSV账单+GL总账)→ S7(AI低信心建议)→ S8(PDF/图片扫描件)。单一权威源 docs/refactor/adr-006-universal-importer.md**
>
> **(同会话早些)🟢 对账异步大改 #14+#15+#16 全部完成并上线(v118.35.0.69 · home.js?v=11835069)· 银行对账已真站点端到端 UI 验证通过(submit→轮询→渲染 + 进度文案 + 解析诊断表全 OK)· 收入/销项税共用同一机制(后端已 E2E 证 · 前端同款代码 · 待真文件 UI 复测)· #17 剩灰度收尾**
>
> **真因排查战果(第十三会话)**:#15 enqueue INSERT 漏传 progress 值(8 占位符 7 值)→ "tuple index out of range" → submit 全失败 · 真站点 E2E 抓出(mock 证明不了真执行)· 已修 + 加占位符数==参数数守门。
>
> **(第十二会话)**· **🔴 紧急:mrerp 银行对账 500 真因=服务器磁盘满(已修复+上线)· 🟡 异步大改地基已打好(待续做完)**
>
> **🚨 整顿/异步全部让位** · 当前最高优先级 = 把对账异步大改做完(下窗口接力 · 见下方"第十二会话"段)
>
> **整顿期(REFACTOR_MASTER_PLAN.md)**:暂停(BUG>整顿)· A 阶段 **8/10** · B 阶段 ~1/10(notification+clients+exceptions+route_helpers)· C 前端未动
>
> **整改单一权威源**:[`docs/audits/2026-05-22-ocr-recon-audit.md`](../docs/audits/2026-05-22-ocr-recon-audit.md)

---

## 🆕 2026-05-24 第十二会话 · mrerp 对账 500 彻查(磁盘满)+ 对账异步大改地基 · ⚠️⚠️ 下窗口必读必接

### A. 核心 BUG 已彻底解决并上线 ✅(付费用户 mrerp 银行对账报 `Unexpected token '<', "<html>..." is not valid JSON`)

**真因(一路排错 · 全靠数据非猜测)= 服务器 52G 硬盘 100% 满**:
- 现象链:磁盘满 → Nginx 写不下上传文件请求体(`/var/lib/nginx/body/` `pwrite() failed (28: No space left on device)`)→ Nginx 返回 HTML 500 → 前端 `res.json()` 解析 HTML 抛 `Unexpected token '<'`。
- **排错走过的弯路(教训记牢)**:先猜超时(❌ 是 500 不是 504)→ 猜大文件(❌ 文件才 226KB 文字版 · 本地全链路 2.25s 跑通)→ 猜内存 OOM(❌ 服务才占 190M/峰值 397M · dmesg 无 OOM)→ 本地 TestClient 跑完整路由 200(❌ 代码无 bug)→ 查 nginx 日志(默认 access/error.log 半夜轮转后 0 字节 · logrotate 没 reopen)→ **`error.log.1` 里抓到 `[crit] pwrite ... No space left on device`** = 铁证。
- 罪魁:`/tmp` 堆 28G `pip-unpack-*`/`pip-install-*`(每次部署 pip 解压 torch ~2.7G 不清理 · 9 次累积撑爆)。
- **已修复**:① 清 /tmp pip 残渣 100%→44%(对账当场复活 · Zihao 确认)② **铁律 #24** 入档 ③ git-deploy.sh 生成器(app.py L728)加部署后 `rm -rf /tmp/pip-*` + 磁盘体检(已上线 · 部署日志见 `disk usage after cleanup: 44%`)④ `nginx -s reopen` 恢复日志 ⑤ 每日 cron `/etc/cron.d/clean-tmp` 兜底 ⑥ `/root/.cache`(pip 缓存 5.4G)已清。**当前磁盘 40% · 30G 可用 · 健康**(从 100% 满恢复)。
- **前端兜底已上线 v118.35.0.68**(`a4f10de`):`runRecon` 的 `res.json()` 加 try/catch · 非 JSON 响应显示友好 4 语 `brv2-err-server`(服务器繁忙/请稍后重试或分批上传)· 不再弹乱码。
- **遗留小债**:每次部署 `pip install -r requirements.txt` 重编 **PyMuPDF** wheel 失败(非致命 · 不挡部署 · 但白跑+丢报错)· 回头钉版本/已装跳过。

### B. 对账异步大改(ADR-005)· 地基已打好 · 剩余待做完 ⏳

**为什么做**:三个对账(银行 bank-v2/run · 收入 gl-vat/run · 销项税 vat_excel/build)全是同步阻塞干等 · 慢任务占连接 · 多用户同时跑会拖垮。Zihao 拍板"做到端到端 100% · 不留半成品"。**(注:本次 500 真因是磁盘 · 不是同步阻塞 · 但异步对扛规模+体验仍值得做 · Zihao 要求做完。)**

**已完成并入库(休眠安全 · 不影响线上)**:
- `docs/refactor/adr-005-recon-async-jobs.md` —— 完整设计(单一权威源 · 下窗口先读)
- Alembic `003_recon_jobs.py` —— `recon_jobs` 队列表(状态/进度/订单号 · 结果仍写老表)· **⚠️ 生产未建表**(git-deploy 不跑 alembic · 下窗口要手动 `alembic upgrade head` 或在 worker 启动时建)
- `services/recon_jobs/store.py` —— 队列 CRUD(enqueue/claim_next SKIP LOCKED/update_progress/finish/fail/reclaim_stale/get/gc_old)
- `services/recon_jobs/worker.py` —— 双模工人(embedded web内 + standalone)· 并发闸门 · 租约续期 · 暂存 GC · handler 注册表

**剩余步骤(下窗口做完)**:
1. **#14 抽 run_*** ✅ **完成(2026-05-24 第十三会话)**:`services/recon_jobs/handlers.py` 建好 `run_bank_recon/run_glvat/run_salesvat(params, input_ref, progress_cb)` 三纯函数 · **0 改识别逻辑**(解析/对账原样调用 · 写现有结果表)· import 即 `register_handler` 接入 worker(bank/glvat/salesvat)· `_read_inputs` 按 role 从暂存目录读文件 · `_parallel`(ThreadPoolExecutor)复刻原 asyncio.gather 多文件并行 · 进度走 parse→reconcile→persist→done · 扣费/成本记录从 `create_task` 改工人线程内同步调。守门测试 `tests/unit/test_recon_handlers_contract.py`(10 个:签名/注册同一对象/读暂存保序/_parallel 保序/bank 正常+整侧全失败存诊断/glvat 正常+GL/VAT 0 行抛/salesvat 正常落盘)。**单元 428→438 全绿 · black/ruff(F)绿 · app import 绿**。⚠️ embedded worker 仍未 wire 进 app.py · handlers 当前完全休眠不影响线上。**下一步接 #15。**
   - ⚠️ **input_ref 约定(给 #15 落盘用)**:`[{"path","filename","role"}]` · role ∈ bank:`stmt`/`gl` · glvat:`gl`/`vat` · salesvat:`invoice`/`report`。
   - ⚠️ **params 约定**:bank=`{user_id,tenant_id,api_key,is_exempt,lang,gl_account,stmt_opening_override,gl_opening_override,gl_closing_override,stmt_closing_override}` · glvat=`{user_id,tenant_id,api_key,revenue_prefix,lang}` · salesvat=`{user_id,tenant_id,api_key,is_exempt,lang}`。
   - ⚠️ **result 指针**:bank→`("bank_recon_v2_task", id)` · glvat→`("gl_vat_task", id)` · salesvat→`("vat_recon_tasks", uuid)`(前端用现有 `/tasks/{id}/download` 取 Excel)。
2. **#15 接口改 submit** ✅ **完成(2026-05-24 第十三会话 · 加性/不破老流程)**:新建 **`recon_jobs_routes.py`**(铁律 #17 独立 router)· 三个 submit 接口(`POST /api/recon/bank-v2/submit`、`/gl-vat/submit`、`POST /api/vat_excel/submit`):鉴权+校验+credits 前置检查 → 文件落盘暂存 `STAGE_DIR/<job_id>/`(job_id 预生成)→ `store.enqueue` 建 job → 秒回 `{ok, job_id}`。统一 `GET /api/recon/jobs/{id}` 返 status/progress/result_table/result_id/error_code(前端据 result_id 调现有结果接口渲染/下载)。`app.py` include 新 router + lifespan 启动事件 `store.ensure_table()` + `worker.start_embedded()`(`PEARNLY_SKIP_HEAVY_INIT` 下不起 · `RECON_ASYNC!=1` 可秒回滚)+ 关闭 `stop_embedded()`。`store.enqueue` 加 `job_id` 预生成参数 · `store.ensure_table()` 幂等建表(Zihao 拍板启动自动建 · 不手动 alembic · DDL 与 003 逐字一致)· `worker.run_worker` 启动也 ensure_table。守门测试 `test_recon_jobs_submit_contract.py`(9 个:4 路由契约+app 挂载/enqueue 显式 id/ensure_table DDL/bank submit 落盘+enqueue/credits 402/jobs 命中映射+404)。**单元 438→447 全绿 · black/ruff(F)绿 · app 4 路由注册验证 ✓**。
   - ⚠️ **加性策略**:老 `/run` 接口**完全没动** · 现前端仍用它 · embedded worker 上线后只是空转(无 job 入队)· 对 mrerp 零影响。**真正切流量靠 #16 前端改调 submit。** 无版本号/release_notes(无用户可见变化)。
   - ⚠️ **剩 #16**:三个 run 前端改 submit→轮询 jobs/{id}→用 result_id 调现有结果接口渲染 · 三处 `.json()` 兜底 · cache_bust + 4 语 release_notes · **碰 live home.js(付费用户)· 需浏览器实测 · 建议 Zihao 在场做**。
3. **(原 #15 内容已并入上方)**
3. **#16 前端**:三个 run 前端 → submit→轮询 jobs/{id}→用 result_id 调现有结果接口渲染(渲染/导出/历史**不改**)· **Zihao 要求:不加进度条 · 在现有"转圈处理中"图标旁加"共 X/Y 页"实时进度**(两文件用连续编号区分 stmt→gl)· 三处 `.json()` 全加兜底(铁律 #1 · gl-vat/vat_excel 一并)· cache_bust+release_notes。
4. **#17 测试+部署**:守门测试(生命周期/分发/SKIP LOCKED 并发/状态接口/端到端)+ 生产建表 + 启 embedded worker(单 1.9G 机内存够 · standalone 会双份 ML 内存慎用)+ 用 mrerp 真文件(`D:\Users\Skin\Desktop\银行对账需求\报错`)灰度验证端到端跑通。

**关键约束**:embedded 工人优先(1.9G 内存机 standalone 会 OOM)· 结果写老表不动历史/导出 · RECON_ASYNC flag 可秒回滚 · 不碰 OCR/识别逻辑。

---

## 🆕 2026-05-24 第十二会话 · B1 抽 route_helpers 公共模块 · ⚠️ 下窗口必读

**模式**:Zihao 在场 · 选了上窗口推荐的"抽 route_helpers"(B 阶段提速关键 · 纯后端低风险)。

**做了什么(commit `a295515` · push master · 已部署 · 生产存活 ✓)**:
- 新建 **`route_helpers.py`** · 集中 5 个被多路由组共用的 helper:`_require_super_admin` / `_require_owner_or_super`(含懒建 tenant)/ `_log_op` / `_get_client_ip` / `_check_password_strength`(+ `_WEAK_PASSWORDS` 弱密码黑名单)· 从 `auth`/`db` import 防循环 · 纯搬家不改逻辑/返回值/异常 code。
- **app.py** 删这 5 个定义 + 常量 · 改 `from route_helpers import ...`(只 import 它直接用的 4 个)· **9546→9417 行(净 -129)**。
- **去重(铁律 #1 修一类)**:`billing_routes.py` 与 `admin_diagnostics_routes.py` 之前各自复制了一份 `_require_super_admin`(注释里早写了"待抽公共 helper 时合")· 删拷贝 · 改 import route_helpers · 三处共用同一对象。
- 连带清掉因删函数产生的孤儿 import:app.py 的 `fastapi.status`(顺带消两个 F811)· billing 的 `typing.Any/Dict` · admin_diagnostics 的 `auth.get_current_user_from_request`。
- 守门测试 `test_route_helpers_contract.py`(12 个:import 契约 / **单一来源 identity(防再各自拷贝漂移)** / 密码强度 5 分支 / client_ip XFF+回退+无 client / 超管 403+放行)。
- 守门全绿:imports / i18n(0/0)/ **unit 428**(416+12)/ black / ruff(F 集)。

**⚠️ 提交踩的一个坑(已自纠)**:`git add -A` 把之前遗留的未跟踪 scratch 目录(`_deploy_nginx/`/`_test_reports/`(含一堆 PNG)/`probes/`/`recon-i18n-fixes md`)一起扫进了 commit · 发现后 `git reset --soft HEAD~1` 回退 · 只 `git add` 我那 5 个文件重新提交(未 push 前自纠 · 没碰红线)。**教训:提交前用 `git add <具体文件>` 不要 `-A` · 本地有遗留未跟踪文件。这些 scratch 目录建议 Zihao 决定 gitignore 还是清理。**

**为什么这次没动版本号/release_notes**:纯后端内部重构 · 0 用户可见变化 · 照 B1 前几次范式 · 验证点 = 生产 /api/version 仍 200(= 新 import 结构启动不崩 · 防循环 import/NameError)。

**下窗口可做(route_helpers 已解锁)**:① 抽 **team_routes.py**(7 路由 · 现在可直接 `from route_helpers import _require_owner_or_super, _log_op`)② 抽 **history_routes.py**(7 路由 · 含 assign_client · 依赖 `_async_run_exception_checks`/`_check_history_access`→`_plan_permissions` · 这几个还在 app.py · 评估是否也搬 route_helpers 或单独处理)③ Zihao 在场时开 C1 前端拆 home.js ④ 帮 Zihao 收 A3/A4。

---

## 🆕 2026-05-24 第十一会话 · 自主长跑 · B1 连抽 clients + exceptions 两个 router · ⚠️ 下窗口必读

**模式**:Zihao 授权"自主长跑到上下文 80% 自动收尾"· 任务 = 前后端搬家(B1 拆 router + C1 拆 home.js)。

**实际做了(全 push master · 已部署 · CI clients ✅ / exceptions 跑中)**:
- **clients_routes.py**(commit `f27ac38`)· 抽 /api/clients 5 路由(GET/POST/PATCH/DELETE + /export)· 搬 ClientCreate/Update + _serialize_client · contract 测试 5 个 · 生产存活 ✓
- **exceptions_routes.py**(commit `30f114f`)· 抽 /api/exceptions 6 + /api/exception-whitelist 2 = 8 路由 · 顺手清死代码 ExceptionResolvePayload · contract 测试 3 个 · 生产存活 ✓
- 范式照 B1 notification:`APIRouter()` + 从 auth 拿 get_current_user_from_request + `_tid` 复制防循环 import · 纯搬家不改逻辑/URL/response。
- **app.py 9923→9546 行**(净 -377)· 守门:imports/i18n(0/0)/unit(**416**)/black/ruff 全绿。

**⚠️ 必须知道的一个债(CRLF→LF)**:抽 clients 那次我用 Python 整写 app.py · 把它从 CRLF 误转成 LF · commit `f27ac38` 出现一次性"全文件 diff"(10044+/9921-)· 因 **force-push 是铁律 #16 红线没回改** · 之后 app.py 统一 LF · 后续 diff 已恢复干净(exceptions 那次 4+/151-)。**教训:改 app.py 一律用 Edit 工具(保留 LF)· 不要再用 Python readlines/writelines 整写带 CRLF 的大文件。**

**为什么没做前端 C + team/history(自主长跑下的稳妥取舍)**:
- **前端 C1(home.js→src/home/*)主动不做**:要 Vite build + 改 home.html script + cache_bust + 4 语 release_notes + 部署**付费用户实时 UI** · 且没有像后端 /api/version 那样的廉价验证(需真浏览器测)· 无人值守自动关机前部署前端风险过高 · 留 Zihao 在场时做。
- **team(7 路由)**:依赖 `_require_owner_or_super`(用 20 次)/`_log_op`(13 次)等共享 helper · 干净做法要先抽公共 helper 模块(`route_helpers.py`)· 是更大的活 · 半途遇关机会把 app.py 弄坏 · 没在长跑里硬塞。
- **history(7 路由 · 含 assign_client)**:依赖 `_async_run_exception_checks`/`_check_history_access`→`_plan_permissions` 较缠 · 同上。

**下窗口可做**:① 抽 `route_helpers.py`(把 `_require_owner_or_super`/`_require_super_admin`/`_log_op`/`_get_client_ip`/`_check_password_strength` 集中)→ 解锁 team/history/admin 一大批 router(B 阶段提速关键)② 或 Zihao 在场时开 C1 前端拆第一个 home.js 模块 ③ 帮 Zihao 收 A3/A4(Docker build + doppler CLI 验证)。

---

## 🆕 2026-05-24 第十会话 · A3 本地 Docker + A4 Doppler 密钥收拢 · ⚠️ 下窗口必读

**主线**:Zihao 拍板 A3/A4 方向 · 推进两项(commit `df727f6` · push master)。

**A3 环境分级 = 本地 Docker**(Zihao 拍板不开第二台 Vultr):
- 交付:`Dockerfile`(python:3.11-slim 对齐 CI + lock 依赖)+ `.dockerignore` + `docker-compose.yml`(staging:app + 本地 postgres16)+ `docker-compose.dev.yml`(挂源码热重载)+ `docs/refactor/adr-003-local-docker-env.md`。
- **prod 部署链完全未动**(仍 git pull + systemctl)· Docker 只做本地 staging/dev。
- ⚠️ **本机未装 Docker · build 未验证** · 待 Zihao 装 Docker Desktop 后跑 ADR-003 验证清单(镜像含 torch ML 栈 · 首次 build 慢/大属正常)。

**A4 Secrets = Doppler**(Zihao 拍板 · 个人免费):
- Zihao 注册 Doppler + 建 project `pearnly`(三环境 dev/stg/prd)。
- **第 1 步收拢完成**:生产 `/opt/mrpilot/.env` 经 scp(Zihao 自己跑 · 密钥不经 AI)→ 去重 + 补本地 MRERP + 剔除 2 条死代码 demo 密码 → **39 条导入 Doppler `prd`** · 桌面明文临时文件已删。
- 迁移 4 步计划(防删错)见 `docs/refactor/adr-004-doppler-secrets.md`:① 收拢 ✅ → ② 本地 `doppler run` 验证 → ③ 生产改用(碰红线)→ ④ 清理旧密钥(都待做 · ⛔ 不可提前删)。

**遗留小债**:demo 账号死代码(`db.py` `ensure_demo_account` · 老套餐 free/plus 模型建 · credits 迁移后登不上)· 删环境变量无用(代码有默认值)· 真清要改代码 · 归整顿 I2。

**守门**:imports/i18n/unit 全绿(403 tests)· 纯新增 infra 配置/文档 · 0 业务代码改动。

**🆕 同窗续作 · B1 后端拆 router 开工**(Zihao 授权长跑):
- 抽出**第 1 个** `notification_routes.py`(通知规则 6 路由:GET/POST /rules · PATCH/DELETE /rules/{id} · POST /rules/{id}/test · GET /logs)· commit `c0b29eb`。
- 纯搬家不改逻辑 · `_tid`/`NOTIF_TEMPLATE_*` 复制防循环 import(app.py 保留)· models + `_validate_template_params` 整移。
- **app.py ~10075→9923 行**(净 -152)· 守门测试 `test_notification_routes_contract.py`(5 个 · 路由契约+include挂载+校验逻辑)。
- 守门全绿:imports/i18n/unit(**408**)· black/ruff · **生产 /api/version 存活验证 ✓** · CI lint job 绿(test job 跑中)。
- **B1 模式已跑通**(照 billing_routes 范式 · 从 auth 拿 current_user 防循环)· 后续 router 照此抽:候选 /api/clients(4)、/api/team(7)、/api/history(7)、/api/exceptions(6)等边界清晰组。

**下窗口可做**:① 续抽后端 router(B1 模式已验证 · 低风险)或转前端 C(home.js→src/home/*);② 帮 Zihao 完成 A4 第 2 步(doppler CLI 本地验证)+ A3 build 验证。

---

## 🆕 2026-05-23 第九会话 · 整顿 REFACTOR-A5(CI lint)+ 8 条硬门槛 · ⚠️ 下窗口必读

**主线**:回归工程整顿 · 完成 REFACTOR-A5(CI 加 lint + format)· Zihao 拍板"全量 auto-fix 一次到位"。

**做了什么(commit `5ae7bd0` · push master · CI 双 job 全绿 · 已部署)**:
- **后端**:`pyproject.toml` 配 black(line-length 100)+ ruff(select=F 起步集)· **129 个 .py 全量 black 格式化** + ruff 99 处安全自动修。
- **lint 顺手修出 2 个真 bug**(Zihao 拍板修):① `db.py` 对账降级查询 `date` 未导入 → 每次 NameError 恒返空;② `bank_recon_v2.py` GL 提示词 `.format()` 把 JSON 示例 `{date:...}` 当占位符 → KeyError 崩 → GL 解析永久失败。
- **前端**:`.prettierrc`(tabWidth 4 配现状)+ `.prettierignore` + `eslint.config.mjs` · 格式化 **18 个可维护文件**(src/home · static · e2e · 配置)· **巨石 home.js/css/html + login.html + nav 原型经 .prettierignore 豁免**(阶段 C 拆解目标 · 现格式化=20万行丢弃 diff + 毁 git blame · 已标 C1/C2/C3)。eslint 0 error(58 warning 仅提示 = 静默吞错债 I1)。
- **CI**:`ci.yml` 加并行 lint job(black --check / ruff / prettier --check / eslint)· `requirements-dev.txt` 锁 black/ruff · prettier/eslint 进 devDependencies。
- i18n 守门验证不破(prettier 不动 home.js · check_i18n 0/0)。

**🔑 同窗 Zihao 拍板:整顿期 8 条硬门槛**(见 `REFACTOR_MASTER_PLAN.md` 专段 + 铁律 #23):
- 止血:app.py 不许新增路由(进 *_routes.py)· db.py 不许新增 ensure_*(只 Alembic)· home.js 不许新增业务模块(进 **src/home/*** · 更正旧"static/*.js IIFE"措辞)。
- 测试:每拆模块带守门测试 · 核心路径至少 1 个 E2E/integration。
- 度量:coverage 不死磕 70% 改"每月只升不降"棘轮 · /ready 必须能真失败 · 进度脚本必须诚实。

**顺手修 `scripts/refactor_progress.py`**(硬门槛 #8 · commit 同批):① 数对位置(`static/home/*`→`src/home/*`)② integration 不再写死 0(真数 `tests/integration/` · **实际有 20 个 · 之前一直误报 0**)③ ESLint 检测加 `eslint.config.mjs` + 加 Prettier 检测 ④ 模块/测试得分每类按目标封顶(防 services 31/10 超额掩盖 home 模块化 2/50 · 模块化进度从虚高 84% 修为诚实 32%)。修后**综合进度 48%**。

**🆕 同窗长跑续作 · 自主跑完 A8 + A6(CI 全绿 · 无需 Zihao 介入)**:
- **A8 覆盖率 baseline**(commit `c818578`)· coverage.py 跑 unittest · **baseline 22.5%**(403 tests)· `pyproject [tool.coverage]` 配 `fail_under=21`(留 1.5pt 缓冲 · 真地板 · 硬门槛 #6 棘轮:覆盖率掉到 21% 以下 CI 红 · 提升后手动上调)· ci test job 改在 coverage 下跑 + `coverage report` 强制 · codecov 上传需账号暂缓。
- **A6 安全扫描**(commit `ed8b5af`)· **bandit**(HIGH 拦门 · 顺手清 2 处 md5 行指纹 HIGH 加 `usedforsecurity=False`)+ **pip-audit**(代 safety · 免注册账号 · `-r lock --no-deps`)+ **npm audit**(high 拦门)· 三件套 baseline **全 0** · CI 绿。
- master plan 原写 "safety" · 改用 pip-audit(safety 新版需注册账号 · 与自主跑冲突 · 已入档说明)。

**⛔ A 阶段收官只剩 A3 + A4 · 都卡 Zihao 决策(AI 无法自主)**:
- **A3 环境分级**(prod/staging/dev):需 Zihao 定 ① 开第二台 Vultr(花钱)还是 Docker 本地 ② 会动部署链(git-deploy/webhook)触红线。
- **A4 Secrets**(.env → Doppler/1Password):需 Zihao 注册付费账号 + 迁真密钥。

**下窗口第一步**:读 `REFACTOR_MASTER_PLAN.md`"当前进度看板"。A 阶段要往下走 = 先找 Zihao 拍 A3 方向(服务器 vs Docker);否则可跳去 **B 阶段**(后端拆 router · 依赖 A1/A5 已满足)或 **C 阶段**(前端拆巨石 home.js → src/home/*)。

---

## 🆕 2026-05-23 第八会话 · 银行对账闭环 + 14 份实测 + 改善计划收尾 · ⚠️ 下窗口必读

> 完整交接见 [`HANDOVER_TO_NEXT_WINDOW.md`](../HANDOVER_TO_NEXT_WINDOW.md)。当前线上 **v118.35.0.67** · `home.js?v=11835067`。

**做了什么(全 push master · 已部署)**:
- **坐标感知文本解析根治密集件**:BAY 314/31、KBank 266/33、SCB —— 全免费、Gemini 调用 0(原以为做不到的 KBank 合并列用 x 聚类攻克)。
- **KTB 多账户 .xls 静默错误修复**(归零户期末 0 被丢 + 空期初数学反推 + 逐账户完整性交叉校验)。
- **期初/期末兜底回填**(AM)+ **缺页醒目提示**(BBL 只传末页)。
- **14 份真实账单全量 UI 等价实测 + 逐行核对**:行级准确率 ≈99.9%(真错 2 处:AMZ 漏 1 笔、BBL2645 误读 1 笔扫款行 · **全部主动告警**)· 2 份 BBL 是**源文件缺页**非引擎错。导出件在 `probes/_ui_downloads/`。
- 评测集 **10 份标准答案** `tests/eval/ground_truth_local/`(eval 10/11 ✓)。

**🔑 关键决定(Zihao 2026-05-23 拍板)**:
- **M4 银行对账闭环收尾**(已很扎实 · 不再抠细节)。
- **M1/M2/M3 暂缓** · 等用户反馈具体问题再逐一改。
- **学习机制(用户纠正→产品越用越准)= 完整设计已出 · 但全部不做**(不要空壳/半成品)。设计落点:审计 Phase 2/3 + 本会话讨论(值记忆 vs 模板记忆 / `field_correction_memory` 库 / Excel 回传 diff / 自我纠偏)· 真要做从切片 S1(建库 + 接 M1 现有纠正入口)起。
- **改善计划就此收尾 · 下窗口回归 `REFACTOR_MASTER_PLAN.md` 工程整顿(从 A5 续)**。

**外部 OCR 模型(Qwen2.5-VL 72B / PaddleOCR-VL)**:评估结论**暂不值得**(见 HANDOVER §9)· 文本件已免费解决、单页扫描件 Gemini 够用 · 等遇到"完整多页密集扫描件还漏读"再用评测集量化决定 · 定位是第二证人不是替换。

**commit**:`e267b1a`(v0.66 坐标解析+KTB.xls)· `ce00960`(v0.67 期初期末回填+缺页提示)· `da380a7`(交接+§9)。

---

## 🆕 2026-05-23 第七会话 · 银行对账 OCR 可信度攻坚 · ⚠️ 下窗口必读

> **完整交接见 [`HANDOVER_TO_NEXT_WINDOW.md`](../HANDOVER_TO_NEXT_WINDOW.md)**(本会话主线 + 路线图 + 代码地图 + 铁律 · **下窗口第一件事就读它**)

**主线**:用 skin 今天搞到的 **7 份真实泰国银行账单**(`D:\Users\Skin\Desktop\账单`)压测银行对账,修一批"误导用户/让用户兜底"的问题。心法:**0 静默错误**(错的必标、可证的自动修并标注、看不清绝不猜)。

**本会话 commit(全 push master · 已部署)**:

| 版本 | commit | 内容 |
|---|---|---|
| v0.61 | `a80b054` | 对账诚实化(diff=0 恒等式假象 → 匹配率指标+低匹配不染绿)+ 多账户.xls 分账户校验(KTB) |
| v0.62 | `adea687` | Gemini **temperature=0**(根治同图结果飘)+ 余额链**自动修复金额**(可证才改+标✎已修正) |
| v0.63 | `d0739fc` | **完整性交叉校验**(页脚笔数/合计抓漏行)+ **持久化磁盘缓存** + max_output_tokens |
| v0.65 | `38b576b` | **OCR 评测集**运行器 `tests/eval/`(让改进可量化) |

**🔴 本会话最大发现**:密集多页扫描件被**系统性漏读 30-40%**(BAY 页脚 314 笔/只读 179 · KBank 266/199)· 余额链对"读出来的部分"自洽所以以前没发现 · 完整性校验首次抓到。**根治 = 逐页识别再合并(下窗口 OCR 头号任务 · 见 HANDOVER §3 P1)**。

**下窗口路线(skin 已拍板 · 做①②③免费 · Document AI④暂不做)**:① 逐页识别(根治漏读)② 标注评测集量化 ③ few-shot 提示词(本会话未做 · 原因见 HANDOVER §3 P3)。

**收尾欠账**:few-shot 未做、逐页识别未做、评测集只起头 AM(BAY/KBank 待标注)。`test_mrerp_*`/chromium 报错是既有环境问题非回归。

---

## 🆕 2026-05-23 拍板新铁律 · release_notes 覆盖式 + 官方语言(CLAUDE.md §6 升级)

**触发**:Zihao 2026-05-23 反馈 release_notes prepend 链太长 + 内部叙事 / emoji 不够专业

**新规则全文** 见 `CLAUDE.md/CLAUDE.md` §6 中段「🔒 2026-05-23 Zihao 升级铁律(覆盖式 + 官方语言)」

**核心 3 条**:
1. ❌ 禁止 prepend 老版本说明 · 每次部署 4 语字段**完全覆盖** · 只剩本次更新
2. ❌ 禁止口语化 / emoji(🚨 / 客户反馈 / 大白话 / hotfix / BUG-FIX 编号)· 用**标准官方语言**(已优化 / 即日生效 / 系统更新)
3. ❌ 禁止开发术语(根因 / 修法 / datetime / regex 等)· 用用户能懂的描述

**守门测试**:`tests/unit/test_release_notes_no_history.py`(4 契约 · 锁住未来 agent 不能再 prepend / 加 emoji / 加开发术语)

---

## 🔧 2026-05-23 新增能力 · Claude 可直接看 GitHub Actions CI(gh CLI 已装 + 已登录)

**全文** 见 `CLAUDE.md/CLAUDE.md` §22(铁律 #22 · CI 状态可视化能力)

**接力 agent quick reference**:
- gh CLI 路径:`C:\Program Files\GitHub CLI\gh.exe`(绝对路径调 · 不依赖 PATH)
- 已登录:`skin306152-star`(keyring 持久 · 跨 session 不丢)
- Repo:`skin306152-star/pearnly-app`(私库)
- **优先用 PowerShell tool 调** · 不用 Bash(PATH 没刷新到 gh)

**最常用命令**:
```powershell
# 看 master 最近 CI 状态(push 后必跑 verify)
& "C:\Program Files\GitHub CLI\gh.exe" run list --repo skin306152-star/pearnly-app --branch master --limit 5
```

---

## 🆕 2026-05-23 第六会话累计交接(用户换窗口前)· ⚠️ 下窗口必读

**会话主题**:整改 Phase 0 + Phase 1 P1.1 + GL Excel 紧急 hotfix(5 个 T1-T5)+ 4 anchor 完整化 + 规则铁律升级 + CI 能力入档

### 📦 第六会话累计 commit list(12 个 · 全 push master · webhook 自动 deploy 生效)

| Commit | 版本 | 内容 | 类别 |
|---|---|---|---|
| `64a84ca` | v0.37 | P0.1 OCR 抽到的 3 anchor 值预填 input(localStorage 跨会话)| 整改 Phase 0 |
| `ffd15b4` | v0.38 | P0.2 Excel 末尾加『手动录入痕迹』section + 标黄被覆盖 cell | 整改 Phase 0 |
| `735c834` | v0.39 | P0.3 历史详情/结果页显示『OCR vs User 对照表』+ 4 语 | 整改 Phase 0 |
| `eb2a55a` | v0.40 | P0.4 6 类 modal flex-chain audit + .modal/.drawer 防御性 min-height:0 | 整改 Phase 0 |
| `a8d24d7` | docs | Phase 0 整改全收官 · 4 commit + 4 Decision Points 全敲定入档 | 文档 |
| `5ca45a0` | v0.41 | P1.1 4 模块 task 表加 field_overrides JSONB(**Alembic 002 首次真迁移**)| 整改 Phase 1 |
| `714a1cc` | (无) | Dependabot ignore google-ai-generativelanguage + close 红 PR #11 | CI |
| `138d73e` | v0.42 | **T1** GL Excel 上传 0 行(根因泰国佛历 datetime cell)+ _parse_date 4 层兜底 | 紧急 hotfix |
| `456e381` | v0.43 | **T2** GL Excel 期初/期末读 balance 列 + release_notes 覆盖式新规则落地 + CLAUDE.md §6 升级 | 紧急 hotfix + 规则 |
| `21486c2` | v0.44 | **T3** 加第 4 个 anchor `stmt_closing`(Statement 期末)+ Excel lang 跟随守门契约 | 紧急 hotfix |
| `8b4cfd0` | v0.45 | **T4** anchor 预填 UX 加强(橙色 banner + 浅橙底 cell + 来源标识)| 紧急 hotfix UX |
| 本次 | v0.46 | **T5** M3 parse_gl_excel datetime BE→CE 同步 + M2/M3 export lang 守门契约 + CLAUDE.md §22 CI 能力入档 + 本交接段 | 同步 + 文档 |

### 🟡 下窗口接力 · 待跟进 / 未完成清单

**A · 待客户验证(等 Zihao 转发付费用户测)**:
1. **T1+T2 GL Excel 0 行修复**:客户重新上传同款 GL Excel 看『แถวที่พบ』≥1 行 + opening/closing 都对(完整闭环 · 不用 anchor 兜底)
2. **T3 第 4 个 anchor 上线**:对账页面看到 4 个录入框(横排:GL期末 / Statement期末 / Statement期初 / GL期初)
3. **T4 预填 UX 加强**:橙色 banner + 4 input 浅橙底 + label 后缀『· OCR』· 点击改字色变黑
4. **T5 M3 收入对账 date 显示**:GL Excel 文件含 BE datetime cell 时 · M3 历史详情 / Excel 显示 ISO CE date(不再 garbage)

**B · 我未完成的工作(stopped at)**:
- **Phase 1 P1.2-M2**(销售税对账 Excel 加来源列 + 标黄)· 我之前看到 `recon_routes.py L786 row_action` 路由就停下处理 T1-T5 紧急 BUG · **0 代码改**
- 下窗口接 P1.2-M2:看 vat_excel_exporter.py · 升级 row_action 写入 reconciliation_row.field_overrides + Excel 加 OCR vs 手改 layout · 1 commit 完闭环

**C · Phase 1 整改剩余 task list**(audit doc §5):
- P1.2 ✅ 4 模块 Excel 加来源列 + 标黄(M4 已 P0.2 + M2 我停在路上 · M3/M1 未开始)
- P1.3 历史详情显示对照 + 用户改痕迹时间线(4 模块)
- P1.4 字段级 confidence 接到前端(M1+M2+M4)
- P1.5 低置信度警告 toast(M1+M2+M4 · 依赖 P1.4)
- P1.6 M3 加用户校对 UI(跟 M2 row_action 对齐)
- P1.7 M3 加 3 anchor 余额手动录入(跟 BUG-B 同款 · 现在加上后还要扩到 4 anchor)

**D · 整顿期(REFACTOR_MASTER_PLAN.md)冻结状态**:A 阶段 4.5/10 · 整改完后继续 A5(CI lint)/ A6(依赖锁定加固)等

**E · Dependabot 未处理 PR**(`gh pr list --state open` 看)· 整顿期 A5/A6 统一清:
- 2 红:#8 pdfminer-six / #5 vite major(major upgrade · 大概率 breaking · 需 ignore 锁版本范围)
- 6 绿:#10 sqlalchemy / #9 alembic / #7 cryptography / #4 actions/upload-artifact / #3 actions/setup-node / #2 actions/setup-python
- 6 绿合并要本地 pip-compile regen lock(CONTRIBUTING.md §依赖管理)· 不是 1 commit 能搞定
- **#2/#3/#4 升 Node 24 兼容版本能解 2026-09-16 Node 20 deprecation**(到期前必须合)

**F · 整改决策 4 个全锁(防接力反悔)**:
1. ✅ Phase 0 立刻干 → 已完成
2. ✅ Phase 1 拆 7 commit 接力 → 下窗口接 P1.2 起
3. ✅ Phase 3 P3.1 分工:Claude 写脚本从 ocr_history 抽 top 50 vendor + Zihao 跑 Supabase 导出
4. ✅ Phase 4 X1/X2/X3 全永久锁死(用户自定义公式 / 100% 自动化 / 自训 OCR)

### 📋 下窗口启动顺序(60 秒 checklist)

1. `git branch --show-current` → 确认 master(铁律 #14)
2. 读 `CLAUDE.md/CLAUDE.md` 顶部 22 条铁律(重点 #21 整改不污染 / #22 CI 能力 / #6 release_notes 覆盖式)
3. 读 `docs/audits/2026-05-22-ocr-recon-audit.md` 整改单一权威源(更新到 T5 后状态)
4. 读本文档(STATE_PEARNLY.md)头部到此交接段
5. **跑 `& "C:\Program Files\GitHub CLI\gh.exe" run list --repo skin306152-star/pearnly-app --branch master --limit 5`** 看 T1-T5 CI 状态(确认 5 个 push 全绿)
6. 跑 `python -m unittest discover -s tests/unit 2>&1 | tail -5`(应该 331+ tests OK)
7. 看 Zihao 反馈:客户测 T1-T5 结果 / 是否继续 Phase 1 P1.2 / 是否处理 dependabot 堆积
8. 按拍板顺序接 Phase 1 P1.2-M2(或 Zihao 改优先级再调)

### ⚠ 关键铁律提醒(下窗口最易踩坑)

- **铁律 #6** release_notes:**必须覆盖式**(不能 prepend 老版本)· **必须官方语言**(禁 🚨/客户反馈/hotfix/BUG-FIX-XX 编号)· 守门契约 `test_release_notes_no_history.py` 会自动 fail 强制改
- **铁律 #21** 整改不污染:新 schema 走 Alembic + 新业务函数禁进 db.py(进 `services/db_migrations/`)+ 新路由禁进 app.py(独立 `*_routes.py`)+ 新前端禁进 home.js(独立 IIFE)+ 新 CSS 禁进 home.css(独立 .css 或 scoped 组件 HTML)
- **铁律 #14** branch:每次启动 check `git branch --show-current` = master · 不在就切回去

---

---

## 🔴🔴🔴 整顿模式 ON(2026-05-22 起到约 2026-12)

**Zihao 2026-05-22 拍板**:封锁整顿 5-8 个月 · 路径 B 上 Vite + ES modules · 工程标准化到 Google / Anthropic Claude code 级。

**核心文档**:[`CLAUDE.md/REFACTOR_MASTER_PLAN.md`](REFACTOR_MASTER_PLAN.md)(整顿单一权威源 · 9 阶段 A-I · 60+ task)

**当前状态**:
- **阶段 A 工具链** 🟡 4.5/10(A0 ✅ + A1 ✅ + A2.1 ✅ + A7 ✅ + A9 ✅)· 阶段 A 已近 1/2
- **下一个 task**:**REFACTOR-A5 CI lint**(半天 · black + ruff + ESLint + Prettier)· 或 A3 环境分级(1-2 天)/ A8 Code Coverage(半天 · 依赖 A5)

**封锁条款**(铁律 #18):
- ❌ 0 新功能开发(P0-VAT v4.9.6 / Phase 6 进项管理 / MODULE_ROADMAP 全 hold)
- ✅ 只做 REFACTOR_MASTER_PLAN.md 9 阶段 task
- ✅ 紧急 BUG 修复允许(影响付费用户 / 数据安全 / 服务中断)

**接力 agent 必读 4 文档**(铁律 #19):
1. CLAUDE.md/CLAUDE.md(20 条铁律 · 重点看 #18-20)
2. 本文档头部(整顿模式段)
3. REFACTOR_MASTER_PLAN.md(找下一个 task + 完成判定)
4. 对应 task 的"完成判定"段

**commit message 格式**(铁律 #20):
```
<type>(<scope>): <subject> · REFACTOR-<task-id>

<body>

守门 5 道全绿:imports / i18n / unit / playwright / node

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

**完成定义**:home.js < 200 行 / app.py < 500 行 / 测试覆盖 ≥ 70% / API p95 < 1s / 50-100 模块文件 / Google 级 90%+

**自动统计脚本**:`python scripts/refactor_progress.py`(每窗口跑 1 次 · 看进度)

---

## 🆕 2026-05-22 第五会话续 2 · 🚨 整改模式开启 · 4 模块 OCR / 对账深度审计 + Phase 0-4 整改路线图

> **触发**:用户(Zihao)收到 1 个付费客户 OCR 不准投诉(BUG-B 是触发点)· 拍板整改 > 整顿
> **接力规则**:换窗口先读 [`docs/audits/2026-05-22-ocr-recon-audit.md`](../docs/audits/2026-05-22-ocr-recon-audit.md)

### 1 个 commit + 审计文档

- 审计文档:`docs/audits/2026-05-22-ocr-recon-audit.md`(~ 9000 字 · 4 模块摸排 + 横向对比 + 5 共性 gap + Phase 0-4 整改清单 + 跟整顿期协调 + 周计划)
- STATE 头部:整顿模式 → **🚨 整改模式 ON**(整顿暂停 · 整改优先)

### 4 模块边界澄清(本次定的标准命名)

| 编号 | 模块名 | 路由 |
|---|---|---|
| M1 | 上传发票区(OCR → ERP) | `POST /api/ocr/upload` + ERP push 路由 |
| M2 | **销售税对账**(销项税报告核查 · 发票 vs VAT 报告)| `/api/recon/*` + `/api/vat_excel/*` |
| M3 | **收入对账**(总账 GL vs VAT 报告)| `POST /api/recon/gl-vat/run` |
| M4 | **银行对账**(银行账单 vs GL)| `POST /api/recon/bank-v2/run` |

下文 + 整改清单都用 M1-M4 编号。

### 共性 Gap(整改的核心战场)

- **Gap A · OCR vs 手改痕迹** 4 模块全缺(M4 BUG-B 落库了但没导出展示)
- **Gap B · 字段级 confidence UI** 4 模块全缺(只有 M2/M4 有行级 · 没字段级)
- **Gap C · 用户改→OCR 学** 只有 M1 部分有(`buyer_to_client_memory` 客户名学习 · 别的字段不学)
- **Gap D · per-vendor / per-bank 模板学习** 4 模块全缺
- **Gap E · 统一校对面板** M2 有 row_action · M4 有 anchor 录入 · M3 完全没用户校对入口

### 整改 Phase 0-4 总览(详见审计文档)

- **Phase 0**(本周 · 4 个 task):BUG-B 3 个尾巴 + BUG-A 扫其他 modal
- **Phase 1**(2-3 周 · 7 个 task):4 模块加 OCR 痕迹 + 字段 confidence + 校对统一
- **Phase 2**(1 个月):用户改→OCR 学(扩展 `buyer_to_client_memory` → 全字段)
- **Phase 3**(2-3 个月):per-vendor / per-bank 模板库
- **Phase 4**(永久不做):用户自定义公式 / 100% straight-through / 自训 OCR 模型

### 整顿期 vs 整改

| | 整顿期(REFACTOR_MASTER_PLAN.md) | 整改(本次) |
|---|---|---|
| 状态 | **暂停**(冻结在 A 阶段 4.5/10) | **🚨 ON**(优先级最高) |
| 单一权威源 | REFACTOR_MASTER_PLAN.md | docs/audits/2026-05-22-ocr-recon-audit.md |
| commit 标记 | `REFACTOR-A7` 等 | `BUG-FIX-P0.1` / `BUG-FIX-P1.3` 等 |
| 完成时间 | 整改完后接着做 | Phase 0-1 大约 4 周 · 全 Phase 0-3 大约 4-5 月 |

### 重大决策(本会话续 2)

- **整改优先级 > 整顿**(2026-05-22 Zihao):1 个付费客户投诉直击 Pearnly 核心信任问题 · 不立刻修就跑路 · 整顿期推后无所谓
- **Phase 4 永久不做 3 条**(2026-05-22 Zihao 默认):用户自定义公式 / 100% 自动化 / 自训 OCR · 都明确不做 · 防接力 agent 反悔
- **4 模块统一命名**(2026-05-22):M1-M4 · 文档 + 代码注释 + commit message 都用
- **每个 Phase 0/1 task 独立 commit**(2026-05-22):拆 commit · 防一波带崩 · 5 道守门一波过

### 下窗口接力 · ⚠️ 必读!(给下个 Claude 窗口看)

**Phase 0 4 task 全部 commit + push 完成(2026-05-23 第六会话)· Decision Points 4 个全敲定:**
- ✅ Phase 0 本会话立刻干(完)
- ✅ Phase 1 拆 7 commit
- ✅ Phase 3 P3.1 Claude 写脚本 + Zihao 跑 + 导出
- ✅ Phase 4 X1 / X2 / X3 全锁死

**Phase 0 commits**:
- P0.1 · 64a84ca · v118.35.0.37 · OCR snapshot 落库 + 前端 localStorage 预填(M4)
- P0.2 · ffd15b4 · v118.35.0.38 · Excel 末尾加『手动录入痕迹』+ 标黄 + comment(M4)
- P0.3 · 735c834 · v118.35.0.39 · 历史详情 + 结果页显示 OCR vs User 对照表(M4)
- P0.4 · eb2a55a · v118.35.0.40 · 6 类 modal flex-chain audit + min-height:0 防御(全局 UI)

**净增长账**(铁律 #21 容忍上限内):
- home.js +181 行 / +1750 容忍 (10% 用量)
- home.html +17 行 / +650 容忍 (3% 用量)
- home.css +2 行 / +400 容忍 (0.5% 用量)
- app.py 0 净逻辑(只 release_notes 4 语 prepend)
- recon_routes.py +55 行(独立路由 · 非 app.py)
- bank_recon_v2.py +97 行(独立模块 · 非巨石)
- 新文档 docs/audits/2026-05-23-modal-flex-chain-audit.md +133 行
- 新测试 tests/unit/*.py +4 文件 +368 行(D 阶段 reward)

**守门累计**:imports / i18n 0/0 / unit 306 OK / node check 全绿 · 4 个 commit 均合规

**M4 银行对账『OCR vs 手改痕迹』Gap A 完整闭环** → 共性 Gap A 4/4 模块完成 1/4

---

**下窗口启动顺序**:
1. ✅ `git branch --show-current` → 确认 master(铁律 #14)
2. ✅ 读 `CLAUDE.md/CLAUDE.md` 顶部 21 条铁律(尤其 #21 整改期不污染未来整顿)
3. ✅ 读 **`docs/audits/2026-05-22-ocr-recon-audit.md`**(整改单一权威源 · Phase 0 已 ✅ · 重点 §5 Phase 1)
4. ✅ 读 `docs/audits/2026-05-23-modal-flex-chain-audit.md`(P0.4 audit + 未来 modal bug 修法预案)
5. ✅ 读本文档头部 + 第五会话续 2 段
6. ✅ Zihao 拍板:开 Phase 1?还是先让本周 Zihao 跑生产测 Phase 0 的 4 个新功能再开 Phase 1?
7. ✅ 开 Phase 1 → 按拆 7 commit 跑 P1.1 schema(借此激活 REFACTOR-A2.2 + B3 Alembic 真迁移)

**Phase 0 4 个 task 已收尾** ✅(都在 TaskList 历史里 completed):
- P0.1 · BUG-B-T1 ✅ v118.35.0.37 64a84ca
- P0.2 · BUG-B-T2 ✅ v118.35.0.38 ffd15b4
- P0.3 · BUG-B-T3 ✅ v118.35.0.39 735c834
- P0.4 · BUG-A-T1 ✅ v118.35.0.40 eb2a55a

**Phase 1 7 个 task 待启动**(详见审计文档 §5):
- #P1.1 · 统一 _field_overrides JSONB schema(1 天 · 借此激活 Alembic 真迁移 · 4 模块)
- #P1.2 · Excel 导出全部加来源列 + 标黄(2 天 · 跟 BUG-B-T2 同款 · 4 模块)
- #P1.3 · 历史详情显示对照 + 用户改痕迹时间线(2 天 · 跟 P0.3 同款 · 4 模块)
- #P1.4 · 字段级 confidence 接到前端(2 天 · M1+M2+M4)
- #P1.5 · 低置信度警告 toast(半天 · M1+M2+M4)
- #P1.6 · M3 加用户校对 UI(2 天 · 跟 M2 row_action 对齐)
- #P1.7 · M3 加 3 anchor 余额手动录入(1 天 · 跟 BUG-B 同款)

**🆕 铁律 #21 · 整改期不污染未来整顿**(2026-05-23 拍板 · CLAUDE.md §铁律 21):
- 新 DB 函数 → `services/<domain>/*.py`(不进 db.py)
- 新路由 → `*_routes.py`(不进 app.py)
- 新前端模块 → 独立 `static/*.js` IIFE
- 新 CSS → 独立 `.css`
- 新 schema → Alembic(借 P1.1 激活 A2.2 + B3 第一次真迁移)
- 每个 BUG-FIX task 加守门测试
- **遇不进巨石不会**:Claude 自判断 · 必要时暂塞 + commit 透明记(行数 + 原因 + 迁出 deadline)
- 容忍上限:home.js +1750 / home.css +400 / home.html +650 / app.py +300 / db.py +250(整改完跑 refactor_progress.py 看)

**commit 格式**(整改期):
```
<type>(<scope>): <subject> · BUG-FIX-P0.X
...
守门 5 道:imports / i18n / unit / playwright / node
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

**OCR 训练战略已锚定**(见审计文档 §10 FAQ):
- ✅ 走训记忆路线(memory-based / RAG)· 不走真训模型
- ✅ 知识存 Pearnly DB · 跨 OCR 厂商便携
- ✅ 1 个事务所 + 6 个月 = 够养记忆库
- ❌ **永远不自训 OCR 模型**(Phase 4 ❌ X3 永久不做)
- ❌ **永远不上 Vertex AI fine-tuning**
- **Claude 能做**:全部机制(schema / prompt 注入 / per-bank parser / per-vendor prompt)
- **Claude 能做**:自己爬数据 / 训神经网络 / 
- **Zihao 必须做**:给真发票 / 真银行账单样本(每 vendor 5-10 张 · 每 bank 3-5 份)· 跑生产测试 · 报错给 Claude 迭代 prompt

### ✅ Decision Points · Zihao 2026-05-23 全部敲定(下窗口直接按拍板执行)

1. ✅ **Phase 0 立刻干** → 已完成(4 commit · 4 task · 2026-05-23 第六会话)
2. ✅ **Phase 1 拆 7 commit**(1 task = 1 commit · 防一波带崩) → 下窗口接 P1.1 起
3. ✅ **Phase 3 P3.1**:Claude 写脚本从 ocr_history 自动抽 top 50 vendor · Zihao 跑 Supabase 导出给 Claude · Claude 做 prompt(分工锁定)
4. ✅ **Phase 4 X1/X2/X3 全锁死**(用户自定义公式 / 100% 自动化 / 自训 OCR · 永久不做)· 详见审计文档 §5 Phase 4 段

### 防偷懒(整改期专属)

- ❌ 整改期 grep `MODULE_ROADMAP.md` 想做新功能 → 立即停 · 整改也是『新功能闸口关』
- ❌ 整改期不做 REFACTOR-A5 等整顿 task · A 阶段冻结
- ❌ commit 不含 BUG-FIX-P0.X / P1.X 编号 → 偷整顿 · 算违规
- ❌ 帮 Zihao 训自家 OCR 模型 · 上 Vertex AI · 等任何走"真训"路的事情(Phase 4 ❌ 锁死)

---

## 🆕 2026-05-22 第五会话续 · BUG-A hotfix(设置 modal)+ BUG-B 破例新功能(收入对账 3 anchor)· 2 commit

> **接力规则**:换窗口先看本段

### 2 个 commit

| Commit | Type | 内容 |
|---|---|---|
| `4163408` | hotfix · BUG-A | settings modal 右栏在浏览器 zoom 67/75/80/90/100% 都看不到底部字段(LINE ID / 国家 / 公司信息 tab) · 根因 flex chain 在 px rounding 时高度解析失败 · overflow-y:auto 不触发。修法镜像 v118.34.39 左栏修法:直接 max-height: calc(min(85vh, 100vh - 64px) - 80px) · bypass flex chain。home.html L52-67 内联 defensive override + home.css L14273-14288 base rule 同步 · cache_bust 11835034 → 11835035 · release_notes 4 语 v118.35.0.35 |
| `5ccd989` | feat · BUG-B(破例) | 收入对账(/bank-v2)加 3 个 anchor 余额手动录入兜底:GL 期末 / Statement 期初 / GL 期初。OCR 抽这 3 个『锚点』不准时整张对账报告废 · Zihao 拍板紧急 BUG 修复一级(整顿期破例 1 次)。前端 home.html 加 .brv2-anchor-row(3 input + 实时『期初差额』提示)· home.js 4 语 i18n × 5 key + runRecon FormData 加 3 个 override · home.css 暖灰底 + 黑 focus · 后端 recon_routes.py /bank-v2/run 加 3 个 Optional Form override · summary._anchor_overrides 落库 {ocr, user} 对照 · cache_bust 11835035 → 11835036 · release_notes 4 语 v118.35.0.36 |

### BUG-B 客户原始诉求(2026-05-22)

客户截图(本地 `D:\Users\Skin\Desktop\BUG\BUG-B\`):
- 1.jpg 泰文聊天:OCR 算 ยอดยกไป GL / ผลต่างยอดยกมา 不准 · 报告对不上
- 2.jpg Excel 模板 + Pearnly UI 对比 · 紫色 bracket 圈出 OCR 算错的 3 anchor 数据区域 · 红色注解 ① "OCR 不准" + ② "应建 TEXT BOX 让客户录入这 3 个数"

### 重大决策(本会话续)

- **BUG-A 修法跟左栏对齐**(2026-05-22):不要重新发明 · v118.34.39 修过左栏 max-height calc 卡死 · 右栏直接镜像同款修法 · 不要尝试别的方案(已经吃过 4-5 轮 flex chain 教训)
- **BUG-B 破例新功能**(2026-05-22 Zihao 拍板):整顿期『0 新功能』红线 · 但客户对账报告对不上是 P0 影响付费用户准确率的紧急 BUG · 算紧急 BUG 修复一级 · 入档 ❗ 例外段(主计划)· 累计破例 1 次
- **3 anchor 不强校验业务等式**(2026-05-22):本来想加『GL 期末 ↔ 期初差额 audit equation』· 但实际等式还要扣除未匹配项 · 简单 == 校验会误报。改成单纯显示『期初差额 = stmt_opening - gl_opening』info 提示 · 不强制 · 让会计师肉眼判断
- **override 落库 {ocr, user} 对照**(2026-05-22):落 summary_j["_anchor_overrides"] · 用户回查任务能看出哪几个数是 OCR 抽的 / 哪几个是手填的 · 给业务对账信任度兜底

### 守门(BUG-A 跑 3 道 · BUG-B 跑 4 道)

- BUG-A:imports / i18n / unit 293 OK · 跳 playwright / node(没改 JS)
- BUG-B:imports / i18n(20 新 key × 4 语 0 missing 0 extra)/ unit 293 OK / node --check home.js EXIT=0 · 跳 playwright(E2E 跑 prod 着陆页不覆盖收入对账)

### 整顿期账(铁律 #18 跟踪)

- 累计破例次数:**1 次**(BUG-B `5ccd989`)
- 整顿期代码规模影响:home.js +57 行 / home.html +113 行 / app.py +8 行 / recon_routes.py +24 行 · 整顿期目标方向相反(home.js < 200 行)· 但缓解措施=阶段 C 拆 home.js 时 brv2 模块独立文件迁出 · 一并搬

### 必测清单(Zihao 自测 · 每项 ≤30 秒)

**BUG-A**(设置 modal 滚动):
1. 浏览器打开 https://pearnly.com · 登录 · 点头像 → 设置
2. Ctrl++ / Ctrl+- 切换浏览器缩放 67% / 75% / 80% / 90% / 100% / 125%
3. 每个缩放下点开『设置』· 右栏滚动到底部 · 看是否能看到 LINE ID / 公司信息 tab
4. 左栏导航(账户 / 公司 / 工作流 / 系统 / 关于)滚动看是否还正常(无回归)
5. 切 zh / en / th / ja 4 语 · 每语切一次 · 看 modal 没崩

**BUG-B**(收入对账 3 anchor 录入):
1. 进收入对账 tab(/home#/recon)· 上传 Statement PDF + GL · 不填 anchor · 跑对账 · 看跟以前一样走 OCR
2. 上传 + 填 1 个 anchor(随便填 9999.99)· 跑对账 · 看公式 KPI 用的是你填的 9999.99 不是 OCR 抽的
3. 上传 + 填 3 个 anchor 都不一样 · 跑对账 · 看 3 个都生效
4. 切 4 语 · 看 anchor label 都对(GL 期末余额 / ยอดยกไป GL / GL closing balance / GL 期末残高)
5. 手机端浏览器(devtools 切 iPhone 12)· 看 3 input 堆 1 列 · 不溢出
6. 填 Statement 期初 + GL 期初 · 第 3 个不填 · 看下面『期初差额』实时算出来

### 下窗口接力(给下个 Claude 窗口看)

- **当前 task**:REFACTOR-A5 CI lint(半天 · 风险中 · 涉及 black + ruff 自动 reformat 现有 .py · 建议先 `--check` 模式跑出 diff 给 Zihao 看 · 拍板再上自动 fix)
- **备选**:A3 环境分级(1-2 天 · 重)/ A8 Code Coverage(半天 · 依赖 A5)
- **本会话续遗留**:BUG-A / BUG-B 都需要 Zihao 部署后实测确认 · 若 BUG-A 任一缩放仍报告滚不动 → 看是否是其它 modal 同款病(brv2-formula / .modal / .upg-modal · 已扫但未修)· 若 BUG-B 业务等式有更复杂的稽核公式 · 加 ผลต่าง 校验(目前只 info display)
- **整顿期账**:本会话续破例 1 次(BUG-B)· 累计破例 1 次 · MASTER_PLAN ❗ 例外段已入档

---

## 🆕 2026-05-22 第五会话 · REFACTOR-A7 依赖锁定落地(1 commit)

> **接力规则**:换窗口先看本段

### 1 个 commit · pip-compile 全传递依赖钉死

| Commit | Task | 内容 |
|---|---|---|
| `296c074` | REFACTOR-A7 | 本机装 pip-tools 7.5.3 · pip-compile requirements.txt → requirements.lock.txt(299 行 · LF · 0 BOM · 全传递依赖钉死)· ci.yml `pip install -r` 改装 lock · cache-dependency-path 同步 · dependabot.yml 加注释说明 Dependabot 只改源 · CONTRIBUTING.md 加 §依赖管理 段(两层文件 + 改依赖流程 + Dependabot PR 处理) |

### 两层文件设计

| 文件 | 角色 | 谁改 |
|---|---|---|
| `requirements.txt` | **源** · 顶层依赖 + 大版本约束(`alembic>=1.13,<2.0`)· 人读 | 人 / Dependabot |
| `requirements.lock.txt` | **产物** · pip-compile 出 · 所有传递依赖钉死(`urllib3==2.7.0`)· CI / prod 装 | pip-compile 自动 · 不手改 |

### 重大决策(本会话)

- **pip-tools 7.5.3 不进 requirements.txt**(2026-05-22):本机 dev 工具 · 跟 alembic 一样不入 prod 依赖
- **lock 用 Python 3.10 生成 · CI 跑 Python 3.11**:大部分 pure-Python 包跨版本 OK · torch / openpyxl / cryptography 等核心都有 3.10/3.11 双 wheel · 若 CI 红再切 Linux 容器 regen
- **Dependabot 只改 requirements.txt 源 · lock 不动**:Dependabot 不原生跑 pip-compile · reviewer 合 PR 前手动 `python -m piptools compile` · 不然 CI 装老版本看不到升级效果(铁律 + CONTRIBUTING.md 入档)
- **不开 `--generate-hashes`**:加哈希后 lock 5967 字节 → 数十 KB · 编辑难 · 暂时不上 · 等阶段 B/C 后期再补

### 守门 3 道全绿(本会话)

- `python scripts/check_imports.py --quiet` → EXIT=0
- `python scripts/check_i18n.py --strict --quiet` → 0 missing 0 extra
- `PEARNLY_SKIP_HEAVY_INIT=1 python -m unittest discover -s tests/unit` → **Ran 293 tests in 2.154s · OK (skipped=2)**
- 跳 playwright + node:本 commit 未改 JS / login.html / home.js / 4 语切换

### 进度指标(refactor_progress.py 本会话末跑出)

- **工程化就绪**:4/8(50%) → **5/8(62%)**(加 requirements.lock ✅)
- **Google 级达标综合**:43%(代码规模 1% / 模块化 73% / 测试 22% / 静默 57% / 工程化 62%)
- 代码规模没动(本任务不改业务代码)· 测试 288→293 unit(+5 是历史漂移 · 不是本会话加的)

### 必测清单(本会话不必跑 · 纯配置改动)

- 无新 UI / 无前端改 → Zihao 不需要手测
- 等 GitHub Actions CI 跑 `cadb4b2..296c074` 全绿即视为生产可用
- 若 CI 红 · 看头部 step 是 import / install · 大概率 3.10→3.11 跨版本 deps 冲突 · 切 Linux 容器 regen lock

### 下窗口接力(给下个 Claude 窗口看)

- **当前 task**:REFACTOR-A5 CI lint(半天 · 风险中 · 涉及 black + ruff 自动 reformat 现有 .py · 建议先 `--check` 模式跑出 diff 给 Zihao 看 · 拍板再上自动 fix)
- **备选**:A3 环境分级(1-2 天 · 重 · 涉及 Docker / Vultr 第二台)/ A8 Code Coverage(半天 · 依赖 A5 · 简单)
- **本会话遗留**:Dependabot PR 第一次跑(下周一早 8 点 Bangkok 时区)· 合 PR 前必须 reviewer 跑 `python -m piptools compile ... -o requirements.lock.txt` regen lock
- **CI 守门**:`scripts/refactor_progress.py` 工程化 check 还差 3 项:Black / ESLint / Code coverage · 是 A5/A8 的事

---

## 🆕 2026-05-22 第四会话 · REFACTOR-A1 Vite 落地全 4 子(1 个会话内完成 · 3 commit)

> **接力规则**:换窗口先看本段

### 7 个 commit · prod 11835033 + Alembic + Dependabot 落地

| Commit | Task | 内容 |
|---|---|---|
| `e11e81d` | REFACTOR-A1.1 | 装 Vite 6.4.2 + 配 esbuild · 本地 build · src/main.js 占位 · src/package.json 局部 ESM scope · vite.config.mjs · 不动 playwright |
| `cfbb7d5` | REFACTOR-A1.2 | CI 加 vite build step(npm ci 后 / Playwright 前) · 守门从 4 关升到 5 关 · 防本地 build 漏跑 |
| `1c4c3bd` | REFACTOR-A1.3 | dashboard.js / billing.js 从 static/home/ 搬到 src/home/ · 改 ES module(去 IIFE)· Vite bundle 到 static/dist/main.js 15.11kB(gzip 5.03kB · 减 37%)· home.html cache_bust 11835031→11835032 · script tag 改 type=module · release_notes v118.35.0.32 4 语 · A1.4 自动验证 prod 通 |
| `086a981` | REFACTOR-A1.4 | A1 全 4 子完成入档 · 主计划 + STATE 更新 |
| `5a74a25` | hotfix | home.js L29630 `_renderTaskList` 加 null guard · 修部署后 console TypeError · 跟 Vite 改动无关(home.js 老 bug)· 加载顺序变触发 · cache_bust 11835032→11835033 |
| `4d5c8ba` | REFACTOR-A2.1 | 装 alembic 1.18 + SQLAlchemy 2 · alembic/env.py 从 env var 读 DATABASE_URL · 001_baseline 空迁移 · A2.2 git-deploy.sh 钩子并入 B3(真迁第一个 ensure_* 时再加) |
| `e57993a` | REFACTOR-A9 | .github/dependabot.yml · pip + npm + github-actions 3 ecosystem · 周一 08:00 Asia/Bangkok 开 PR · patch/minor 分组 · security 始终单 PR |

### A1.4 prod 自动验证(本会话)
- ✅ /api/version 返 version=11835033(含 hotfix)
- ✅ /static/dist/main.js?v=11835033 fetch 200 · 15107 bytes
- ✅ 旧路径 /static/home/{dashboard,billing}.js 404 · home.html 不再引用 · 无害
- ✅ Zihao Console 截图确认 vite bundle loaded + 报 _renderTaskList null bug · 已 hotfix 修

### hotfix 经验记录(本会话)
- A1.3 部署后 Zihao 截图发现 home.js L29630 `_renderTaskList` TypeError
- 根因:_rerenderAll(i18n / module init)在用户不在 sv 销项税页时调它 · DOM 元素 null
- 跟 Vite 无关(home.js 老 bug · _renderClientSelect L29732 已有同款 guard · _renderTaskList 漏)
- A1.3 改了加载顺序(main.js type=module vs 老 2 条 defer 链)· 触发时机变 → 沉默的 bug 跳出来
- 修:加 1 行 null guard · cache_bust 11835032→11835033 · release_notes 不动
- 教训:home.js 33k 行还有很多类似 null check 漏点 · 阶段 C 拆 home.js 时一并扫

### 重大决策(本会话拍板)
- **Vite build 方案 = 本地 build · 产物 static/dist/* 进 git · 服务器零改动**
- **home.js 33k 行不进 Vite · 阶段 C 后再纳入**(铁律 #18 渐进翻新)
- **顶层 package.json 不加 type:module · src/package.json 局部 ESM**(避免炸 playwright.config.js CJS)
- **A1.3 改 script tag 顺序**:home.js 同步 → main.js type=module 自动 defer · 等价原 dashboard/billing defer
- **A2.2 钩子并入 B3**(2026-05-22):A2.1 装好后 001 空迁移 · hook 是 no-op · 留到 B3 真要跑第一条迁移时再加 git-deploy.sh hook · 同步搞 `pip install -r requirements.txt` · 降低风险
- **Dependabot 不上 Renovate**(2026-05-22):GitHub 内置免费 · 不引入第三方 · A 阶段够用

### 必测清单(Zihao 自测 · 每项 ≤30 秒)
1. 浏览器打开 https://pearnly.com · 看头部"立即更新"横幅是否再弹(11835033)
2. 点更新 + 登录 · 首页 #/dashboard · 看 KPI 卡片有数据 + **F12 Console 不再报 _renderTaskList TypeError**
3. 点充值 · 看 3 步 modal 能开 · 输金额 + 看银行账号 + 关闭(不用真传)
4. F12 Console · 应该看到 `[pearnly] vite bundle loaded · dashboard + billing` · 没 ERROR
5. F12 Network · 看到 `/static/dist/main.js?v=11835033` 200 · 旧 `/static/home/dashboard.js` 不再 fetch

## 🆕 2026-05-22 第四会话续 · CLEANUP-PLAN 老订阅残留全清 · 2 commit

> **背景**:Zihao 截图 /admin/users 仍能看到 Trial/Pro/Firm KPI + 套餐分布 + Trial 即将到期 + 修改套餐 modal + 点确认升级真的写库。之前 v118.35.0.4/0.9/0.16 三次清理只清用户端 home.* · admin 后台漏。

### 2 个 commit

| Commit | Task | 内容 |
|---|---|---|
| `3cb8675` | CLEANUP-PLAN-01 + 02 | 后端 auth_signup.py 删 4 老订阅路由(/api/admin/users/upgrade · /payments/pending · /payments/{id}/screenshot · /payments/{id}/review) + AdminUpgradeRequest · funnel 改瘦 · admin SPA 三件套(admin.html/admin.js/admin-i18n.js)删套餐 KPI/修改套餐 modal/套餐 badge/升级按钮/36 i18n key · 净减 457 行 |
| 本 commit | CLEANUP-PLAN-03 + 04 | home.* 用户可见 3 处改文案 · home.html "订阅 & 套餐" → "账户 & 余额" · 设置页"套餐 & 用量" → "用量" · home.js 4 语 i18n value 12 处改 · cache_bust 11835033 → 11835034 · vite rebuild · release_notes v118.35.0.33 4 语 · 主计划 I2 ✅ 部分 · 本档 |

### 留下窗口清的(2026-05-22 截至:home.js 死代码)
- L22200+ admin SPA 独立前老 loadAdminUsersPage 逻辑(NAV-IA Phase 8 留)· 估 500+ 行
- 27 个 unused 订阅 i18n key(× 4 语 = 108 处)· 含 upgrade-plan-tag-* / settings-sub-* / admin-type-byo / err.ocr.plan_not_supported 等
- PLAN_CONFIG / LEGACY_PLAN_MAP / _get_plan / get_plan_features(auth_signup.py 常量 + helper · 仍被 /api/me/plan 用户端调用 · 一起清需要同时改 home.js 多处)
- 都是死代码 · 但 home.js 33k 行结构敏感 · 这次会话不安全做 · 留 REFACTOR-C1 阶段拆 home.js 时一并

### 重大决策(本会话续 · 2026-05-22)
- **删除不是隐藏**(Zihao 拍板 · 跟历史决策一致):4 后端路由整段 git rm · admin SPA UI 整段 git rm · 不留 deprecated 注释 · git log 是历史
- **DB schema 字段保留**:users.plan / monthly_quota / trial_expires_at / plan_expires_at / upgraded_at / subscription_log 表 / payment_pending 表都不删 · 留 REFACTOR-B3 Alembic 时按"删字段先 Optional + default · 一个迭代后再真删"流程做(铁律 #15)
- **/api/me/plan 路由留**:home.js 4 处调用 · 强删会炸 · 留 C1
- **不动 home.js 死代码大块**:风险大 · 留 C1 拆时一并

### 下窗口接力(给下个 Claude 窗口看)
- **当前 task**:REFACTOR-A7 依赖锁定(1-2h · pip-tools 生成 requirements.lock.txt + CI 改用 lock)
- **备选**:A5 CI lint(半天 · 风险中 · 涉及自动 reformat 现有 .py)/ A3 环境分级(1-2 天 · 重)
- **A2.2 git-deploy.sh 钩子注意事项**(等 B3 真要做时):
  1. ssh 上服务器 cat /opt/mrpilot/git-deploy.sh 看现状(已知 L688 只 pip install playwright · 不重 pip install -r)
  2. 加 `pip install -r requirements.txt` 在 git pull 后(让 alembic 进 prod venv)
  3. 加 `alembic upgrade head` 在 systemctl restart 前
  4. 加失败回滚(alembic downgrade -1)
  5. test 在 staging 跑通后再上 prod

---

## 🆕 2026-05-22 第三会话 · 阶段 7-8 推进 + 整顿期立项 · 6 个 task

> **接力规则**:换窗口先看本段

### 6 个 commit 全绿

| Commit | Task | 内容 | home.js Δ |
|---|---|---|---|
| `558a326` | 原 7.1 → REFACTOR-C1 部分 | dashboard 抽出 `static/home/dashboard.js`(196 行) | −197 |
| `0bd1f1b` | 原 7.2 → REFACTOR-C1 部分 | billing 抽出 `static/home/billing.js`(320 行) | −320 |
| `ae3e846` | 原 7.3 batch 1 → REFACTOR-I1 部分 | 15 个 `catch (_) {}` 加 silent 注释 | +6 注释 |
| `7c163ca` | 原 7.3 batch 2 → REFACTOR-I1 部分 | 12 silent 注释 + 3 console.warn | +12 注释 +3 warn |
| `0ba0acf` | 原 8.1 → REFACTOR-G1 前置 | docs/README 索引 40 文件 | 0 |
| **本次** | **REFACTOR-A0** | **整顿主计划落档**(REFACTOR_MASTER_PLAN + 铁律 18-20 + 统计脚本) | 0 |

### 累计成果(本会话第三轮 · 整顿期立项前)
- home.js **33768 → 33251 行**(减 517 行)
- 静默吞错处理 **30/52**(已注释)
- docs/ 全索引(40 markdown)
- 5 道守门全绿(每个 commit)
- 4 个 cache_bust 进位 + 4 语 release_notes 4 版

### 整顿期立项产出(本次 REFACTOR-A0)
- ✅ `CLAUDE.md/REFACTOR_MASTER_PLAN.md`(60+ task · 9 阶段 A-I · 单一权威源)
- ✅ 铁律 #18(封锁新功能)+ #19(必读 4 文档)+ #20(commit 必含 task ID)
- ✅ STATE_PEARNLY 头部加"整顿模式 ON"
- ✅ `scripts/refactor_progress.py`(自动统计 · 防偷懒)

### 下窗口接力 = REFACTOR-A1 Vite 落地

子拆分:
- A1.1 · 装 Vite + 配 esbuild(半天 · 1 窗口)
- A1.2 · CI 加 build step(1h · 同 1 窗口)
- A1.3 · dashboard.js / billing.js 改 ES modules(半天 · 1 窗口)
- A1.4 · 验证 prod 全跑通(半天 · 1 窗口)

---

## 历史 STATE(整顿模式立项前 · 仅供参考)

---

## 🆕 2026-05-22 本会话(第二轮)完成清单 · EXECUTION_PLAN 阶段 4-6 收官

> **接力规则**:换窗口先看本段

### 核心产出

**7 个 EXECUTION_PLAN 阶段任务**连续推进 · 全部 ✅:

| Task | 内容 | 工时(实际/估) |
|---|---|---|
| 4.2 Playwright smoke | 新建 `tests/e2e/` + CI 加 e2e step + 4 件事守门(prod 着陆页加载 / 顶栏 / 4 语切换 / 无 console error) | 45min / 2h |
| 5.1 抽 billing router | 11 路由从 app.py → `billing_routes.py`(673 行)· `/api/me/credits` + 切公司 + 充值 + admin topup 等 | 100min / 2-3h |
| 5.3 立铁律 #17 | CLAUDE.md 加铁律"新功能禁止塞巨石" + 新建 `CONTRIBUTING.md` | 25min / 30min |
| 5.2 抽 admin diagnostics | 5 路由(diagnostics + internal/deploy + install-playwright) → `admin_diagnostics_routes.py`(303 行)· 新抽 `_require_internal_token` 统一 secret 校验 | 75min / 2h |
| 6.1 ensure_* 盘点 | 25 个 ensure_* 函数全清单 → `docs/architecture/db-ensure-inventory.md`(178 行) | 55min / 1-2h |
| 6.2 Alembic 设计 | 完整 Alembic 迁移方案 → `docs/architecture/db-migration-plan.md`(338 行 · 5 决策点全答) | 60min / 2h |

### 量化收益

- **app.py 10060 → 9211 行**(减 **850 行 · 8.4%**)
- 2 个独立 router 模块(`billing_routes.py` 673 + `admin_diagnostics_routes.py` 303 = 976 行)
- 第一个 E2E 测试(prod 着陆页 4 件事 · CI 4 step 全绿 · 4.4s 本机 / 4s CI)
- 铁律 #17 + `CONTRIBUTING.md`(防屎山扩张)
- 2 份架构文档(db-ensure-inventory + db-migration-plan)给 Task 6.3 落地打底
- 11 个 commit · 全部走 C 档位 push · 全部 CI 验过(`46ca511` / `7778afb` / `fa5e0ea` / `767ade9` / `e676c01` / `8ca78f9` / `876649d` / `8c360d2` / `3ab1684` / `96c38c2` + 本次收尾 commit)

### 几个踩坑教训(下窗口要避开)

1. **PowerShell `WriteAllText` 默认加 UTF-8 BOM**(Task 5.1 踩):转 CRLF 时用 `[System.IO.File]::WriteAllText` 默认 UTF-8 encoder 加了 BOM(U+FEFF) · cpython 容忍但 `ast.parse` 不容忍 → CI #12 红
   - **教训**:转 CRLF 用 `New-Object System.Text.UTF8Encoding $false` 明确 no-BOM · 或用 Python `ReadAllBytes` 字节级处理(Task 5.2 改用此法 · 0 BOM 问题)
2. **`concurrency: cancel-in-progress` 工作正常**:快速连推 2 个 commit 时前一个 run 被 cancel · **不是 bug** 是预期行为 · 别误以为 CI 失败
3. **私库无 gh CLI 拉 CI 状态**:用 `git credential fill` 拿 GitHub PAT + `Invoke-RestMethod` 调 GitHub Actions API(`/actions/runs?per_page=N`)· 跨平台稳
4. **lazy import 解循环 import**:`admin_diagnostics_routes` 顶层不 import app · handler 内部 `import app as _app`(运行时 app 已 init) · 解 `_last_500_event` mutable global 共享 · 干净
5. **改 webhook 自身代码风险**:Task 5.2 改了 `/internal/deploy` handler 路由位置 · 但 URL 不变 · 旧 webhook 接到 push 触发部署 · 服务器拉新代码 · 新 handler 接管 · 风险为 0(实测 webhook 自我 hot-swap 成功)
6. **生产部署 ≠ CI** :本会话 4 个 push 都触发了 webhook 自动部署(改了 .py 就部署) · 改 docs/ 不部署。`fa5e0ea` push 时服务器 502 ~20 秒(systemctl restart 中) · 然后恢复;`876649d` 同样 ~25 秒恢复 · 都正常

### EXECUTION_PLAN 进度看板(本会话末)

| 阶段 | 完成度 | 备注 |
|---|---|---|
| 0 安全基线 | ✅ 5+1/5 | 2026-05-21 早期 |
| 1 多租户保险 | ✅ 2/2 | 54 contract tests |
| 2 计费保险 | ✅ 1/1 | 43 contract tests |
| 3 CI 保险 | ✅ 2/2 | 4 step CI · 本机 + CI 双绿 |
| **4 i18n + E2E** | ✅ **2/2** | Task 4.2 本会话补完 · 第一个 E2E |
| **5 后端路由拆** | ✅ **3/3** | 本会话全做完 · app.py 减 850 行 |
| **6 DB 迁移规范** | ✅ **2/2** | 本会话全做完 · 等 Task 6.3 落地 |
| 7 前端拆分 | ⚪ 0/3 | 下一接力点 |
| 8 治理收尾 | ⚪ 0/2 | |

### 下窗口接力候选(等用户拍板)

1. 🥇 **阶段 7 Task 7.1 抽 home.js dashboard 模块**(3-4h · 第一次拆前端 · 用 Playwright 做安全网)
2. 🥈 **Task 6.3 实际落地 Alembic**(2.5h · `db-migration-plan.md` 已经设计完 · 装包 + env.py + 001/002 迁移 + staging 闭环测试)
3. 🥉 **回 P0-VAT v4.9.6 主线**(4.1 天 · STATE 主线 · 6 bug + UI 美化 + 真实 PDF 504 fix)
4. **跳到阶段 8** Task 8.1 文档导航整理(1h · 给 80+ docs 建 README 索引 · 文档级零代码)

### F-01 服务器装包同步(2026-05-22 第一会话起 · 仍未做)

**未做** · 仍是下窗口待办。`requirements.txt` 已加 `python-docx` + `reportlab` + `python-multipart` · 但服务器没自动 `pip install`:
```
ssh root@45.76.53.194 "cd /opt/mrpilot && source venv/bin/activate && pip install python-docx reportlab python-multipart && systemctl restart mrpilot"
```
**优先级 P2 · 30 秒**

---

## 🆕 2026-05-22 本会话(第一轮)完成清单(CI 收官 · 本机 OOM 链路深挖)

> **接力规则**:换窗口先看本段

### 核心产出

**主线任务**:阶段 3 Task 3.2 GitHub Actions 最小 CI 三 step(import + i18n + unit tests)从 1.7/2 推进到 **2/2 完成**(等 CI run #6 commit `cadb4b2` 出最终绿)

### 4 个 commit · 修了 6 层依赖洋葱

| Commit | 改 | 修了什么 |
|---|---|---|
| `d1912aa` | app.py + tests/unit/test_erp_test_connection_route_dispatch.py | 真 OOM 元凶(`_erp_retry_loop` 加 `PEARNLY_SKIP_HEAVY_INIT` env gate)+ KMS_KEY setUpClass 加临时 Fernet key + Python 3.10 event-loop 污染 workaround + chromium binary 缺转 skipTest |
| `10df685` | CLAUDE.md/EXECUTION_PLAN.md | 阶段 3 Task 3.2 完成入档 + 本机 OOM 链路 4 修总结 |
| `bc6688c` | requirements.txt | 加 `python-multipart`(recon_routes.py `/upload_report` Form 字段触发 FastAPI 检查 · CI 干净 venv 撞 import 挂) |
| `cadb4b2` | tests/unit/test_erp_test_connection_route_dispatch.py | `PushMRERPAsyncContextTests` 改 sync `TestCase` + `asyncio.run()` · 修 Python 3.11 `_tearDownAsyncioRunner` 撞 `_check_running`(我之前的 `_setupAsyncioLoop` override 是 3.10 hook · CI 用 3.11.15 完全不被调用) |

### 真 OOM 元凶(本会话起因)

用户在跑 CI 同款 `python -m unittest discover -s tests/unit` 时,Claude Code 被 OOM-kill 多次,内存任务管理器显示 PowerShell ~3.8GB + Python ~3.8GB · 系统 94%:

- 测试用 `with TestClient(app) as c:` 进 lifespan · 同时全局 `patch("asyncio.sleep")` 短路 30s 间隔
- → `_erp_retry_loop` 从 30s 一次变成 CPU 死循环
- → `list_logs_due_for_retry` 每秒被调约 **2 万次** raise(`DATABASE_URL` 未设)
- → stderr 缓冲 21 分钟攒 **1.6 GB / 840 万行**日志
- → OS OOM-kill 整个 shell + Claude Code

修法:lifespan 看 `PEARNLY_SKIP_HEAVY_INIT=1` 就不 create_task(测试 setUpClass 早就 setdefault 这个 env · 但 app.py 之前根本没读它 · 死字段)。

### 收获的经验值(下窗口接力时要记得)

1. **本机绿 ≠ CI 绿**:本机 venv 装了一堆传递依赖把问题盖住 · CI 干净 venv 一层层剥洋葱。新加 import 必须显式 `pip install <pkg>` 后再 `pip freeze | grep` 同步到 requirements.txt
2. **跨 Python 版本 hook 差异**:本机 Python 3.10 · CI Python 3.11.15 · `IsolatedAsyncioTestCase` 内部 hook 完全不同。能用普通 `TestCase` + `asyncio.run()` 就别继承 `IsolatedAsyncioTestCase`
3. **stderr 缓冲会 OOM**:测试别 tee 完整输出到管道 · 写文件或 `--tb=short` · 21 分钟 1.6GB 日志就是 PowerShell 缓冲爆的
4. **task 不退干净会污染下个 case**:starlette TestClient `with` 块退出时 portal loop 在某些 OS/版本组合下不清 `asyncio.events._running_loop` 标志

### 待下窗口

接力点(EXECUTION_PLAN.md 已更新):
- 阶段 4 Task 4.2:第一个 Playwright smoke 测试(2h)
- 或 阶段 5 Task 5.1:抽 billing router(2-3h)

如 CI run #6 `cadb4b2` 仍红 · 看 log 头部判断是新一层洋葱还是同问题没修透。

### 顺便发现的硬件问题(non-prod)

用户笔记本(联想小新 Air 14 ITL 2021 · 16GB 双通道 · MT 82FF)实测 8GB 跑 Claude Code + 浏览器 + Python 测试常 OOM · 已建议买 2 条 DDR4-3200 16GB SO-DIMM 替换原有 2×4GB · 32GB 双通道彻底解决。用户 2026-05-22 14:00 左右带电脑去线下修电脑/加内存。

---

## 🆕 2026-05-16(深夜) 本窗口完成清单(v118.32.5.5.30 · UI精修)

> **接力规则**:换窗口先看本段

### 对账 UI 视觉精修(home.html / home.css / home.js · cache bust 11841123)

| 项 | 修法 |
|---|---|
| GL 折叠头背景 | `#f4f4f0` → `#ffffff` · hover `#ebebea`→`#F9FAFB` |
| VAT 折叠头背景 | `#fafaf8` → `#ffffff` · hover `#f4f4f0`→`#F9FAFB` |
| 搜索框背景 | `var(--bg)` → `#ffffff` |
| GL "导出 Excel" | 差异明细头部 → **对账汇总头部** |
| VAT 下载按钮 | 独立蓝色 bar → **对账汇总头部** ghost 风 · 文案同步 |
| VAT 折叠防误触 | click代理加 button/a 判断 · 按钮不触发折叠 |
| 去除 vex-dl-bar | 已删除 · 无 DOM 残留 |

### 待下窗口
- 🔴 **Excel 差异明细 Sheet 表头美化**(ws1 · `gl_vat_reconciler.py`) ← 下窗口第一优先
- 🟡 验证 Excel 对账汇总格式(ws2 · WHITE_FILL/SECT_FONT 已部署 · 待用户重跑验证)

---

## 🆕 2026-05-16(深深夜) 本窗口完成清单(接 v5.5.28 · 多项修复)

> **接力规则**:换窗口先看本段 · 老段保留在下面

### 🔴 P0 Bug 修复 · 客户 Korn 对账数据错误(已验证数字正确)

| 文件 | Bug | 修法 |
|---|---|---|
| `vat_report_parser.py` | `_to_float()` 遇到 `(500.00)` 括号负数抛异常 → 整行 VAT 记录被跳过 | 加括号负数解析:`(500.00)` → `-500.0` |
| `gl_vat_reconciler.py` | GL 2列格式 + 无期初余额时 · ลดหนี้/รับคืน(退货)行被默认归 Credit · 导致 GL 合计多算 2000 | 加 `_DEBIT_LINE_KW` frozenset + `_is_debit_line()` · 关键词优先判断 → 退货 = Debit |

**Korn 验证结果**:`ตัวเลขแสดงถูกหมดแล้ว` ✅ (数字全部正确)

### UI 修复(home.js + home.html + home.css)

| 项 | 修法 |
|---|---|
| GL `#1A3C5E` 深蓝色残留 5 处 | 全替换为 `var(--ink)` / `var(--bg)` / `var(--line)` |
| GL 对账结果区在卡片外 | `glv-result` 移入 `vex-main-action` 内(同 VAT 面板结构) |
| GL 对账跑完后汇总/明细不自动展开 | 加 `_expandResults()` helper · 在 `_run()` 和 `_loadTask()` 结束时调用 |
| VAT 对账汇总行显示 UUID hash | 删 `subEl.textContent = '#' + last.task_id` |
| 差异明细行数徽章右对齐跑偏 | `.recon-collapse-sub` 改为 pill badge 样式(同 `glv-section-count`) |
| 历史表下载按钮 tooltip 显示"操作" | 改为 `t('hist_export')` → 显示"导出" |
| GL 折叠头 hover 显示蓝色 `#F1F5F9` | 改为 `#ebebea` |

### CSS 视觉层次(参考上传识别页面)

| 元素 | 之前 | 之后 |
|---|---|---|
| `vex-main-action`（主操作卡片）| `#f4f4f0`（同页面）| `#ffffff`（白卡片）|
| `vex-drop`（上传格子）| `#f4f4f0` | `#f8f8f6`（凹陷感）|
| `vex-kpi-card`（KPI 卡片）| `#F9FAFB` | `#ffffff` |
| `vex-task-section`（VAT 历史区）| 无背景 | 白卡片 + 圆角边框 |
| `.glv-history`（GL 历史区）| 无背景 | 白卡片 + 圆角边框 |

### Excel 汇总 Sheet 格式(gl_vat_reconciler.py · ws2)

| 项 | 修法 |
|---|---|
| 分区标题行有黄色底色 | 加 `WHITE_FILL = PatternFill("solid", fgColor="FFFFFF")` 显式覆盖 |
| 分区标题行显示小计金额(与明细行重复) | `b_val = "" if not emphasize else amount` · 标题行 B 列留空 |
| 分区标题行字体与明细行相同 | 加 `SECT_FONT = Font(bold=True, size=10)` 粗体 |

⚠️ **注意**:Excel格式修复刚刚部署 · 用户在本窗口测试时用的是旧版(有问题)。下窗口需先验证。

---

## 🆕 2026-05-16(深夜) 本窗口完成清单(v118.32.5.5.26 → v118.32.5.5.28 · 共 3 个微版本)

> **接力规则**:换窗口先看本段 · 老段保留在下面

### VAT 预览面板数据接通 + UI 清理

| 版本 | 内容 |
|---|---|
| **v118.32.5.5.26** | **P0 完成**:销项税对账跑完后自动拉 `/api/vat_excel/tasks/{id}` JSON · 填充 `vex-summary-collapse`(5 KPI:总量/匹配/差异/现金/差异金额) + `vex-detail-collapse`(全量差异行 · 可滚动 · 无截断); `_fetchAndFillVexPreview` 异步函数 · 跨 IIFE 靠 `window._fillVexSummary/Detail` 全局桥; `app.py` release_notes 4 语更新 |
| **v118.32.5.5.27** | **屎山清理**:砍掉"对账完成"绿色完成横幅(`vex-result` div + MutationObserver `_watchVexResult` + 4 语 i18n key + CSS `.vex-result`); 下载按钮移至极简 `vex-dl-bar`(仅一个下载按钮 · display flex); cache bust 11841111→11841112 |
| **v118.32.5.5.28** | **UI 蓝色/颜色/顺序三项修正**:`.vex-pp-guide` `#DBEAFE`→`var(--line-soft)` 蓝底清除; 预览面板边框 `#E5E7EB`→`var(--line)` 统一暖灰; `.vex-action-info.ok` 颜色→`var(--success)` 绿; GL 对账面板"对账汇总"与"差异明细"互换顺序(汇总在前); cache bust 11841112→11841113 |

### 待下窗口继续
- 🟡 GL 收入对账预览面板数据填充(同 VAT 套路 · 接 `/api/recon/gl-vat/tasks/{id}` JSON · 当前骨架空)
- 🟡 GL 对账 i18n 完整性 lint(`scripts/check_i18n.py`)

---

## 🆕 2026-05-16(晚) 本窗口完成清单(v118.32.5.5.16 → v118.32.5.5.25 · 共 10 个微版本)

> **接力规则**:换窗口先看本段 · 老段保留在下面

### NAV-IA Gap 补全 + 新铁律 + 基础设施加固

| 版本 | 内容 |
|---|---|
| **v118.32.5.5.16** | **视觉大清扫**:7 处硬编码蓝色(`.rh-stat-dot` / `.client-card` / `.billing-card` / spinner / `.ob-deco` / `.sv-batch-count strong` / `.glv-history-actions`)→ `var(--accent)` / 纯黑 / 暖灰; **首页 dashboard**:4 KPI 卡 + 快速操作 + 最近动态(复用 `/api/me/plan` + `/api/ocr/history`) |
| **v118.32.5.5.17** | **版本更新弹窗**:新文件 `static/version-banner.js`(独立 IIFE · 30s 轮询 `/api/version` · 顶部条 + modal + 4 语 + 30min snooze); `/api/version` 加 `release_notes` 4 语字段; CLAUDE.md 铁律 #6:每次部署写 4 语 release_notes |
| **v118.32.5.5.18** | **部署 graceful 三层**:systemd `TimeoutStopSec=35` + `KillSignal=SIGTERM`; uvicorn `--timeout-graceful-shutdown 30`; lifespan 加 `_recover_interrupted_tasks()`(扫 `status=running` 老任务 → 标 `interrupted`) |
| **v118.32.5.5.19** | **对账对称化**:销项税核查加 `vex-summary-collapse`(4 KPI 卡) + `vex-detail-collapse`(逐条差异表); 收入对账加 `glv-preview-panel`(vex-pp-grid 两栏 · 文件名/大小/路径) |
| **v118.32.5.5.20** | **批量删**:后端 `recon_routes.py` 加 `/api/recon/gl-vat/tasks/batch_delete` · `db.py` 加 `delete_gl_vat_tasks_batch()`; 前端两个对账历史表加 checkbox 列 + 顶部批量删按钮 |
| **v118.32.5.5.21** | **弹窗文案 + reload bug 修**:点"立即更新"前先写 `LS_LAST_SEEN = 最新版本`，防 reload 后弹窗复现; banner 文案 4 语标准化 |
| **v118.32.5.5.22** | **Gmail thead 切换栏**:选中行后 thead 切换成 batch 模式行(内联 · 不另建 div);修表头列宽错位(nth-child → nth-last-child · 操作列固定 110px) |
| **v118.32.5.5.23** | 收入对账查看清单 UI 骨架:改为 `vex-pp-grid` 两栏 + 上方两上传区域对齐 |
| **v118.32.5.5.24** | **屎山清理**:删老 `pn-version-banner` IIFE(116 行 JS + 86 行 CSS); `vex-pp-grid` 从 `1.5fr 1fr` → `1fr 1fr; gap:60px` 对齐上方上传区 |
| **v118.32.5.5.25** | **查看清单 1:1 复刻**:`_renderGlvPreviewPanel()` 完整实现(搜索框 / 清除全部 / 文件行 × X 删除按钮 / 分页); `_removeFile()` 直接写 `STATE.vatFile/glFile=null` 绕过 `setFile(null)` 早返回; `_reset()` 同步调 panel 刷新 |

### 本窗口新铁律
6. **每次部署写 4 语 release_notes**(v5.5.17 拍板):大白话 · 不含 OCR/Gemini/API/batch 等技术词 · 会计师能看懂"我能用上啥"

### 待下窗口继续(本段已由 v5.5.26-28 解决)
- ✅ ~~销项税核查预览数据填充~~ — v5.5.26 已完成
- ✅ ~~UI 蓝色残留~~ — v5.5.28 已清理

---

## 🆕 2026-05-16 本窗口完成清单(v118.44.1.0 → v118.32.5.5.15 · 共 17 个微版本)

> **接力规则**:换窗口先看本段 · 老 GL 主线段保留在下面

### Admin SPA 用户管理补全(NAV-IA Phase 8 收尾)
| 版本 | 内容 |
|---|---|
| **v118.44.1.0** | 用户详情抽屉(7 section)+ 3 tab(客户/员工/日志)切换 + 升级 modal · 移植自 home.js L20600-L22400(1800 行) |
| **v118.44.1.1** | 封停 / 解封 / 级联删除(双重确认)+ 风控完整版(展开 / 分页 / 详情 modal / 批量封禁) |

**改动**:`static/admin/admin.html` + `admin.js`(+1200 行) + `admin-i18n.js`(zh+th 49→130 key)· admin SPA 0 home.js 依赖 · 后端 13+ API 全在不动。

### GL 收入对账 + 销项税核查多 ERP 兼容
| 版本 | 内容 |
|---|---|
| **v118.32.5.5** | WNF/Express/Mr.ERP 风格 GL PDF 解析(`gl_vat_reconciler._parse_gl_text_lines`):兼容 2/3 列数字 + 无日期延续行 + 余额变化判借贷 |
| **v118.32.5.5.1** | 科目 regex `_ACCT_RE` 放宽 4-5 位→4-7 位(支持 WNF 6 位科目 411000) |
| **v118.32.5.5.2** | filename 500 修(泰文文件名走 RFC 5987 utf-8) + VAT 页眉过滤(`_filter_garbage_rows`) + 4 处 alert→showToast |
| **v118.32.5.5.3** | VAT 过滤加严:doc_no 单 token + ≤30 字符 + 不含表头关键词 |
| **v118.32.5.5.4** | VAT pdf_text 过滤后 < 3 行先试 `_parse_vat_pdf_text_lines` 文字行 regex · 不立即回退 Gemini(省 40 秒) |
| **v118.32.5.5.5** | invoice_no 切粘连尾(`_GLUED_TAIL_RE`):DXOHC25-006**OHANAHAN** → DXOHC25-006 + ref_no 严格化(必须含数字) |
| **v118.32.5.5.6** | z-index 单点修(`.cpw-forgot-overlay` 1000→10000) |
| **v118.32.5.5.7** | **z-index 批量修 13 处**(用户反馈"修一类不修一处")· `.add-emp-overlay/.modal-mask/.modal-overlay/.admin-modal-backdrop/.cmdk-mask` 等全升 10000 |
| **v118.32.5.5.8** | BAKELAB pypdf 抽泰文字符顺序乱 · 税号检测改任意 13 位 fallback(`_extract_seller` + `_extract_buyer`) |
| **v118.32.5.5.9** | `extract_invoice_fields` 加 text_path 快路径(销项税核查 BAKELAB 5 张 24s→11s) · `try_text_extraction(strict=False)` |
| **v118.32.5.5.10** | **Session 1 账号 1 设备**:JWT 加 jti · users 加 `active_jti` · 登录写入 · 校验不等就 401 `auth.session_revoked` |
| **v118.32.5.5.11** | `gl_vat_reconciler` summary 加 4 类调整项明细 list + Sheet 2 缩进展开单据明细(Korn 反馈) |
| **v118.32.5.5.12** | 修 migrate bug · `_ensure_user_profile_columns` 加 `commit=True`(ALTER TABLE 之前未提交导致 active_jti 列没建上) |
| **v118.32.5.5.13** | Session 心跳:15 秒轮询 `/api/me/plan` + window focus / visibilitychange 立即 check · 实时踢人 |
| **v118.32.5.5.14** | Trial 缩水:100 张/月 7 天 → **30 张/月 3 天**(Korn 反薅闸 🅱) |
| **v118.32.5.5.15** | login.html 着陆页 4 真公司名换假名:SINCERE/GreenLeaf/PT Solutions/Café Mae → 咖啡店/面包房/IT 公司/餐厅(4 语 i18n + DOM) |

### 本窗口产生的新铁律(已记 memory · 见 CLAUDE.md)
1. **修一类不修一处** · 修 bug 前 grep 同类 pattern 一次性全修(2026-05-16 v118.32.5.5.7 拍板)
2. **ALTER TABLE 必须 `commit=True`** · `db.get_cursor()` 默认不 commit · DDL 会在 with 块退出时回滚(v118.32.5.5.12 踩坑)
3. **Session 控制走 active_jti 模式** · JWT 加 `jti` claim · 每次登录写 users.active_jti · token.jti != active_jti → 401 `auth.session_revoked`
4. **PLG 反薅闸 5 道**(2026-05-16):trial 30/3 + 1 设备 + 24h 同 IP 3 邮箱 + 24h 同 /24 网段 10 邮箱 + 员工共享老板额度
5. **着陆页禁止真公司名** · 用行业类目假名(咖啡店 / 面包房 / IT 公司 / 餐厅)避免商号冒用风险

### 待用户(Zihao)测试确认
- session 实时踢人(v5.5.13 加心跳后)— 3 设备登录测 · 看 15 秒内被踢
- admin SPA 抽屉 / 3 tab / 4 modal / 风控批量封禁
- z-index 13 处批量修(除"添加员工"已确认)

### 待 Korn 回复
- 「5 人轮流用 1 账号」想堵法:🅰 设备指纹累计 / 🅱 IP 段限流 / 🅲 价格策略 / 不堵(SaaS 通病)
- 多 ERP 真实样本(Express / Mr.ERP / FlowAccount)收集中
- 着陆页假名风格确认

### STATE 老遗留(本窗口未碰 · 下窗口可选)
- 🔴 P0-VAT 6 张文件 10 分钟卡 · `parse_vat_report` 同步阻塞 async · `run_in_executor` 修(0.5 天)
- 🟡 真实国税局 PDF 504 timeout(BAKELAB 33 行)· timeout 60 + 重试 + pdfplumber 优先(0.5 天)
- 🟢 进项管理 UI 壳子 v118.45.0 / Phase 6 v118.40 MVP(3 周)

---

## 🆕 GL 对账主线(2026-05-15 晚 上线 · 客户拍板)

> **核心**:新功能"收入对账"(总账 GL vs 销项税报告) · 与现有"销项税报告核查"(发票 vs VAT 报告)互补
> **触发**:客户桌面"新需求"文件夹 · 新需求.md + Thai/中双语规则 · 2026-05-15 PM 立项 → 同日晚上线

| 子模块 | 状态 |
|---|---|
| `gl_vat_reconciler.py` 核心引擎(pdfplumber + 文字行 regex + 对账 + 4 语 Excel 导出) | ✅ v118.32.5.0 |
| `recon_routes.py` 4 个 API 路由(run/tasks/{id}/{id}/export) | ✅ |
| `db.py` `gl_vat_task` 表 + 5 个 CRUD | ✅ |
| 前端:对账中心新加"收入对账" Tab + 折叠区 + 历史表 + i18n × 4 语 | ✅ |
| **销项税性能修复** · `classify_file(fast_mode_invoice=True)` 跳冗余 Gemini classify(节省 25-30s/10 张) | ✅ v118.32.5.3 |
| Excel 导出升级:5 KPI 顶行 + 状态列 + 4 语使用说明 Sheet(借鉴 vat_recon 模板) | ✅ v118.32.5.4 |
| 客户拍板重命名:`销项税对账→销项税报告核查`(zh) / `GL对账→收入对账`(zh) / Thai 4 语同步 | ✅ |

**性能基线**:GL 对账(2 文字 PDF · 252 行)~2 秒;销项税核查(5 张发票 + 1 VAT)~40 秒(原 3 分钟)。

**已知细节**:
- 匹配键 VAT.`เลขที่เอกสารอ้างอิง` ↔ GL.`ใบสำคัญ`(不是 invoice_no)
- 正数 → GL Credit · 负数 → GL Debit 转负
- 收入科目默认 4xxx 开头(UI 可改前缀)
- 生产服 venv 新装 `pdfplumber 0.11.9`

详见 `HANDOVER_TO_NEXT_WINDOW.md`(2026-05-15 晚版本)。

---

## 🧭 NAV-IA 平行主线(2026-05-15 收官 · 8 Phase 全部完成)

> **PRD 主文件**:`NAV_IA_PRD.md`(IA 重构唯一 spec)
> **Phase 6 子 PRD**:`MODULE_EXPENSE_PRD_v2.md`(进项管理模块 · 对标 Paypers · 3 周)
> **基准实物**:`D:\Users\Skin\Desktop\pearnly_project\pearnly_nav_prototype_final.html`(切视角看效果)
> **CLAUDE.md 铁律段**:已加「🧭 导航 IA 铁律」节
> **触发**:2026-05-13 Zihao 提"产品凌乱不堪 · 找不到头" → 2026-05-15 拍板

### 当前状态: **NAV-IA 主线收官 · Phase 1-8 全部 ✅ · 等 Zihao 拍板下一主线**

| Phase | 内容 | 工时 | 状态 |
|---|---|---|---|
| 0 | 文档体系建立 | 0.5 d | ✅ **2026-05-15** |
| 1 | **顶栏三件套**:头像菜单 + 搜索框 + Cmd+K 命令面板 | 1.5 d | ✅ **2026-05-15** · v118.33.1.0 |
| 2 | sidebar 重复入口清扫 | 0.5 d | ✅ **2026-05-15** · v118.33.2.0 |
| 3 | sidebar 集成一级入口 + 后撤销 CTA(prototype 没有) | 0.5 d | ✅ **2026-05-15** · v118.33.3.0 |
| 4 | "即将" badge 大清扫(5 个) | 0.5 d | ✅ **2026-05-15** · v118.33.4.0 |
| 5 | sidebar 业务流分组(销项▾/进项▾) | 1 d | ✅ **2026-05-15** · v118.33.5.0 |
| 6 | 进项管理完整模块(新功能) | 3-5 d | 🚫 **永久跳过** · 等独立开 v118.40 MVP · 子 PRD:`MODULE_EXPENSE_PRD_v2.md` |
| 7 | **集成模块独立化** | 1 d | ✅ **2026-05-15** · v118.33.7.0 |
| **视觉皮肤对齐** | 11 轮微迭代 · 蓝→黑 / 浅蓝→暖灰 / 顶栏 48 / 字号 13 / 一刀切替换 50+ 处浅蓝硬编码 | ~1 d 累计 | ✅ **2026-05-15** · v118.33.7.1 → v7.11 |
| 8 | **Admin Layout 独立**(Earn 专属 · 仅 2 项 sub-nav · admin SPA 不引 home.js) | 1 d + 6 hotfix | ✅ **2026-05-15** · v118.44.0 → v118.44.0.7(8 个微版本) |

### 🆕 Phase 8 实施详情(本窗口 2026-05-15 · 8 个微版本)

| 版本 | 干啥 |
|---|---|
| v118.44.0 | 首部署 · 新建 admin.html/css/js 三件套 + app.py 加 `/admin/{rest:path}` 路由 + login.html 超管跳 /admin/cost |
| v118.44.0.1 | 老 `/admin` 改 301 重定向到 `/admin/cost`(解决浏览器 cache 卡老 home.html) |
| v118.44.0.2 | 修文字隐形(home.js applyLang 抛错残留 `.lang-switching` class)+ admin.js 持续轮询业务函数 |
| v118.44.0.3 | login.html 超管直跳 `/admin/cost` 跳过 `/home` 中转 · `/` `/login` no-cache · 卡顿 3s → 1s |
| v118.44.0.4 | 删「返回普通视图」按钮(死循环) + 修语言下拉关闭 bug |
| v118.44.0.5 | home.js L13585 顶层 try-catch + admin.js 自己 fetch admin 业务 API |
| v118.44.0.6 | 诊断面板改累积日志 |
| **v118.44.0.7** | **彻底独立救援版** · admin.html 拔掉 home.js + 新建 `admin-i18n.js`(zh+th 49 key)+ 5 个按钮 listener + 修 Google 余额 endpoint(`/api/admin/billing/balance`)+ 删诊断 chip |

### 🎯 Phase 8 文件清单(给下窗口接力用)

**新建 4 个文件 · admin SPA 完全独立**:
- `static/admin/admin.html` (~20 KB · sidebar 2 项 + topbar + page-admin-cost + page-admin-users DOM)
- `static/admin/admin.css` (~9 KB · 复用 home.css token + admin 专属变体)
- `static/admin/admin.js` (~23 KB · 鉴权 + 路由 + UI + 业务 fetch 全自包含)
- `static/admin/admin-i18n.js` (~7 KB · zh + th 49 key · 不写 en/ja 按铁律)

**改 home.js 关键位置**:
- L9851 admin-layout 早退分支(已废 · 因为 admin.html 不再引 home.js)
- L9890 `_isAdminPath` 加 `startsWith('/admin/')`
- L11598 `renderFileList` 加 `if (!list) return` 防御
- L13585 + L13590 顶层 `applyLang/routeTo` 包 try-catch
- L29911 / L30029 跳 `/admin/cost`
- 4 个语言块加 6 个 `adm-*` key(zh/en/th/ja 全)

**改 app.py 2 个 route**:
- 老 `/admin` 改 301 重定向到 `/admin/cost`
- 新加 `/admin/{rest:path}` 服务 admin.html
- `/` `/login` 加 no-cache headers

**改 login.html**:超管登录跳 `/admin/cost`(已登录用户重访同上)

### 🚨 Phase 8 关键经验教训(给下窗口看)

1. **home.js 30k 行屎山 + 248 处 `.classList.`**:在缺 DOM 上下文下任何一个 null 就抛错 · setInterval/subscribeI18n 持续触发让浏览器交互失效。**任何新独立模块不要再 `<script src="/static/home.js">`** · 重做的 admin SPA 拔掉它后立刻清净。
2. **i18n 区域分级铁律生效**:admin-i18n.js 只内嵌 zh + th 49 key(adm-* 内部页豁免 en/ja)
3. **app.py 后端 API 零改动**(只加静态 route)· 严格遵守"不改后端 API"铁律 ✓
4. **优化选项 2(拆 home.js)立项 TECH_DEBT.md P1** · 渐进翻新 4 阶段路线 · 不闭眼开干 · 等专门窗口

### 4 类账号矩阵(铁律 · 详见 NAV_IA_PRD §2)
- **员工** = 看不到付费 / 测试 / 管理员
- **老板** = 看付费 · 看不到测试 / 管理员
- **skin** = 老板 + 测试中心
- **Earn** = **走独立 /admin/cost layout** · 不进 home.html · sub-nav 仅 2 项

### Earn 铁律精确化(2026-05-15 Zihao 拍板)
**Earn 不工作 · 只管账户 + 看成本** · admin layout 只 2 个 sub-nav:成本追踪 + 用户管理
**已砍**:平台概览 / 操作日志 / API 健康度

### 与 P0-VAT 主线协调
- NAV-IA 已收官 · 后续接力直接做 P0-VAT 剩余尾巴 或 Phase 6 进项管理 v118.40
- 接力机制:窗口开"继续"先看 P0-VAT 是否有阻塞 · 或挑 Phase 6/P0-VAT 推

### 4 类账号矩阵(铁律 · 详见 NAV_IA_PRD §2)
- **员工** = 看不到付费 / 测试 / 管理员
- **老板** = 看付费 · 看不到测试 / 管理员
- **skin** = 老板 + 测试中心
- **Earn** = **走独立 /admin layout** · 不进 home.html · **sub-nav 仅 2 项**(成本追踪 + 用户管理)

### Earn 铁律精确化(2026-05-15 Zihao 拍板)
**Earn 不工作 · 只管账户 + 看成本** · admin layout 只 2 个 sub-nav:
1. 成本追踪(`admin-cost` · 不动)
2. 用户管理(`admin-users` · 不动)

砍掉的(原 PRD 写了但 Earn 不需要):
- ❌ 平台概览
- ❌ 操作日志
- ❌ API 健康度

### 与 P0-VAT 主线协调
- NAV-IA 改前端 · P0-VAT 改后端 + 对账核心 · **同窗口可并行**
- 优先级:P0-VAT > NAV-IA · 但 NAV-IA 可挤 P0-VAT 等待时间(用户测试期/真实数据等)
- 接力机制:任何窗口开"继续"先看 P0-VAT 是否有阻塞 · 无阻塞 + 有空 → 挑 NAV-IA Phase 接力

---
> **当前线上(已 ssh 核实)**:**v118.44.0.7**(NAV-IA Phase 1-8 全部完成 · Earn admin SPA 独立)· `/api/version`=`11841085` · `systemctl is-active mrpilot` = active
>
> **🔥 本窗口决策(2026-05-14)**:**MR.ERP 项目搁置 → 全删源码(~5600 行)** · 等客户部署 `pearnly_bridge.php` API 后再接回
>
> **本窗口完成清单**:
>   - ✅ **v27.8.1.17.2** · P0-1 / P1-3 / P1-4 / P1-6 / P1-7 / P1-8 / P2-10 / P2-11 共 8 项前端修缮
>   - ✅ **v27.8.1.17.3** · P0-2 已推送标记 + 重复推送二次确认
>   - ✅ **v27.8.1.18** · P1-5 商品映射 tab + P2-9 全部跳过按钮
>   - ❌ ~~v18 智能归属(buyer_name → client 学习)~~ · 半完成已撤销
>   - ❌ ~~v27.8.1.19-debug(Bug #4 排查接口)~~ · 已撤销
>   - ✅ **v27.8.1.19-no-mrerp** · MR.ERP 代码全删(~5600 行)
>   - ✅ **v27.8.1.19-fix** · 修智能引号 JS 语法错误
>
> **下一步候选**:
>   - 🔥 **P0** · 等客户 bridge API · 收到 URL + KEY + schema 后接入 `pushHistoryToErp()` 空壳(0.5-1 天)
>   - P1 OCR速度优化(parse_vat_report 同步函数阻塞 async 根因 · 用run_in_executor修 · 约0.5天)
>   - P2 银行对账(等客户需求)
>   - 🚫 浏览器扩展(Zihao 拍板:不开展)
>
> **主线**:LINE 登录 ✅ → 用户管理 ✅ → 客户分配 ✅ → ERP 适配器 ✅ → **MR.ERP 整链路推完** ✅ → **MR.ERP 改善 11 项** ✅ → ⏸️ **MR.ERP 全删搁置(等 bridge API)** → P0-VAT 已完成 → P1 OCR 速度 / P2 银行对账 / Bridge API 接入
> **重要文档**:`HANDOVER_TO_NEXT_WINDOW.md`(本窗口完整交接 · 必读)· `MODULE_SALE_VAT_RECON_PRD.md`(P0-VAT 需求权威 · 已完结)

---

## ⚠️ 战略铁律 · 头号(2026-05-09)

**自动化 ERP 适配器主线升 P0** · 所有后续窗口必须以 ERP 工作优先 · 其他全部排后:
- ⏸️ 银行对账 v118.26.3/.4 暂停
- ⏸️ 用户管理深化 v118.29.x 推后
- ⏸️ 老板看板 v118.30.x 等 ERP 闭环后做
- ✅ Git 私库 + 公测可与 v118.27 并行

理由:OCR 推 ERP 才是 Pearnly 核心商业闭环 · 没这条线 · 银行对账 / 用户管理只是辅助。

---

## 一句话定位

Pearnly = **4 语言 SaaS（中 / 英 / 泰 / 日）** · 会计事务所 + SME 老板的 AP 自动化 SaaS · 4 语都是真产品语言 · **当前 GTM 首发 = 泰国市场** · 强项是多语言 OCR(泰中日)+ 全管道自动化(LINE / 邮件 / 文件夹)+ **ERP 中立中间件(任何 ERP 都能推 · API 直推 / xlsx 兜底 / 浏览器扩展全自动)** + 一页多发票拆分。

**「不让用户换 ERP · 让 Pearnly 适配所有 ERP」** = Pearnly 区别于 FlowAccount / PEAK 单兵作战的核心定位。

> 🌐 4 语铁律：每个功能必须 th / en / zh / ja 4 语完整 · 不许"先做泰文剩下再说" · i18n 字典顺序 th → en → zh → ja（开发优先级·非重要性）· 详见 CLAUDE.md 顶部铁律

---

## 线上版本

| 项 | 值 |
|---|---|
| 域名 | https://pearnly.com(Cloudflare DNS only · 自建 SSL · 已稳)|
| 服务器 | `root@45.76.53.194` · Vultr Tokyo · Ubuntu 24.04 · `/opt/mrpilot/` |
| 数据库 | Supabase PostgreSQL `aydjsgmirjpkjaqknmlg` · AWS ap-southeast-1 · service_role |
| 部署 | `bash /opt/mrpilot/deploy.sh /tmp/<tar.gz>` |
| 邮件 | Gmail SMTP · 发件人 `Pearnly <hello@pearnly.com>` |
| LINE Bot | Greeting message **ON** · 加好友自动推 4 语欢迎 + 6 位代码绑定引导 |
| LINE Login | Channel ID `2010022630` · Email scope **Applied** ✅ |
| env(关键)| `PEARNLY_PUBLIC_URL=https://pearnly.com` `LINE_LOGIN_CHANNEL_ID=2010022630` |
| 联系 | hello@pearnly.com / +66 86-889-2228 / LINE @059oupmg |

**当前 cache bust**:`home.css?v=11841085` · `home.js?v=11841085`(v118.44.0.7 · NAV-IA Phase 1-8 全部完成 · 2026-05-15 线上)
**下版本 cache bust**:`11841086`
**下版本 cache bust**:`11841079`

---

## 🔑 账号分工(铁律)

| 账号 | 用途 | 备注 |
|---|---|---|
| **skin306152@gmail.com (Google OAuth)** | 🧪 功能测试账号 + 测试中心白名单 + ERP dev seed 白名单 | `user_id=468b50c1-5593-4fd6-990d-515ce8085563` `tenant_id=040f012b-a456-49b3-a8f4-f83901bec9ea` |
| **Earn** | 👑 超管账号 | 永远只看 /admin · 不跑系统业务 · 仅平台管理 |
| mrerp@outlook.co.th | yearly · 1500 配额 · **绝对不许碰** | 真实付费用户 |

**铁律**:测产品功能 → skin OAuth · 测平台管理 → Earn /admin · 绝对不许碰 mrerp

---

## 🔌 MR.ERP 项目状态(2026-05-14 全删 · 等 bridge API)

**Zihao 拍板**：暂停 HTML 爬取方案 → 等客户部署 `pearnly_bridge.php` 提供 JSON API。

**项目内 MR.ERP 代码**：✅ 全删（app.py / db.py / home.js / home.html 共约 5600 行）

**给客户的 Bridge 文件**：`D:\Users\Skin\Desktop\pearnly_project\mrerp_bridge\`
- `pearnly_bridge.php`(单文件 · 191 行 · 提供 ping/products/customers/schema 接口)
- `INSTALL.txt`(3 步安装说明)

**客户装好后 Zihao 提供**：① ERP 网址 ② API 密钥 ③ schema 接口截图

**接入位置**：home.js `pushHistoryToErp()` 空壳 + 后端新建 bridge_client 模块

**保留的 MR.ERP 测试信息（备用）**：

| 项 | 值 |
|---|---|
| 域名 | `mrerp4sme.com`(已知) |
| 测试账号 | Username: `test01` |
| 测试公司 | `1010-01-000006` |
| 测试数据库 | `TEST2019`(`?comidyear=6&seldb=1`) |

---

## 🔥🔥 P0-VAT v118.32.3.x → v118.32.4.x 真实进展(2026-05-12 外部窗口核实)

> **背景**:上窗口意外关闭 + 文档没来得及更新 · 本窗口 ssh 服务器核实真实状态 · 文档曾误标 v3.9 待部署 · 实际已推到 v4.7 在线
> **核实方式**:服务器 `/opt/mrpilot/static/home.html` 的 cache bust + `/api/version` + 服务器代码版本注释 grep

**v3.0 → v3.9(全部已上线)** —— 上上窗口 BCDEF 优化 · 详情见旧 HANDOVER

**v3.10 → v4.7(已上线 · 上窗口意外关闭前推完 8 版 · 中间细节缺失)**:

| 版本 | 推断内容(代码注释 grep)| 状态 |
|---|---|---|
| v4.0 | C 进度反馈业务化 5 阶段步骤 | ✅ 在线 |
| v4.1 | 失败明细 + 业务错误码 4 语 + 失败 task 关联客户名 | ✅ 在线 |
| v4.2 | 微调(无注释痕迹) | ✅ 在线 |
| v4.3 | 金额格式化含币种 + 概览卡可见性控制 | ✅ 在线 |
| v4.4 | 无注释痕迹 | ✅ 在线 |
| v4.5 | 无注释痕迹 | ✅ 在线 |
| v4.6 | 无注释痕迹 | ✅ 在线 |
| v4.7 | done 状态防被轮询响应覆盖 | ✅ 在线 |

**v4.8(本窗口推上线 · 2026-05-12)**:

| 文件 | 改动 | 业务影响 |
|---|---|---|
| `vat_report_parser.py` | Gemini prompt 加 5 条严格规则 + self-check | OCR 不许自作主张改人名/税号/金额 · self-check 验证 pre_vat + vat ≈ total |
| `recon_routes.py` | RowActionBody 加 `source` 字段(invoice/report) | 行级操作记录用户采纳哪边为准 · 拼进 notes 不改 db schema |
| `home.js` "B 方案" | accepted_diff 视觉等同 matched(绿勾 + 已核对徽章)+ 2 个大按钮 + 新 action 映射(accept-invoice / accept-report / undo) | 金额对不上的行用户校对兜底 · 选完即视为对得上 |
| `home.html` / `home.css` | cache bust 11832470 → 11832480 + 配套样式 | - |

**部署核实**:`/api/version` = `{"version":"11832480"}` ✅ · `systemctl is-active mrpilot` = active

**⚠️ deploy.sh 坑**:`sleep 3` 不够(uvicorn 启动实际 7 秒)· 部署完瞬间 nginx 502 · 等几秒自动恢复 · 下次顺手把 sleep 改 10s

**🔴 P0 遗留(v4.8 没碰)**:6 张文件批量识别仍卡 10 分钟 · 嫌疑根因 `parse_vat_report` 同步函数阻塞 async 事件循环 · 推荐 hotfix 包 `run_in_executor`

**剩余 BCDEF 阶段**:D 后台异步 + LINE/邮件通知(v118.32.5)→ E OCR prompt 升级深化(v118.32.6 · v4.8 已偷跑 prompt 严格规则部分)

---

## 🔥🔥 v118.32.4.9 核对表重构 · 主线推翻(2026-05-12 Zihao 拍板)

> **触发**:Zihao 用 19 张 BAKELAB 发票 + 1 张销项税报告测试 v4.8 · 结果 1✓ 16⚠ 严重对不上 · 截图 + PDF 核对要求(`异常\ขั้นตอนการตรวจรายงานภาษีขาย.pdf`)发回
> **核心认知改变**:Pearnly = **核对表生成器**(不是匹配判定器)· 准确率 100% 定义 = **OCR 抽出来的字段跟原文 100% 一致**(不是匹配率 100%)

### 核对要求(来源 · Zihao 给的会计师标准 PDF)

**必识别 7 项 = PDF 编号 3-9**:
| # | 字段 | 备注 |
|---|---|---|
| 3 | 日期 | 必 |
| 4 | 发票号 | 必 |
| 5 | 客户名 | 必 |
| 6 | 买方税号 | 必 |
| 7 | 买方分公司 | 必(个人买家除外 · PDF 明文) |
| 8 | 净额(VAT 前) | 必 |
| 9 | VAT 金额 | 必 |

**辅助检查**:PDF 第 1 项"是否有 ใบกำกับภาษี 字样" + 第 2 项卖方 4 子项一致性(同一份报告应同一个卖方)

### 三个微版本拆分

**v118.32.4.9 核对表重构**(1.5 天):
- 后端 reconciliation_matcher.py 改"逐字段对照"模式 · 不归一化 · 如实展示两边
- 数据结构每行 7 字段 × 报告/发票两侧 + 一致 bool + 差异类型枚举
- 前端对账中心改对照表 UI(参考 PDF 底部表格布局)
- 每行差异提供 3 个动作:"改报告"/"改发票"/"两边都对是同一笔"
- **UI 顶部加"此次汇总"区**(Zihao 强调):
  - 总行数:N
  - 完全一致:X 行
  - 数据差异:Y 行(细分 · 发票号差/客户名差/金额差/...)
  - 🔴 OCR 没识别完整:Z 行
  - 散客无发票(正常):M 行
- 4 语 i18n × 全部新词条

**v118.32.4.10 7 项 OCR 准确率底线**(1 天):
- vat_report_parser.py + 发票 OCR 都加:7 项任一缺失 → 那一行红字"OCR 没识别完整"+ 重传按钮
- 后端业务规则校验(独立于对照):
  - 净额 + VAT ≠ 总额 → "金额自相矛盾"
  - VAT ≠ 净额 × 7%(非 0% / 免税)→ "税率异常"
  - 税号不是 13 位 → "税号格式异常"(散客除外)
- 系统标完用户自己决定要不要修

**v118.32.4.11 Excel 导出 + 列表时间戳**(0.5 天):
- 按 PDF 底部表格格式导出 Excel(左右双栏 + 备注 + 三签名位 ผู้จัดทำ/ผู้ตรวจสอบ/ผู้อนุมัติ)
- **Excel 表头 4 语 i18n**(F2 已做基础 · 这次扩到对照表全字段)
- **Excel 顶部加"此次汇总"区**(对应 UI 汇总)
- 近期对账列表加时间戳 + 默认时间倒序 + "清 7 天前任务"按钮

---

## 🧪 v118.32.4.9.5 内测结果 + v118.32.4.9.6 规划(2026-05-13 评估完)

> **背景**:v4.9.5 推上线后 Zihao 用 13 个场景实测 Excel 公式对账新方案 · 仅 skin306152 内测可见
> **结果**:4 全对 + 3 部分对 + 6 个 bug → 公式对账思路成立但实现要重做
> **现状**:已评估完工作量 · 等 Zihao 拍 504 + 拍"开干"

### 13 场景测试结果分布

| 类型 | 数量 | 含义 |
|---|---|---|
| ✅ 全对 | 4 | 发票号匹配 + 7 字段全等 + 金额对得上 |
| 🟡 部分对 | 3 | 发票号匹配但金额或字段有差异(Sheet 3 SUMIF 聚合后信息丢失看不出来) |
| 🔴 错 | 6 | 5 类 bug · 见下 |

### 5 个 bug 拆解(v4.9.6 一锅烩 · 评估 2.5 天)

| # | bug 现象 | 根因 | 修法 | 工时 |
|---|---|---|---|---|
| 1 | Sheet 1/Sheet 2「期间」列空白 | invoice.period AI 没抽 + Sheet 2 拿 period_year/month 没拼出 | build_excel 写入时 period 空 → 从 invoice_date / report_date 降级算 MM/YYYY(BE 转公历) | 0.2 天 |
| 2 | 散客发票(无税号)+ 散客在报告里 → 现在标"发票有报告无"孤儿 | 散客硬走"无税号即孤儿"分支 · 没去报告里查 | 散客改三重匹配 客户名+发票号+金额 · 加 `_match_cash_customer` 辅助 | 0.4 天 |
| 3 | Sheet 3 只对总金额 · 漏发票号差/日期差/期间差/分公司差/客户名差 5 维度 | Sheet 3 按 buyer_tax_id SUMIF 聚合 · 同客户多张发票合一行 · 维度信息丢失 | **Sheet 3 整段重写** · 砍 SUMIF · 改 INDEX/MATCH 按发票号一对一 · 5 维度各占独立列 · 报告侧落单行贴在表底 | 0.8 天 |
| 4 | 税号差 1-2 位直接判孤儿 | 等号严格比 · 无 fuzzy | 加 Levenshtein 编辑距离 ≤ 2 → 标"疑似匹配 · 请确认" · 不替用户判定(符合「我们只核实」铁律) | 0.3 天 |
| 5 | 发票缺税号(OCR 漏抽)→ 现在标孤儿 | 当前只看发票自己的 buyer_tax_id 空 = 散客 | 反向匹配 VAT 报告 · 找到了 → "OCR 漏抽税号 · 实际应为 XXX" · 跟 Bug 2 共享代码 | 0.2 天 |

### UI 美化清单(0.6 天 · 基准模板 `异常/vat_recon_BEAUTIFIED_demo.xlsx`)

| 项 | 实现 |
|---|---|
| Sarabun 字体(泰文优先) | openpyxl Font(name="Sarabun") + Tahoma fallback |
| 金额列千分位 #,##0.00 + 右对齐 | 已有部分基础 · 全字段对齐 |
| 斑马条纹(偶数行 #F9FAFB) | 数据循环里设 PatternFill |
| 表头蓝底白字 + 行高 32 | 蓝底白字已有 · 行高从 24 → 32 |
| 冻结第一行 | 已有 freeze_panes="A2"(保持) |
| Sheet 标签彩色 | ws.sheet_properties.tabColor(发票蓝/报告绿/对账橙/说明灰) |
| Sheet 3 KPI 4 大数字卡片 | 顶部 4 个大单元格 · 字号 18 加粗 + 背景色 + 大行高 |

### 核心改造点 · Sheet 3 推翻重做

- **当前**:按 `buyer_tax_id` 聚合 · 每税号 1 行 · `SUMIF(Sheet1!I)` 算金额合计
- **改后**:按 `invoice_no` 一对一 · 每张发票 1 行 · INDEX/MATCH 按发票号查报告
- **报告侧没匹配上的**:贴表底 ("发票无 · 报告有" · 不让信息丢失)
- **散客特殊处理**:三重匹配 客户名+发票号+金额 · 匹配失败再走 OCR 漏抽提示
- **结果**:用户能在一张表上同时看到 5 维度差异 · 不需要回到 Sheet 1/2 翻原数据

### v4.9.6 决策点(等 Zihao 拍)

🟡 **真实国税局 PDF 504 超时**(33 行 BAKELAB · pdfplumber 抽不到 → Gemini 25s timeout)
- 带:+0.5 天 · timeout 60s + 重试 + pdfplumber 优先 · 总 3.0 天
- 不带:推 v4.9.7 · 用户继续用合成数据测 · 总 2.5 天

### 部署后必测(≤2 项 · Zihao 已确认)

1. 重跑 13 个测试 PDF · 看每个 bug 都标对
2. 下载 Excel · 看格式美化是否到位

### 测试数据资产

- `异常/测试/v4_9_多场景/`(1 报告 + 12 发票)
- `异常/测试/รายงานภาษีขาย 03.69 - 001 033.pdf`(33 行真实国税局 · 504 那张)
- `异常/vat_recon_BEAUTIFIED_demo.xlsx`(美化基准模板)

---

## 🎯 v118.32.4.10 UX 大改造 · 等 v4.9.6 测过开干(3.1 天)

> **触发**:2026-05-13 Zihao 拍板 · 公式对账 v4.9.6 修完后 · UX 从"导出 Excel"升级为"UI 主流程 + Excel 变导出"
> **核心认知**:对账完成 → 进 UI 看大盘 + 详情 · Excel 不再是主出口 · 看齐 DataSnipper 同级 UX

### 改动清单

**改动 1 · 撤销旧模式(0.3 天)**
- 删「标准对账 / Excel 公式对账」toggle 切换器
- 销项税对账模块全平台默认走新流程 · 撤 skin306152 email 白名单
- BETA 标签保留(产品未完全成熟)
- 旧 vat_report_parser.py 等模块代码不动 · 保留向后兼容 · 但 UI 入口隐藏
- 试用账号限额 3 次 · 第 4 次弹"升级解锁无限次"(不是直接拒绝)
- 「近期对账任务」= **当前 tenant 内所有用户**的历史任务(不跨租户)

**改动 2 · UI 汇总页核心(2.3 天)**
- 后端:`/build` 不返 xlsx 改返 JSON + 新建 `vat_recon_results` 表 + 单独 export endpoint(0.8 天)
- 前端主体(1.8 天):
  - 顶部 KPI 4 大卡(行高 100)· 蓝总笔数 / 绿匹配 / 红异常 / 橙异常金额
  - 第二行筛选 + 操作:[全部][匹配][缺一边][金额不一致][待确认] tab + 排序 + 批量 + 📥Excel + 📄PDF
  - 对账明细表 · 列:☐ 状态 税号 客户 发票号 期间 发票金额 报告金额 差异 操作
  - 行颜色:匹配绿底 / 异常红底 / 待确认黄底 / hover 高亮
  - 4 语 i18n × 50+ 词条 + 移动端适配 + 防呆撤销

**改动 3 · Excel 导出按钮(0.2 天)**
- 复用现有 build_excel · 单独 GET endpoint
- 点按钮重新生成(用户改了数据也能拿最新)

### 关键决策(已拍)
- 撤白名单 → 所有 plan 都能用(trial 限 3 次 / monthly+yearly+lifetime+admin 无限)
- 详情抽屉 + PDF 预览推到 v4.11 · v4.10 只做列表 · 点行先不展开详情
- 审计 PDF 导出推到 v4.12 · v4.10 只做 Excel 导出

---

## ❌ v118.32.4.11 详情抽屉 + PDF 溯源 · **永久砍(2026-05-13 Zihao 拍板)**

> v4.11 详情抽屉 / PDF 溯源 · 永久砍(2026-05-13 Zihao 拍板)
> 理由:v4.10.10 已删整套 modal 预览代码 · 改走「Pearnly = 数据提取器 · 用户拿 Excel 自己看」路线
> v4.10.11 加了上传清单预览面板 · 用户感知充分 · 不需要再造任务详情预览
>
> 原计划(留痕 · 勿重启):点行 → 抽屉滑出 · 左半可编辑 · 右半 PDF.js + bbox 高亮 · OCR bbox 三层降级 · 3.0 天
> **下一个版本直接跳 v4.10.12(Excel 质量验收 + 任务列表时间戳 + 清7天)**

---

## ⏸️ v118.32.4.12 暂缓 · 待真实会计师反馈(P3 候选)

> **拍板**:2026-05-13 Zihao 决定 · v4.11 上线后让真实会计师试用 2-3 周再决定要不要做
> **理由**:避免凭空猜需求做错方向

候选内容:
- 审计 PDF 导出(KPI + 异常表 + 异常发票缩略图 + 签字栏 + 4 语)
- 历史对比卡片(同客户跨期"上月 X 张 · 这次 Y 张 · 异常增加 Z")
- 批量操作(选行 · 标已审/驳回 · 全部接受匹配项)

**触发条件**:
- 真实会计师试用 2-3 周
- 反馈表明这些功能确实是高频需求(不是"想要"而是"必需")
- 之后再开 v4.12 · 工时 2.7 天

---

### 推翻的旧方案(留痕 · 别再走回头路)

❌ **v4.9 旧方案 · INV ↔ IV 模糊匹配归一化** —— 替用户做决定 · 违反"我们只核实"哲学
❌ **v4.9 旧方案 · 客户名去 ์ 符号自动算同一人** —— 同上
❌ **匹配率 100% 当成功标准** —— 错位的 KPI · 真正 KPI 是 OCR 字段抽取准确率 100%

---

## 核心模块状态

### ✅ 已上线(线上稳定)

**v118.28 系列(2026-05-08 ~ 05-09 · 17 版)**
- v28.0 客户切换器 + v28.1.0 测试中心
- v28.3 LINE Bot URL · v28.4.x LINE 社交登录
- v28.5.x 顶栏布局 + 移动端 6 BUG
- v29.0 用户管理 UI + 操作日志
- v28.6 超管员工 tab 只读化
- v28.7 + v28.7.1 密码重置链接化
- v28.8 客户老板查 Pearnly 访问日志
- v28.9 改密后旧 JWT 失效
- v28.2 + v28.2.1 超管 /admin URL 独立
- v28.1 客户分配面板

**v118.26 银行对账系列(2026-05-09)**
- v26.0 顶级菜单 + 当月概览
- v26.1.x 批量上传 + 列表筛选
- v26.2.0/.1 右半屏 + 候选 pane + 客户徽章 ✅(测试通过)
- **v26.2.2** OCR P0 紧急修补(quota gate 早返回 · 修 v27.7 fix_orphan tenant=0 死结)✅
- **v26.2.3** admin_upgrade_user 字段修正 + forgot_password 改 SMTP ✅
- **v26.2.4** banned/inactive 安全闸 + 员工 plan 继承 + _require_owner_or_super 懒建 ✅
- **v26.2.5** signup 3 路径同事务建 tenant(根因修复)✅

**前期累计**
- 多语言 OCR(泰中日)· AP 自动化管道 · 4 语 i18n subscribeI18n 总线
- admin 后台 80% 完成度

### 🔥 进行中(主线 · 战略调整后)

**头号 P0 · 自动化 ERP 适配器**(13-17 天):
- ⏳ v118.27.0 客户/科目/税码映射底座(2-3 天)· **下一件**
- ⏳ v118.27.1 MR.ERP 适配器(方案 A · 5-7 天)· 等 4 件物料
- ⏳ v118.27.2 FlowAccount API 直推(2 天)
- ⏳ v118.27.3 PEAK API 直推(2-3 天)· 等 partnership
- ⏳ v118.27.4 Xero + QB API 直推(各 1.5 天)
- ⏳ v118.28.0 Express 适配器(3 天)
- ⏳ v118.28.1 「我的 ERP 是 ___」反馈框(0.5 天)

**P0 公测启动并行**:
- ⏳ A.1 Git 远程私库 push(0.5 天)

**P1 浏览器扩展平台**(公测后):
- ⏳ v118.31 系列 浏览器扩展框架 + MR.ERP web 自动点击(15-18 天)

### ⏸️ 暂停 / 推后

- v118.26.3 银行对账拖拽匹配(1.5 天 · ERP 闭环后)
- v118.26.4 银行 Excel/CSV 解析(0.75 天 · 同上)
- v118.29.x 用户管理深化(3.6 天 · 公测后)
- v118.30.x 老板看板 + 风控告警(L4-L6 · 7-10 天 · ERP 闭环后)

### ❌ 已取消 / 永久砍

- v27.8 全表 RLS(service_role 自动 BYPASS)
- ~~Mr ERP 直推对接(已复活)~~ → v118.27.1 立项
- Facebook 社交登录
- 超管直接重置客户密码(v28.7)
- 老板看到员工临时密码(v28.7)
- **桌面 RPA(D)** + **UI Automation API(E)**(2026-05-09 · v26.2 调研后定砍)
- 用友 T+ 适配(泰国基本无用户)
- Tally 适配(on-premise + API 弱)

### 🚫 阻塞(等外部条件)

- MR.ERP 4 件物料(现金销售真实数据 / 采购 / 会计凭证 / 错误信息)· 等 Zihao 补
- PEAK API 文档 + sandbox · 等 partnership 邮件回
- Express API 文档 · 等商务联络回

---

## 🆕 铁律清单(累计 33 条)

1-22:见 v118.28.1 HANDOVER · 不变

23. **战略调整 · 自动化 ERP 主线升 P0**(2026-05-09)· 银行对账让路 · 所有窗口 ERP 工作优先
24. **ERP 二分法**(2026-05-09)· 有 API → API 直推 / 无 API → A+C · v118.27.0 映射底座是依赖
25. **桌面 RPA(D)+ UI Automation(E)永久砍**(2026-05-09)· 桌面 ERP 走 A 兜底
26. **浏览器扩展平台(C)= Pearnly 平台能力**(2026-05-09)· 不只 MR.ERP · 复用所有 web ERP
27. **MR.ERP `mrerp4sme.com` PHP web 应用 · 厂商 Mr.ERP for SME**(2026-05-09)
28. **MR.ERP 文件格式铁律**(2026-05-09):.xlsx · 3 sheet 命名严格 `Worksheet/Worksheet 1/Worksheet 2`
29. **MR.ERP 字段格式铁律**(2026-05-09):日期字符串 YYYY-MM-DD · 客户代码三段式含泰文 · 税率字符串枚举
30. **MR.ERP 数据库 / 多公司 = 服务器分配**(2026-05-09):URL 参数 · Pearnly 推不需带
31. **MR.ERP 无 API / 无文件夹监听 / 无定时导入**(2026-05-09):全自动只能走方案 C 浏览器扩展
32. **L1-L6 产品价值定位**(2026-05-09):入账 → 学习 → 对账 → 看板 → 合规 → 风控 · 客单价 599 → 3000-5000
33. **公测策略**(2026-05-09):Git 私库后即启动 · ERP 适配器并行 · 公测反馈反推优先级

### 🆘 v118.26.2.2-2.5 紧急修补铁律(34-43)

34. **OCR quota gate 早返回模式**(v118.26.2.2):有效 plan 用户(trial/free/pro/firm/enterprise/monthly/yearly)在 `_check_user_quota` 顶部直接放行 · lifetime 单独看自带 key
35. **tenants 表无 plan / max_seats 字段**(v118.12.1 → v118.26.2.3):任何 `UPDATE tenants` SQL 严禁包含这 2 字段 · 否则整条抛错被 try 吞
36. **forgot_password 邮件用 SMTP 主用**(v118.26.2.3):`_smtp_send_email` from app.py · Resend 作 fallback · 不依赖 RESEND_API_KEY
37. **被禁用 / 未激活账号 OCR 拦截**(v118.26.2.4):`_check_user_quota` 顶部 `is_banned` / `is_active=False` 早返回
38. **员工 plan 继承在 OCR 路径**(v118.26.2.4):`_check_user_quota` 检测 `role=member` 时查 owner.plan
39. **`_require_owner_or_super` 懒建 tenant 兜底**(v118.26.2.4):`tenant_id=NULL` 时自动建
40. **signup 3 路径同事务建 tenant**(v118.26.2.5 根因解):`_ensure_tenant_for_new_user(cur, user_id, plan, ...)` · 用 PLAN_CONFIG 真实 quota
41. **新注册 token 带 tenant_id**(v118.26.2.5):signup 主路径返回的 access_token 立刻带新 tenant_id
42. **大改造后 5 步回归测试铁律**(SOP §7.5 新增):动 users/tenants/plan/role/quota/auth 后 · 部署后跑 5 步验证 · 一步红立刻 hotfix
43. **LINE push API ack 不可靠**(2026-05-09):已有 LINE→Email fallback 是产品权衡 · 不修

---

## 数据资产

| 资产 | 数量 | 用途 |
|---|---|---|
| 银行对账单 PDF | 9 张 | 对账测试 |
| 发票 OCR 异常规则 PDF | 9 张 | OCR 边界测试 |
| skin OAuth 测试数据 | 8 个 TEST_ 客户 / 37 张发票 / 5 条异常 | 功能测试 |
| **MR.ERP 销售-赊销真实样本** | 1 份 .xlsx(2 行数据 · 文件名 mrerp_sample_SC_credit_real.xlsx) | **v27.8.1.0 推送测试 + 适配器开发** |
| **MR.ERP 销售-现金空模板** | 1 份 .xlsx | 同上(待补真实数据 · 当前 sheet 命名错 Sheet1-4 · 应是 Worksheet/Worksheet 1-3 · 不能直接用) |
| **PEARNLY_ERP_RESEARCH_2026_05.md** | 11 家 ERP API 状态调研 | 战略决策档 |
| **PEARNLY_ERP_DEEP_2026_05.md** | 自动化模块深度优化 + L1-L6 | 战略决策档 |

---

## ⭐ 极简模式(新窗口必读)

省 70% Claude 额度 · 4 语红线不破。

### 启动步骤

1. 新窗口第一句话发简化版 `NEW_WINDOW_OPENER.txt`(3 行)
2. 把当前最新 `pearnly_v118_27_8_1_14d.tar.gz` 拖进对话框
3. 模板「我要做的事」一栏写一句话需求
4. **推荐第一个版本:v118.27.8.1.15 批量上传 500 + plan +300 + auto_push 默认开**(P0-A 第一站 · 1 天)
5. **完整路线**:v15→v22(9.5 天)按 BACKLOG.md 顺序推 · 中途不许扩大范围

### 新窗口 Claude 必须遵守

红线 / 业务闭环 / 省钱 / UI ≤ 5 项 / 部署后命令验证 / 测试中心隔离 → 全在 `PEARNLY_WORKFLOW_SOP.md`。

---

## 当前已知小问题

- 🔴 **P0 · v4.9.2 分组 bug 暂停未解**(2026-05-13):用户拖 13 个 v4_9_多场景测试文件 · stats 显示 12 文件 12 发票 0 VAT 报告 → **VAT 报告被识别成 invoice 而非 vat_report** · v4.9.2 加的 "filename 含 รายงาน → 强制 vat_report" 没起作用 · Zihao 拍板暂停修转去做 v4.9.5 内测 · 留给 v4.9.3 / v4.9.6 一起 fix
- 🔴 **v4.9.5 内测 · 真实国税局 PDF 504 超时**(2026-05-13):合成 PDF(12 行 · reportlab)能跑通 · 但真实 BAKELAB 测试文件夹的 `รายงานภาษีขาย 03.69 - 001 033.pdf`(33 行 · 真实国税局格式)Gemini 25 秒超时 · 嫌疑:PDF 是图片化文字层 → pdfplumber 抽不到 → fallback Gemini 但 timeout 太短 · v4.9.6 已规划修(timeout 60 + 重试 + pdfplumber 优先)
- 🟡 **v4.9.5 测试反馈待修(5 bug + UI 美化 · 2.5 天 已评估)**:详见上方"v118.32.4.9.5 内测结果 + v118.32.4.9.6 规划"段 · 等 Zihao 拍 504 + 拍"开干"
- 🔴 **P0 · 6 张文件批量识别卡 10 分钟未根本解决**(v118.32.3.0-3.9 多版未解决 · 下窗口必修)· 嫌疑根因:`parse_vat_report` 同步函数阻塞 async 事件循环 · 详见 `HANDOVER_v118_32_3_9.md`
- 🟡 P1 · F1 金额对齐(`amount_pre_vat`)用户未实测 5/5 BAKELAB 匹配
- 🟡 P1 · F2 Excel 4 语 i18n 表头(中/英/日/泰)用户未实测
- 🟡 P1 · 系统设置改 modal(v3.6-3.9)用户没逐个 tab 测过 · 可能某些 pane 内容布局错乱
- 🟡 P1 · 单据记录列贴右(v3.9 才找到根因 `.card { padding: 20px }`)用户未确认
- 🟢 P2 · `gemini_engine.py` 不在 project knowledge · E 阶段(OCR prompt 升级)前必须 scp 拉到本地
- 🟢 P2 · 测试中心 sidebar badge 当前显示 "24" 异常 · 下窗口让用户截图看具体错误
- v118.26.2.5 用户管理/租户连环 BUG 全修通过用户测试 ✅
- `/api/me/plan` 慢 2.5-3.4s(测试中心 api_slow 触发)· 加 5 分钟前端缓存 · 0.2 天 · P2
- `deploy.sh` 不复制 `VERSION` · 顺手补
- **A.1 Git 远程私库 push**(0.5 天)· **公测前必做**
- home.js 死代码(admin-modal-reset-pw 词条 / showResetPwdResult / `_admin_*_LEGACY`)· 0.2 天 · P3

---

## 公测启动检查清单(只剩 1 项)

| 项 | 状态 |
|---|---|
| LINE 登录 + 补邮箱 modal | ✅ v28.4.x |
| 操作日志 + 分页 + CSV | ✅ v29.0 |
| 超管员工 tab 只读化 | ✅ v28.6 |
| 密码重置链接化 | ✅ v28.7 |
| /reset 落地页 | ✅ v28.7.1 |
| 客户老板查 Pearnly 访问日志 | ✅ v28.8 |
| 改密后旧 token 失效 | ✅ v28.9 |
| 超管 /admin URL 独立 | ✅ v28.2 (+ .1) |
| 客户分配面板 | ✅ v28.1 |
| 银行对账右半屏 | ✅ v118.26.2.1(测试通过) |
| 用户管理/租户连环 BUG 修补 | ✅ v118.26.2.2-2.5(测试通过) |
| **Git 远程私库 push** | ⏳ 0.5 天 |

**做完 Git 私库即启动公测** · ERP 适配器(v118.27.x)并行 · 公测反馈反推 ERP 排序优先级。

---

# 📌 v118.27 系列进度补丁(2026-05-10)

> 本文档主体写于 v118.26.2.5 时代 · v27.x ERP 适配器系列推进至 v27.7.1 · 此章节同步实际进度

## v118.27 系列 ERP 适配器 · 已上线版本(v27.0 → v27.7.1)

| 版本 | 主题 | cache bust | 状态 |
|---|---|---|---|
| v27.0 | 客户/科目/税码映射底座(3 张表 + 6 接口) | - | ✅ |
| v27.0.1 | pearnlyConfirm 全局弹窗 + ERP 映射搬「自动化」+ seed 提速 | - | ✅ |
| v27.1 | MR.ERP xlsx 适配器(stub-first · sales_credit 单张) | - | ✅ |
| v27.4 | Xero OAuth 2.0 适配器 + 推 ACCREC + 错误码 4 语 | - | ✅ |
| v27.4.1 | Xero scope broad → granular | - | ✅ |
| **v27.4.2** | MR.ERP sheet 数动态(customer/product=1 / journal=2 / sales=3 / payment=4) | 11828944 | ✅ |
| **v27.5** | 抽屉 1 推按钮统一 split + 下拉 + `/api/erp/connectors/status` | 11828945 | ✅ |
| **v27.5.1** | hotfix 多发票文件导出只 1 行 BUG · invoices 数组 + 拆 N 行 | 11828946 | ✅ |
| **v27.5.2** | hotfix race condition + SKIN 双闸白名单 | 11828947 | ✅ |
| **v27.5.3** | 「泰国销售明细」导出模板(`excel_template_th.py`) | 11828948 | ✅ |
| **v27.5.4** | 新版本检测横幅 · `/api/version` + 5min 轮询 + no-cache | 11828949 | ✅ |
| **v27.5.5** | hotfix unified IIFE race · placeholder-first | 11828950 | ✅ |
| **v27.6** | 4 模板对齐 · 砍 ERP 录入格式 · 路由分发 | 11828951 | ✅ |
| **v27.6.1** | hotfix 抽屉推送下拉改向上弹出(dropup) | 11828952 | ✅ |
| **v27.7** | 识别中心下拉向上弹 + `/api/ocr/export-by-history-ids` | 11828953 | ✅ |
| **v27.7.1** | hotfix 客户导出 BUG · `db.list_ocr_history` retention_days Optional | 11828954 | ✅ |
| **v27.8.0.4** | MR.ERP 反向工程 + 后端引擎(mrerp_pusher.py + kms_helper.py · 5 步实测全通) | - | ✅ 临时部署 /tmp/v27_8_test |
| **v27.8.1.0** | MR.ERP MVP · mrerp_credentials 表 + 5 db 函数 + 3 endpoints + 凭据 modal | 11828960 | ✅ |
| **v27.8.1.1** | hotfix · setTimeout 600/700ms 自检定时(防 IIFE race) | 11828961 | ✅ |
| **v27.8.1.2** | excel_template_th.py 公式修复(=E*F · 防循环引用) + `_userInfo` 轮询 | 11828962 | ✅ |
| **v27.8.1.3** | 「识别完自动推送」toggle 端到端 · auto_push 字段 + OCR 钩子(2 处) | 11828963 | ✅ |
| **v27.8.1.4** | mrerp_xlsx_generator schema 大改对齐 Korn 真样本(header 18/detail 8/tail 3) | 11828964 | ✅ |
| **v27.8.1.5** | invoice_no `INV-2026-0501` → `690415-001`(BE+MM+DD+seq) + 下载 xlsx debug | 11828965 | ✅ |
| **v27.8.1.6** | 抢救式抓 MR.ERP 错误 hint(red text + JS alert + ไม่พบ/ผิดพลาด)+ raw HTML 存 | 11828966 | ✅ |
| **v27.8.1.7** | 强制 cell 物理保留(`' '` 占位) + sheet1 col 19 spacer · dim=A1:S2 | 11828967 | ✅ |
| **v27.8.1.8** | 🧪 Korn 真样本对照测试 endpoint + UI 按钮 · 决定性诊断(mrerp_pusher OK + xlsx 字节差异) | 11828968 | ✅ |
| **v27.8.1.9** | 后处理 inlineStr → sharedStrings · 处理 `&#NNNN;` 双重 escape 坑 | 11828969 | ✅ |
| **v27.8.1.10** | 🔬 自诊断对比 endpoint(zip 文件级 diff) + UI modal + 两 xlsx 下载 | 11828970 | ✅ |
| **v27.8.1.11** | XML 后处理 · row spans + 完全空 cell + sheet3 只 header + 去 t="n" | 11828971 | ✅ |
| **v27.8.1.12** | ⭐ Korn 模板克隆方案 · 6 metadata 文件不动 · MR.ERP 推送 100% 打通 ✅ | 11828972 | ✅ **真写库验证** |
| **v27.8.1.13a-14d** | 10 个子版本 · MR.ERP 整链路用户旅程完美闭环(凭据 modal 重构 / 字段映射 UX / armas 真客户主表 / mini modal 内联引导 / 智能推荐排前 / Korn 0006 真实推送) | 11828973-11828122 | ✅ |
| **v27.8.1.14e** | 修「上传图片多选强制合并」痛点 · 默认行为反转(gallery 默认分别 · camera 默认合并) | 11828123 | ✅ |
| **v27.8.1.15** | 批量 500 张 + plan 上限+300 + admin 999→9999 + auto_push 默认开 + 大批量进度条 + 新用户引导 modal | 11828124 | ✅ **用户测试通过** |
| **v27.8.1.16** | score=1.0 零点击 + 0.7-0.97 中分 undo toast(3 秒倒计时 + [改一下]/[没问题])+ 列表 recommend/maybe 徽章 | 11828125 | ✅ **用户测试通过** |
| **v27.8.1.17** | 商品对照表 stkmas + detail 行真 product_code + product mini modal(逐个解决)+ 子串闸 fix(占比 ≥ 0.5 才认 0.85)| 11828126 | ✅ **已部署 · 等用户测** |
| **v27.8.1.17.1** | 租户管理 6 bug hotfix(plan_expires_at 字段同步 / monthly/yearly/lifetime 分支 / 员工字段全继承 / tenant.subscription_expires_at 同步 / 幽灵字段移除 / SSoT 对齐) | 11828127 | ⏳ **待部署测试** |

**线上版本号**:**v118.27.8.1.14b.3**(2026-05-14 · 3 项 bug 修复全上线)
**前期里程碑**:v27.8.1.12 MR.ERP 推送通道打通 · 数据真进 TEST2019 库
**核心成果**:`SI690415-001` 净额 4,635.24 写入 mrerp4sme.com TEST2019 库验证通过 · 整条 OCR → MR.ERP 自动推送链路闭环

---

## 🔥 P0-ERP 改善清单（2026-05-14 · **排在 v18-v22 和其他所有模块之前**）

> **来源**：2026-05-14 全流程产品审查（OCR 识别 → 归属客户 → MR.ERP 推送）完整 UX/逻辑/Bug 审计
> **优先级**：全部排在 v18-v22、OCR 速度优化、银行对账之前

### P0 · 立刻修（下窗口第一优先）

| # | 问题 | 文件 | 工时估算 |
|---|---|---|---|
| 1 | **归属客户保存后必须关闭重开抽屉才能推送**：前端 `_openHistoryDrawer` 拿的是旧 task 对象 snapshot，保存后没刷新 state，导致 `client_id` 仍为空，推送报「请先归属客户」| `home.js` | 0.5h |
| 2 | **推送成功后无标记，可重复推同一张发票**：无 `is_pushed` flag，无二次确认，用户无法判断是否已推 | `home.js` + 后端 | 1h |

### P1 · 本周

| # | 问题 | 文件 | 工时估算 |
|---|---|---|---|
| 3 | **错误文案误导**：报「请先在自动化配置 ERP 端点」，实际原因是「请先为此发票选择归属客户」，并高亮选择框 | `home.js` i18n | 0.3h |
| 4 | **识别成功率显示超 100%**（333% 等）：应改为「共识别出 N 张发票」，去掉百分比 | `home.js` | 0.3h |
| 5 | **字段映射缺「商品映射」tab**：现有客户/科目/税码三 tab，无法管理 `item_name → erp_code` 映射，删除操作全靠 SQL | `home.js` | 2h |
| 6 | **商品 modal 搜索框未预填充 OCR 商品名**：每次手动输入，效率低 | `home.js` | 0.5h |
| 7 | **推送成功弹窗无 MR.ERP 跳转链接**：用户无法一键跳去 MR.ERP 赊销列表核实 | `home.js` | 0.5h |
| 8 | **客户映射备注含内部版本号「v16」**：应改为「系统自动识别 · {日期}」 | `home.js` | 0.2h |

### P2 · 下周

| # | 问题 | 文件 | 工时估算 |
|---|---|---|---|
| 9 | **商品 modal 缺「全部跳过」按钮**：多件商品时每次只能逐个跳 | `home.js` | 0.5h |
| 10 | **推送日志「ERP 返回结果: 2」无意义**：需翻译为友好文案「成功推入 N 行明细」| `home.js` | 0.3h |
| 11 | **商品 modal 加载无进度提示**：连接 MR.ERP 商品库期间界面空白，用户不知道在加载 | `home.js` | 0.5h |

### 逻辑设计（需 Zihao 拍板）

| # | 问题 | 影响 |
|---|---|---|
| 12 | **`erp_client_mappings` 按 `client_id` 存储**：同一 Pearnly 客户下不同买方（如不同分公司）全推同一个 MR.ERP 客户 · 会计事务所管多家公司时可能错推 | 设计决策：保持现状（适合一对一绑定）vs 改为按 `buyer_name` 存储（适合多买方场景）|

### Bug #4（后续调查）

| # | 问题 | 调查方向 |
|---|---|---|
| 13 | **`/api/erp/mrerp/products` 不返回 P001/Pepsi 500ml**（已 Approved）：`_mrerp_fetch_products_raw` 通过 stkmas showdata.php 抓页面 HTML，疑似 P001 所在行解析失败 | 服务器手动运行 `_mrerp_fetch_products_raw(tid)` 打印原始 HTML，确认 P001 是否在里面，定位 `_parse_mrerp_products_html` 解析问题 |

### 绕过方案（Bug #4 修复前）

商品 modal 下方有「手动输入编号」折叠区，用户可直接键入 P001 → 保存 → 映射写入 → 下次同商品名自动复用

---

## 🔥 v118.27.8 系列细化(本窗口拍板 · 不推翻三层架构)

### 三层架构红线(继承 · 全部生效)

| 层 | 名称 | 客户类型 | 状态 |
|---|---|---|---|
| **C** | xlsx 兜底 | 入门 / 谨慎 | ✅ v27.5.3+v27.6 已上 |
| **D** | 浏览器扩展(用浏览器现成 PHPSESSID 推) | 不存密码但要一键 | ⏳ v118.30+ |
| **A** | 后端模拟登录(凭据 KMS 加密存) | 信任 Pearnly · 后台批量 | ✅ 引擎 v27.8.0.4 完成 · 🔥 接 UI 在 v27.8.1.0 |

A 永远不是默认 · UI 必须显眼让用户知道也支持 C。任何一层失败 → 自动降级。

### v27.8 拆分进度(2026-05-11 v14d 收尾更新)

```
v27.8.0   反向工程 + 后端骨架            ✅ 100%
v27.8.1.0 MVP(凭据 + 一键直推)         ✅ 完成
v27.8.1.1 IIFE race + setTimeout 修复   ✅ 完成
v27.8.1.2 公式修复 + _userInfo 轮询      ✅ 完成
v27.8.1.3 自动推送 toggle 端到端         ✅ 完成
v27.8.1.4 schema 大改对齐 Korn 真样本    ✅ 完成
v27.8.1.5 invoice_no 格式 + 下载 xlsx    ✅ 完成
v27.8.1.6 抢救式抓 MR.ERP 错误 hint      ✅ 完成
v27.8.1.7 强制 cell 物理保留 + spacer    ✅ 完成
v27.8.1.8 Korn 真样本对照测试(神器)     ✅ 完成
v27.8.1.9 inlineStr → sharedStrings      ✅ 完成
v27.8.1.10 服务器端字节级自诊断          ✅ 完成
v27.8.1.11 XML 后处理对齐 row spans      ✅ 完成
v27.8.1.12 ⭐ Korn 模板克隆方案 · 推送 ✅ 完成 · 真写库验证
v27.8.1.13a 凭据 modal 重构 + 字段映射 UX + 上传自动归属 bug 修复  ✅ 完成
v27.8.1.13b 测试连接 → 自动探测账套(selectdb.php 解析)            ✅ 完成
v27.8.1.14a/14a.1 dev 抓 MR.ERP 页面 / 客户列表(反向工程)         ✅ 完成
v27.8.1.14b/14b.1 OCR 抽屉 mini modal + 错误码归一 · Korn 0006 验证 ✅ 完成
v27.8.1.14b.2/14b.3 banner + UX 减重(顶栏 SSoT)                  ✅ 完成
v27.8.1.14c 数据源切到 armas 真客户主表 + 深度栈精确解析             ✅ 完成
v27.8.1.14d ⭐ OCR 买方名模糊匹配 + 推荐排前 · MR.ERP 整链路闭环   ✅ 完成
v27.8.1.14e 上传图片多选默认改成分别 · camera vs gallery 分支       ✅ 完成

🔥 P0-A · MR.ERP 全链路完美化(9.5 天):
v27.8.1.15 批量 500 + plan +300 + auto_push 默认开 + 新用户引导     ✅ 完成 · 用户测试通过
v27.8.1.16 score=1.0 零点击 + 0.7-0.97 中分 undo toast              ✅ 完成 · 用户测试通过
v27.8.1.17 商品对照表 stkmas + detail 行真商品码 + 子串闸 fix       ✅ 完成 · 已部署 · 等测试
v27.8.1.17.1 租户管理 6 bug hotfix(套餐升级数据一致性)             ⏳ 待 Zihao 部署测试
v27.8.1.18 OCR 买方名 → Pearnly 客户智能归属 + 学习供应商映射 + 字段对照表 product subtab(v17 遗留) 🔥 下个窗口主任务(1.4 天)
v27.8.2   ERP 主页 UI 三件套(完整映射 UI 已删 · 被 mini modal 替代) 🔥 (2 天)
v27.8.3   推送预览 + 凭据失效检测 + 失败自动降级 xlsx              🔥 (1.7 天)
v27.8.4   真实可达性测试                                          🔥 (0.5 天)
v27.8.5   重复防护 + 批量推送 + ERP 链接 + LINE 推老板             🔥 (1.9 天)

P1 · 公测前 / 战略:
v27.8.6   webhook 卡片化 + 砍蓝按钮(原 v27.8.1.16 降级)           (0.5-1 天)
A.1       Git 远程私库 push · 公测前必做                          (0.5 天)
```

### 🔥 P0-A · MR.ERP 全链路完美化 v15-v22(9.5 天 · v14d 窗口拍板 · 用户全采纳)

> **来源**:`Pearnly_票据到ERP归档_用户旅程分析_v118_27_8_1_14d.md` · 用户拍板"MR.ERP 相关全部排前 · 其他依次排序"
> **详细任务**:见 BACKLOG.md 的 P0-A 章节

**优化目标**(操作数对比):
- 现状:新客户 score=1.0 → 2 次操作 / 批量 50 张 → 50 次推送
- v22 完成后:**新客户 score=1.0 → 0 次操作**(零点击)/ **批量 50 张 → 1 次推送**(批量推)
- 80% 用户场景"想 0 次"· 20% 用户场景"想 1 次"· 0% 用户场景"想 2+ 次"

| 版本 | 内容 | 估时 | 状态 |
|---|---|---|---|
| **v15** | 批量上传 500 + plan 上限+300 + auto_push 默认开 + 新用户引导 | 1 天 | ✅ |
| **v16** | score=1.0 零点击 + 中高分快速确认 toast | 0.6 天 | ✅ |
| **v17** | 商品对照表 stkmas + detail 行真商品码 | 1.5 天 | ✅ 等用户测 |
| **v17.1** | 租户管理 6 bug hotfix | 0.3 天 | ⏳ 待部署 |
| **v18** | OCR 买方名 → Pearnly 客户智能归属 + 学习供应商映射 + 字段对照表 product subtab | 1.4 天 |  |
| **v19** | ERP 主页三件套(4 KPI + 连接器 + 推送日志) | 2 天 |
| **v20** | 推送预览页 + 凭据失效检测 + 失败自动降级 xlsx | 1.7 天 |
| **v21** | 真实可达性测试 | 0.5 天 |
| **v22** | 重复防护 + 批量推送 + ERP 链接 + LINE 推老板 | 1.9 天 |

### 红线 2 · ERP 对接主页 UI 三件套(继承 · v19 实施)

```
① 统计区 · 顶部 · 4 张 KPI 卡(今日已推/待推/失败/自动化率)
② 连接器卡片 · 中部 · Xero/MR.ERP/Webhook + 虚位卡(FlowAccount/PEAK/QB 灰)
③ 推送日志 · 底部 · 表格 + 时间筛选 + 失败行「解决」跳 OCR
```

**注**:原计划在 v19 加的「完整映射 UI / 默认值设置 modal」**已删** —— 14b 已决定 mini modal 替代 + 默认值后端写死(铁律 62)。

### 红线 3 · 真正难点是映射 UI(已被 v14d 解决)

OCR 拿名字 · MR.ERP 要 code:
- 客户名 · v14b/c/d 已用 mini modal + armas + 模糊匹配解决 ✅
- 商品名 · v17 商品对照表用同样方案解决
- 默认仓库 / 部门 / 销售员 · 后端写死(铁律 60 业务化)· 不再要求用户配

---

## 🔌 MR.ERP 反向工程结果(本窗口完成 · 100%)

### 测试环境

```
URL:        https://www.mrerp4sme.com
Username:   test01 / Password: test01
公司:       1010-01-000006 บริษัท ทดสอบการใช้ จำกัด
数据库:     TEST2019(URL ?comidyear=6&seldb=1)
内部 idus:  15(test01 用户 · 从 formupload.php hidden input scrape)
```

### 全 5 步 endpoint 字典(实测通过 ✅)

| 步 | URL | Method | Body | Response |
|---|---|---|---|---|
| 0a 预热 | `/` | GET | - | (set PHPSESSID) |
| 0b 登录 | `/login/checklogin.php` | POST | `txtusers=X&txtpasswords=X&btnsubmit=Submit` | 200 + HTML(同 URL · 不 redirect) |
| 0c 选公司页 | `/login/selectdb.php` | GET | - | 200 |
| 0d 选公司 | `/login/mainmenu.php?comidyear=6&seldb=1` | GET | - | 200 + 主菜单 HTML(被踢回 login = 鉴权失败判定) |
| 0e scrape idus | `/impartran/formupload.php?idmenu=370` | GET | - | 200 + HTML(含 `<input hidden name="idus" value="15">`) |
| **1 上传** | `/impartran/component/uploadexcel.php` | POST | **multipart**: `uploadfile=<file>` + `idus=15` + `selmenu=118` | 200 + 0 字节(文件存 server session) |
| **2 预览** | `/impartran/formrdpc.php` | POST | `idus=15&selmenu=118`(form-urlencoded) | 200 + HTML(form 含 `cbimport[N]` checkbox) |
| **3 确认** | `/impartran/component/importpc.php` | POST | **multipart**: `idus + selmenu + cballfrmimport1=on + cbimport[N]=N` | 200 + 短字符串(数字="2"=新 row id 成功 · 非数字=错误) |

### 路径分类(铁律 51)

```
impartran/  = 交易类业务单据(销售/采购/收付款 import · idmenu=370 是赊销)
imparse/    = 主数据类 / 现金销售 import 走这里(idmenu=371)
expartran/  = 交易类导出(idmenu=404 商品销售导出)
```

### idmenu / selmenu 字典(部分 · v27.8.2 补全)

| 业务 | idmenu | selmenu | 路径 | sheet 数 | 状态 |
|---|---|---|---|---|---|
| SC 赊销 import | 370 | 118 | impartran | 3 | ✅ 实测 |
| SC 销售导出 | 404 | 118(下拉切) | expartran | - | ⚠️ URL 知 · cURL 待抓 |
| SE 现金销售 import | 371 | ❓ 未抓 | imparse | 4 | ⏳ |
| 采购 / 收款 / 付款 / 凭证 | ❓ | ❓ | ❓ | ❓ | ⏳ v27.8.2 |

详细 endpoint 字典 + 8 个踩坑细节 + scrape idus bug 修复 · 见 `HANDOVER_v118_27_8_1_0.md`。

---

## 🆕 铁律清单(累计 62 条 · v14d 窗口新增 61-62)

旧 1-58 见 v118.27.8.0 HANDOVER · 不变。

### 本窗口新增(2026-05-11)

59. **MR.ERP sales_credit xlsx 必须用 Korn 模板克隆生成**(2026-05-11):`mrerp_xlsx_generator.py` 的 sales_credit 路径走 `_generate_xlsx_sales_credit_korn_clone()` · 6 个 metadata 文件不动(workbook.xml / [Content_Types].xml / styles.xml / theme.xml / 2 个 rels) · 只重写 sharedStrings + sheetData · 模板必须存在 `/opt/mrpilot/test_data_mrerp_sample_SC.xlsx` · 不许直接 openpyxl save(它会重写 workbook.xml 丢失 PhpSpreadsheet 兼容性)

60. **UI 文案业务化** · 不能用程序员术语(2026-05-11):「映射」→「对照」/「对照表」(会计师懂)· 「凭据」→「账号」 · 「ERP 端编号」→「客户在 ERP 里的编号 / 商品码」 · `comidyear` / `seldb` 折到「高级设置」隐藏 99% 用户不动 · 文案要假设「会计师不懂技术」 · 所有出现技术名词的地方都要业务化

61. **MR.ERP 主数据用 `showdata.php` 通用 pattern 抓**(2026-05-11 · v14c/v14d 实测):所有 `/X/allview.php?idmenu=N` 列表页 = 空壳 + AJAX 后填(`<div id="showdata">` 由 `showdata()` 异步填充)· 客户端反向工程要点:① warm-up GET 列表页(种 Referer / PHPSESSID)· ② POST `/X/component/showdata.php`(form data: `showdata_numrows=30 / showdata_pages=N / searchdataval=""`)翻页拼接 · ③ 用顶层 `<span>` 深度栈解析(避开 URA hover 嵌套 span 干扰)· ④ 停止条件:返回空 / `id="nodata"` / `len(chunk) < 10` · 任何 MR.ERP 主数据(客户 armas / 商品 stkmas / 供应商 apmas / 仓库 store 等)都走这套

62. **字段对照表 = 后台页 · 不是主入口**(2026-05-11 · v14b 大反思):99% 用户**不**主动进「字段对照表 / 自动化 → ERP 对接 → 字段映射」 · 那是给老司机审计 / 批改用的后台页 · 用户的客户/商品/税码映射应在 **OCR 抽屉推送时按需配**(失败那一刻就地解决) · 任何"先去配置 → 再使用"的 UX 都是失败设计 · mini modal 内联引导 + 智能推荐 + 手动输入备份才是正解

### 本窗口 v15-v17.1 新增(2026-05-11)

63. **模糊匹配子串规则必须有占比闸**(2026-05-11 · v17 边界 fix):`_match_buyer_score` 的 0.85 子串包含规则需加约束:短串占长串 ≥ 50% 才认 0.85 强子串匹配 · 否则降级 SequenceMatcher 兜底。否则会出现「Random XYZ Co」误推荐「XYZ Limited」(3 字符占 9 字符 0.33 触发 0.85)。这条铁律适用任何主数据模糊匹配 ·  客户 / 商品 / 供应商通用。

64. **用户字段必须 SSoT · 顶栏 vs 设置页**(2026-05-11 · v17.1):`/api/me/plan` 是套餐相关字段的权威源 · `_build_user_info` 同样字段必须对齐。两个 endpoint 都要返 `plan_expires_at` / `plan_days_left` / `trial_expires_at` / `trial_days_left` 这一套 · 顶栏走前者 · 设置页走后者 · 双方显示必须完全一致 · 否则会出现「顶栏年付364天 / 设置页月度订阅—」自相矛盾 BUG。

65. **员工继承老板套餐字段必须全套继承**(2026-05-11 · v17.1):`_build_user_info` 检测 `role=member` 查 owner 时 · 不能只继承 `plan` 一个字段 · 还要同时继承 `plan_expires_at` / `trial_expires_at` / `monthly_quota`。否则员工的设置页 / 顶栏跟老板对不齐(员工看到自己注册时的旧数据)。已在 SELECT 多列 + return dict 同步赋值实现。

66. **`admin_upgrade_user` 必须同步 `tenants.subscription_expires_at`**(2026-05-11 · v17.1):铁律 35 写「tenants 表无 plan / max_seats」 · 但 subscription_expires_at 是真存在的列(在 db.py 5659 建 tenant 时写入)· 之前 admin_upgrade_user 漏更新这个列 · 导致 tenant 表过期值永远停在注册时初始值。任何套餐升级 / 降级路径必须同时维护 `users.plan_expires_at` + `tenants.subscription_expires_at`。

67. **tenants 表无 `trial_expires_at` / `plan_expires_at` 列**(2026-05-11 · v17.1):这两个字段只在 users 表 · `get_tenant()` 返回的 dict **不要**引用 `tenant_info["trial_expires_at"]` 这种幽灵字段 · 否则代码误导(实际 always None 走 fallback 到 user 表)。tenants 表能用的过期字段只有 `subscription_expires_at`。

68. **服务器单独覆盖文件清单**(2026-05-11 · v17):有些文件不进 deploy.sh 主流程 · 必须 Zihao 手动 scp 覆盖。当前清单:`mrerp_xlsx_generator.py`(detail 行 product_code 真码注入需要)。新增此类文件时必须在 HANDOVER 显式标出 · 否则部署后功能缺失没人知道。

---

## 🆕 旧铁律清单(累计 58 条 · 见 v27.8.0 收尾时新增 51-58)

旧 1-43 见 v118.26.2.5 HANDOVER · 不变
44-50 不变(本窗口部分修正见下面)

44. **三层 ERP 对接架构永久并存**(2026-05-10):A 后端模拟 + C xlsx 兜底 + D 浏览器扩展 · 任何一层失败自动降级 · A 不是默认
45. **ERP 对接主页 UI 三件套**(2026-05-10):统计 + 连接器卡片 + 推送日志 · 缺一不可(留 v27.8.2 做 · MVP v27.8.1.0 不做)
46. **MR.ERP 反向工程 ✅ 100% 完成**(2026-05-10 本窗口):认证 = 单一 PHPSESSID cookie · 无 CSRF · 无签名 · 全 5 步 endpoint 实测通过
47. **v27.8 真正难点是映射 UI**(2026-05-10):OCR 名字 → MR.ERP code · 必做主数据缓存 + fuzzy match + 用户确认 + 推送预览(留 v27.8.2 做)
48. **真实可达性 60%/90% 不是 100%**(2026-05-10):首次 60% · 重复 90% · 失败必兜底 .xlsx
49. **后端到后端跳过浏览器 JS 校验**(2026-05-10):v27.8 直接 HTTP POST · 不走前端 · 浏览器抓的弹窗错误跟我们无关
50. **MR.ERP idmenu 决定子模块**(2026-05-10):371=现金销售(imparse 路径 · 4 sheet) · 370=赊销(impartran 路径 · 3 sheet) · 各模块 sheet 数 + 路径不同 · v27.8 客户端按 module dispatch

### 本窗口新增 51-58(2026-05-10)

51. **MR.ERP 路径分两套**:`impartran/`(交易类业务单据 · 销售/采购/收付款 import) ≠ `imparse/`(SE 现金销售 + 推测主数据类) ≠ `expartran/`(交易类导出) · 不是单一 endpoint · 同模块名可能跨路径
52. **idus 是 MR.ERP 内部用户 ID**(test01=15 · 不是 username):scrape 来源 = 任意业务页的 `<input type="hidden" name="idus" id="idus" value="N">` · 必须用 BeautifulSoup 解析(name 和 value 之间隔了 id 属性 · 严格正则会漏)
53. **idmenu ≠ selmenu**:idmenu = URL 路由 ID · selmenu = 业务子类型字典(118=ขายเชื่อ-รายได้ขายในประเทศ赊销国内销售)· 同 idmenu 可通过 ชื่อเมนู 下拉切 selmenu(import 和 export 共用同一字典)
54. **MR.ERP 完整 5 步流程铁律**(不可乱序):
    1. GET / 预热(必须 · PHP session 初始化)
    2. POST /login/checklogin.php(`txtusers/txtpasswords/btnsubmit=Submit` 字段名都是复数 · 带 Referer)
    3. GET /login/selectdb.php(选公司页 · 模拟用户流程)
    4. GET /login/mainmenu.php?comidyear=N&seldb=N(激活公司 + 真实判登录成功 · 被踢回 login = 失败)
    5. GET /impartran/formupload.php?idmenu=N(scrape idus)
    6. POST upload → POST formrdpc → POST importpc(实际推送 3 步 · 同 PHPSESSID)
55. **MR.ERP importpc.php 必须 multipart**(虽然字段全是文本)· 服务端不接 form-urlencoded · requests 用 `files=[(name, (None, value))]` 触发
56. **MR.ERP 上传不是 AJAX 是浏览器整页跳转**(uploadexcel.php POST → 浏览器跳到 formrdpc.php)· 但**后端代码不需要模拟跳转** · 直接顺序 POST 即可
57. **MR.ERP checklogin.php 不靠 r.url 判成功**(POST 后永远停在 checklogin.php 自己 · 即使成功也不 redirect)· 真实判定 = 看下一步 GET mainmenu 是否被踢回 login + 看 body 是否含 txtusers
58. **MR.ERP confirm 返回值约定**:数字字符串(如 "2") = 成功 · 表示新 row id · 非数字 = 错误信息(具体格式待 v27.8.2 故意失败 1 次抓样本)· 单号重复行为未确认(实测 690507-001 反复 confirm 都成功 · 可能允许重复)

---

## 当前已知小问题(2026-05-11 v17 / v17.1 更新)

**MR.ERP 主线**:
- v14d 整链路完美闭环 ✅ · Korn 0006 真实推送验证 ✅
- v15 批量上传 500 + plan +300 + admin 999→9999 + auto_push 默认开 ✅
- v16 score=1.0 零点击 + 0.7-0.97 中分 undo toast ✅
- v17 商品对照表 + detail 行真 product_code + 子串闸 fix ✅ **已部署 · 等用户测**
- v17.1 租户管理 6 bug hotfix ⏳ **待部署**
- **服务器需单独 scp 覆盖 `mrerp_xlsx_generator.py`**(detail 行 product_code 真码注入 · 不在 deploy.sh 范围 · 不覆盖则商品映射 v17 链路只生效到映射保存 · xlsx 仍写 `123` 占位)
- **完美匹配场景仍要点 modal 确认**(v16 已解 · 待复测)
- **批量推送缺**(v22 解):50 张要点 50 次
- **凭据失效场景没自动检测**(v20 解)
- **推送失败无自动 xlsx 降级**(v20 解)
- **多客户混合上传归属不准**(v18 智能归属解)
- **重复推送防护缺**(v22 解)
- **字段对照表 product subtab 未做**(v17 BACKLOG 写要做 · 实际未做 · 推到 v18 · 理由:99% 用户从 mini modal 走 · 不阻塞主路径 · 铁律 62 已锁定)

**v14d 实施偏离原 BACKLOG**(已锁定为铁律 62):内存缓存 5 分钟 + 按需拉 + mini modal 显示全部 + 智能推荐排前 · 优于原计划 erp_master_cache 24h + 测试连接预热 + top 3 fuzzy modal。

**v15 实施细节**(本窗口决策):
- plan 上限调整全档单调升:trial 15→30 / monthly 30→500 / yearly 50→800 / lifetime 100→1000 / **admin 999→9999**(铁律:admin >= lifetime · 不能更少)
- 大批量提示阈值 100 张:进度条 IIFE + beforeunload + 首次一次性 toast
- ERP 新建表单 auto_push 默认 true(不动老用户已关的状态)

**v16 实施细节**:
- 客户 mini modal 完美匹配零点击:`_fetchAndRender` 拿 auto_select_code → `_autoApplyPerfect` 静默保存 + onSelected 自动重推
- 中分 0.7-0.97 不弹完整 modal · 弹右下角 undo toast(深色底 + 进度条 · 3 秒倒计时 + [改一下] / [没问题])
- 列表 score 徽章:≥0.7 橙色「推荐」/ ≥0.45 浅黄「可能」
- 后端 `_normalize_buyer_name`(去 4 语公司后缀)+ `_match_buyer_score` + `_rank_customers_for_buyer`

**v16 边界 fix**(本窗口主动发现 · 留 v17 顺手修):
- v16 子串规则只判「buyer 包含 name 或 name 包含 buyer」就给 0.85 · 短串挂中长串假阳性(如 "Random XYZ Co" vs "XYZ Limited" 误推荐)
- v17 加占比闸:短串占长串 ≥ 0.5 才认 0.85 · 否则降级 SequenceMatcher
- 测试验证:Random XYZ Co vs XYZ Limited 从 0.85 降到 0.43(不再误推荐)· 完美匹配 1.0 不受影响

**v17 实施细节**:
- DB:`erp_product_mappings` 表(tenant_id / erp_type / item_name / item_name_norm / erp_code / erp_name) + 4 CRUD + `find_erp_product_mappings_batch`(批量预检用)
- `get_mrerp_mappings_bundle` 加 `products` key
- 后端 stkmas(idmenu=24)抓取 + 5 分钟缓存(走铁律 61 同样 showdata.php pattern)
- 4 endpoints:`GET /api/erp/mrerp/products?item_name=X` / `GET/POST/DELETE /api/erp/mappings/products` / `POST /api/erp/mrerp/products/check`(批量预检)
- 前端 `_pushOne` 顶部 hook `_checkProductsBeforePush` · 多 unmapped item 串行 `_runProductMappingFlow` 逐个弹 product mini modal
- `openMrerpPickProduct` 独立 IIFE(350+ 行 · 接 `{itemName, indexHint, totalHint, onSelected, onSkip, onCancel}`)· 完美匹配零点击短路 + 「第 i/n 个待配」进度提示 + 跳过 + 取消
- 服务器 `mrerp_xlsx_generator.py` 改:加 `_norm_product_name`(re sub 标点 + lowercase · 跟 db.py 一致) + `_build_product_lookup` + `_resolve_product_code` · `build_sales_credit_detail_rows` 循环外建 lookup 一次 · 内循环 O(1) 查 item.name 写入 row 的 `product_code`(找不到 None 下游 `or '123'` fallback)
- 4 语 i18n × 19 词条

**v17.1 实施细节**(用户截图报 + 主动深度排查 6 bug):
- Bug 1:`_build_user_info` 只读老 `users.expires_at` · 没读 `plan_expires_at` → 设置页有效期「—」
- Bug 2:前端 settings 页 plan 分支只覆盖老名 pro/team/firm/enterprise · 新名 monthly/yearly/lifetime 走兜底「月度订阅」
- Bug 3:员工继承老板时只继承 `plan` 字段 · 没继承 `plan_expires_at` / `trial_expires_at` / `monthly_quota` → 员工设置页跟老板对不齐
- Bug 4:`admin_upgrade_user` 漏更 `tenants.subscription_expires_at` → tenant 表过期永远停在注册值
- Bug 5:`_build_user_info` 读 `tenant_info["trial_expires_at"]` 幽灵字段(tenants 表无此列)
- Bug 6:`/api/me/plan` 跟 `_build_user_info` 字段不一致 SSoT 违反 · 修法是后者加 `plan_expires_at` / `plan_days_left` 对齐前者
- 新前端 4 语 × 5 词条(settings-sub-monthly / yearly / lifetime / settings-days-left / settings-lifetime-forever)
- 后续监控点:升级套餐后 顶栏 + 设置页 + 员工 设置页 三处显示是否完全一致

**非 MR.ERP**:
- v118.26.2.5 用户管理/租户连环 BUG 全修通过用户测试 ✅
- `/api/me/plan` 慢 2.5-3.4s(测试中心 api_slow 触发)· 加 5 分钟前端缓存 · 0.2 天 · P2
- `deploy.sh` 不复制 `VERSION` · 顺手补
- **A.1 Git 远程私库 push**(0.5 天)· **公测前必做**
- home.js 死代码 · 0.2 天 · P3
- 老的 `HANDOVER_v118_27_8_1_14e.md` 已过期 · 由 Zihao 删除(铁律 13)
- 新的 `HANDOVER_v118_27_8_1_17_1.md` 给下个窗口接 v18 用 · 必读
---

# 🎯 2026-05-21 会话 · v118.35.0.17 → v118.35.0.27（11 个版本 + 1 事故回滚）

**当前线上版本**: v118.35.0.27 · cache-bust 11835027 · Tag `v1.1.0-credits-stable` → HEAD

## 重大事件

### 1) v118.35.0.20 部署后全站超时事故（14 分钟内自愈）

- **触发**: v0.20 在每个 OCR 请求加 3 次 DB 查询（`is_user_billing_exempt` + `balance` + `pages_used`）
- **根因**: `db.SimpleConnectionPool(maxconn=5)` 太小 · 并发 OCR 把池打满 · 后续请求阻塞累积 → 全站 30+ 秒超时
- **回滚**: 14 分钟内 `git revert` + push · webhook 自动部署回 v0.19
- **修正**: v0.21
  - `maxconn` 5 → 30
  - 3 次独立 SELECT → 1 次 LEFT JOIN（`get_billing_status_combined`）
  - 扣费改 `asyncio.create_task + to_thread` fire-and-forget · 不阻塞 OCR 关键路径
  - `is_billing_exempt` 加 5 分钟进程内 LRU cache
- **铁律 15** 已在 v0.17 入 CLAUDE.md（删后端字段必须同步删 Pydantic response_model）

### 2) P0 商业漏洞修复 · Credits 计费业务闭环

- **漏洞**: 新注册账户余额 0 仍可无限免费用 OCR · 因为 cherry-pick v36 时只搭了基础设施 · 业务层（check/deduct/owner/state）注释里写"下版本拉"被遗忘
- **修复**: v0.21 完整接入 3 个 OCR 入口扣费 + 前置检查
  - `/api/ocr/recognize` · `/api/vat_excel/build` · `/api/recon/bank-v2/run`
  - 余额不足返 HTTP 402 + 友好 4 语提示
  - 删除硬编码 `SKIN_TEST_USER_ID` · 改 `users.is_billing_exempt` 单一数据源
- **价格规则**（Korn 拍板）:
  - PDF 前 200 张 ฿1.50/张 · 第 201 张起 ฿0.75/张 · 跨界自动拆段
  - Excel/CSV/Word 不走 OCR · 按字符 50 字符 = 1 satang（฿0.01）· 向上取整
- **白名单**: `users.is_billing_exempt = TRUE` · 数据库已标 `skin306152@gmail.com` + `mrerp@outlook.co.th`

### 3) Korn 用户银行流水 OCR 失败修复（v0.19）

- **触发**: `STATEMENT EXCEL.xlsx`（泰文 5 列 47 行）报 "Gemini returned invalid JSON after 2" + "BankStatementDocument schema 8 validation errors"
- **根因**: `bank_recon_v2._parse_bank_stmt_via_pipeline` 没有 xlsx 直读 fallback · 强制走 Gemini · 长泰文撞 token 限制
- **修复**: 加 `parse_bank_stmt_xlsx_direct`
  - 多语表头识别（zh/th/en/vi · 5 列 日期/描述/取款/存款/余额）
  - 期初余额识别（空日期+空金额 / "ยอดยกมา/brought forward/opening/期初" 关键词）
  - 日期 carry-forward（同日多笔的空日期行）
  - xlsx 优先直读 · 失败再降级到 Gemini
- **验证**: 4 场景全过（Korn xlsx / 中文表头 / 英文表头+期初 / 无表头 fallback / 表头不全 fallback）

## 基础设施变更

| 维度 | 改前 | 改后 |
|---|---|---|
| DB `maxconn` | 5 | **30** |
| uvicorn workers | 1 | **2**（failover）|
| `timeout-keep-alive` | 30s（默认） | **10s** |
| OCR 关键路径 DB 调用 | v0.20 加到 4 次 | **1 次**（合并查询） |
| 白名单 LRU cache | 无 | **5 分钟** |

## 新 DB 表 / 字段（v0.21 cherry-pick 落地）

- `tenant_credits` · 公司钱包余额
- `credit_transactions` · 充扣流水（type: topup/usage/adjustment）
- `monthly_page_usage` · 月用量统计（用于 PDF 分级）
- `topup_requests` · 充值申请（含 SlipOK 自动验证 + admin 手动审批）
- `users.is_billing_exempt` · 豁免标记
- `users.active_tenant_id` · 多公司切换

## 新文件

- `services/monitoring.py` · Gemini 调用统计 + DB 池 + OS 指标 ring buffer
- `services/task_queue.py` · 任务队列基础设施（内存版 · 接口契约 · 不接 OCR）
- `services/ocr/error_format.py` · OCR 错误翻译层（v0.19 加）

## Earn 后台监控扩展（v0.22 + v0.25 + v0.26 + v0.27）

成本追踪页底部新增 3 个 section + 12 个 KPI 卡 + CSV 导出:
1. 用户扣费 KPI（今日扣费 / 本月扣费 / 余额池总和 / 透支公司数）
2. 公司余额清单表（透支飘红 · 余额低橙色）
3. 系统监控 3 行 12 卡（Gemini RPM / 撞限流 / DB 池 / 内存 / CPU / 核数 / Worker / 队列 4 项）
4. Credits 扣费明细 CSV（UTF-8 BOM · Excel 直开）

## 重要决策

1. **新注册不给试用额度** · 必须充值才能用 · 白名单 2 邮箱豁免
2. **LINE 告警砍掉** · `@059oupmg` 已用于用户交互 · 不混用作运维告警 · 改 Earn 后台监控看
3. **Gemini 多 key 轮询取消** · Tier 1 单 key 1000 RPM 已足够 · 等真撞限流再升 Tier 2
4. **Redis 任务队列最小版** · 写接口契约 + Earn 监控展示 · 不接 OCR 核心 · 等真需要时再装 redis-server
5. **收入对账完整度复盘** · 实际 93/100（之前误判 0/100）· 5 endpoint + 完整 UI + 4 语 i18n + 3-sheet Excel 全在 · 真缺的只有 P0 金额容差（已修 ±฿0.01）

## 文档 · Tag

- **铁律 15** 已入 `CLAUDE.md/CLAUDE.md:245-265`（删后端字段必须同步删 Pydantic response_model）
- **Tag `v1.1.0-credits-stable`** → HEAD `5eb4bb4`（含今日所有改进的稳定版）
- 旧 tag `v1.0.0-credits-release` 保留 → `b742e14`（指 5 月初空架子版 · 历史快照）

## 遗留（明天 / 下次 / 看用户量）

| 优先级 | 任务 | 备注 |
|---|---|---|
| 🟡 P1 | Redis 真上线 · 装 redis-server · 接 OCR 入队 · 独立 consumer worker · systemd 加 unit | 单独部署窗口 · 风险高 · 用户量 ≥ 100+ 家时启动 |
| 🟢 P2 | 收入对账日期容差 + 客户名模糊匹配 | 业务体验改进 |
| 🟢 P2 | admin 后台 LINE 告警 · 用现有 `line_client.push_text` · 不混 `@059oupmg` | 等 Earn 决定要不要专门建告警 Bot |
| 🟢 P3 | 4 语切换全站巡检 · Playwright 自动跑一圈 | 工作量大 · 留独立窗口 |
| 🟢 P3 | 银行对账 CSV/DOCX 前端 placeholder 文案完善 | 后端已支持 · 缺前端文案 |

---

# 🆕 2026-05-21 第二会话总结（接得上下一窗口）

## 来源
用户委托另一个 AI 做只读体检 · 产出 2 份桌面文档:
- `D:\Users\Skin\Desktop\Pearnly_只读项目体检报告_2026-05-21.md`
- `D:\Users\Skin\Desktop\Pearnly_按优先级可执行任务清单_2026-05-21.md`

体检评分: 产品 8/10 · **工程结构 4/10** · 安全 5/10 · 测试 5/10 · 可维护性 4/10

## 本窗口做的 6 件事

### 1. 核实体检报告每条指控（先验证再修）
P0-01 指控 4 个端点 fail-open · 实测**只 1 个真有漏洞**（误报率 75%）。这是一个核实方法论 · 不要盲信体检结论 · 一定要 grep + read 验证。

### 2. 修完所有体检 P0（5 个 commit · 5 项全闭）
| ID | Commit | 内容 |
|---|---|---|
| P0-01 | `6226f10` | `/internal/deploy` fail-closed when GITHUB_WEBHOOK_SECRET 缺失 → 503 |
| P0-02 | `1972abb` | `/api/version` 公开诊断脱敏 → 拆出 `/api/admin/diagnostics/runtime` |
| P0-03 | `1972abb` | 全局异常 handler 客户端只返回 `{"detail":"server.internal_error"}` |
| P0-04 | `b5063d5` | CORS `["*"]` → `[pearnly.com, www.pearnly.com]` + env 覆盖 + dev 放 localhost |
| P0-05 | `1972abb` | `.env.example` 5 个变量 → 60+ 变量 12 分区 |

### 3. 加铁律 16（全档位 push 授权 C 档）
位置: `CLAUDE.md/CLAUDE.md:268-308`
内容: Claude 写完代码可直接 push · **保留 6 条红线必须问**（force-push / reset-hard / 30+ 文件 / db schema migration / 关键路径破坏 / no-verify）。Zihao 在 2026-05-21 选 C 档位。

### 4. 写最优执行清单（8 阶段路线）
位置: `CLAUDE.md/EXECUTION_PLAN.md`（新文件 · 243 行）· commit `bdef105`

**核心原则**: 永远先写测试守门 → 再拆代码 · 拆代码本身需要测试当安全网。

| 阶段 | 状态 | 内容 |
|---|---|---|
| 0 安全基线 | ✅ 完成 | P0-01~05 + 铁律 16 |
| **1 多租户保险** | 🟡 进行中（1/2）| Task 1.1 ✅ · Task 1.2 待启动 |
| 2 计费保险 | ⚪ | Credits contract tests |
| 3 CI 保险 | ⚪ | GitHub Actions + check_imports |
| 4 i18n + E2E | ⚪ | check_i18n + 第一个 Playwright smoke |
| 5 后端路由拆 | ⚪ | 抽 billing_router + admin_diagnostics_router |
| 6 DB 迁移规范 | ⚪ | ensure_* 盘点 + Alembic 设计 |
| 7 前端绞杀拆 | ⚪ | dashboard.js + billing.js |
| 8 治理收尾 | ⚪ | 文档导航 + 锁版本 + 静默吞错清理 |

### 5. 阶段 1 Task 1.1 完成: 多租户隔离矩阵
位置: `docs/architecture/tenant-access-matrix.md`（新文件 · 349 行）· commit `8dd2c9c`

13 张表完整的读/写/删隔离矩阵 + 风险 TOP 10 + 未验证 10 项。

### 6. **意外发现并修复 1 个 P0 真漏洞**（商业终结级）
`db.get_gl_vat_task(task_id)` 和 `db.get_bank_recon_v2_task(task_id)` 无任何权限校验 · `recon_routes.py` 4 个路由直接裸调返回 · 任何登录用户可枚举 `task_id` 拖走平台所有事务所的对账详情。

修复方案: DB 层 fail-safe（不在路由层补丁）
- 函数签名加 `user_id` 必传 + `tenant_id` 可选
- Dual-Key SQL: `WHERE id=%s AND (tenant_id=%s::uuid OR user_id=%s::uuid)`
- caller 不传 scope **物理拿不到 row**
- 跨 tenant 用户 → 404（与"任务不存在"同响应 · 防枚举侧信道）

涉及 6 处修改（commit `8dd2c9c`）:
- `db.py:8335` get_gl_vat_task
- `db.py:8534` get_bank_recon_v2_task
- `recon_routes.py:1080` GET /gl-vat/{id}
- `recon_routes.py:1111` GET /gl-vat/{id}/export
- `recon_routes.py:1464` GET /bank-v2/{id}
- `recon_routes.py:1511` GET /bank-v2/{id}/export

## 当前生产版本
- 前端 cache_bust: `11835027`（未变 · 今天没动 home.js）
- 最新 commit: `8dd2c9c`
- 部署状态: ✅ 全部已上线 + 验证过 401/404 行为

## 累积 commits（按时间）
- `08409c1` docs(release-notes + 铁律 16): 4 语对齐 + push 授权
- `6226f10` P0-01 internal/deploy fail-closed
- `1972abb` P0-02/03/05 version 脱敏 + 异常脱敏 + env 补全
- `b5063d5` P0-04 CORS 收紧
- `bdef105` docs(plan): EXECUTION_PLAN 8 阶段路线
- `8dd2c9c` **P0 越权读修复** + 多租户矩阵文档

---

# 🚀 下次启动一句话（明天进窗口先看这条）

> **状态**: 体检 P0 全闭 · 阶段 1 Task 1.1 已完成 · 下一步做 Task 1.2
> **第一句话**: 直接说"继续" → 我会读 `CLAUDE.md/EXECUTION_PLAN.md` 阶段 1 看板 → 启动 Task 1.2（多租户隔离 contract tests · 2-3 小时 · 不动业务代码 · 只加 `tests/unit/test_tenant_isolation_contract.py`）
> **蓝图已就绪**: `docs/architecture/tenant-access-matrix.md` 列了 13 张表的所有 list/get/delete 函数 · 直接用作测试清单
> **环境前提**: Task 1.2 需要 `pytest` 或 `unittest` 跑 · 本机 `passlib`/`psycopg2`/`xlrd` 缺失但**这次测试用 mock cursor 不连真 DB** · 不影响本地跑

## 下次窗口必读
1. `CLAUDE.md/EXECUTION_PLAN.md` · 全文 · 看进度看板 + 阶段 1 Task 1.2 描述
2. `docs/architecture/tenant-access-matrix.md` · §2 表级矩阵（13 张表函数清单）+ §4 风险 TOP 10
3. `CLAUDE.md/CLAUDE.md:268-308` · 铁律 16（push 授权 + 红线 6 条）

## 下次窗口禁止做
- ❌ 推倒重构 / 一次性拆完 home.js / db.py
- ❌ 在阶段 1+2 完成前碰目录拆分
- ❌ 改 `app.py` / `db.py` / `home.js` 新增功能（建立硬规矩 · 新功能必须独立文件）
- ❌ 不核实就修体检报告新指控（误报率 75% · 必须先 grep + read 验证）

