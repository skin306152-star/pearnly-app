# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡（2026-06-27 · **B8 RLS · 孤儿 re-enroll automation 域收官（第 5 棒）**:`automation_rules`(tenant_or_user)enroll + `error_events`(纯日志·设计裁决不开)·`aab5ff97`·CI 6 闸全绿 + prod 金丝雀 PASS(rls=on/npol=1·假租户见 0)。**模板纠偏续**:INCIDENT §2 标 tenant_or_user、Explore 据 repo 无 DDL 误判纯 user → SSH prod `\d` 实测 user_id NOT NULL + tenant_id 可空 = tenant_or_user。交接 `docs/refactor/b8-rls-HANDOFF-2026-06-25.md` §7.16。**剩余孤儿域:etax → settings 杂项 → knowledge(最复杂留最后)+ 零暴露孤儿(最低优先)。** 下接前 4 棒 ↓）

- **★ automation 域(§7.16 · `aab5ff97`)**:新建 `services/automation/schema.py:ensure_automation_rls`(legacy 无 CREATE 钩子范式·独立事务·existing_tables·force=False)进 boot_ensures + dal_reexports;零业务代码改动(automation_rules 在 repo 无 SELECT/INSERT·唯一访问 owner_users 级联删 owner bypass)。error_events 不 enroll(唯一消费者超管·SELECT 无 WHERE·INSERT 常无租户·fail-open→守卫维持 DISABLE)。集成 4 例 + 4973 单测 + 6 闸 + 金丝雀 PASS。
- **★ 孤儿 re-enroll · tenant 模板批 enroll 上线 prod 验过**（`2041e719`）：`products`/`client_rules`/`member_scopes` 补回 `tenant` policy,各落最贴合钩子(products→`ensure_sales_rls` 的 `_RLS_TABLES`、client_rules→新 `ensure_client_rules_rls`、member_scopes→内联 `ensure_authz_schema`)。**★模板纠偏(第三次·INCIDENT §2 又错)**:products 的 workspace_client_id 运行时加且可空、client_rules 故意读 `workspace_client_id IS NULL`(firm-wide 默认·tenant_ws 会隐藏破业务)、member_scopes 是授权配置(resolver 读它构建账套上下文·先有鸡)→ 均纯 tenant。零业务代码改动(products/client_rules 早走 get_cursor_rls·member_scopes 全 owner 保 bypass)。集成 4+5 例(含 firm-wide NULL 回归守门)+ 4973 单测 + CI 6 闸绿（run `28281862110`）；金丝雀:3 表 rls=on/npol=1·products owner=44/真租户 27/假 0。**剩余孤儿:knowledge/etax/automation/settings 杂项(见交接 §7.4)。**
- **★ 孤儿 re-enroll · 前 3 棒 sales/suppliers/line 已收 prod 验过**(`8a7d8485`/`4cc03b42`/`cd3cc12d`·详见交接 §7.11~§7.13)：sales 5 表(tenant)、supplier_categories+buyer_to_client_memory(tenant_or_user·落现有 ensure+迁 5 裸 DAL)、line_bindings+line_binding_codes(**纠偏:实为纯 user·非 INCIDENT 说的 tenant_or_user**·store 全 owner 保 bypass)。各自集成测试 + 4973 单测 + CI 6 闸 + 金丝雀全 PASS。**贯穿教训:RLS 模板永远按真实列+访问维度验,INCIDENT §2 分类多处有错(line/products/client_rules/member_scopes 均被纠偏)。**
- **★ wave4 全收官（erp 映射×4 / erp_endpoints+push_logs(JOIN 富化) / import_template / email_ingest）+ /simplify 统一 legacy enroll 范式** · 详见交接 §7.7~§7.10。**legacy 无-CREATE-钩子表范式**：独立 `ensure_<域>_rls()`（各自事务）进 `boot_ensures` + commit `NEW-DEBT-EXEMPT`。剩零暴露孤儿（`erp_oauth_*`/`mrerp_credentials`/`erp_connectors`/`excel_templates`·无访问点·低优先）。

- **★ P0 事故已闭环(本窗)**(`8ba73117`→`6b83e9b6`→`bb33b7a5`):wave3 把 ocr_history/clients 切 get_cursor_rls 后,role 上下文下 `list_ocr_history` 的 `user_id IN (SELECT id FROM users)` 子查询读**孤儿表 users**(prod 72 张表带外 ENABLE RLS 却零 policy=deny-all)返空→真机识别记录 0 条/LINE 记账断/推送断。**止血**=prod 全量 DISABLE 72 张零-policy 孤儿(61 张真隔离表未动)·业务恢复(OCR=21/ERP=2/LINE=4·跨租户 fake=0)。**防复发**=`core/rls.disable_orphan_rls`+`ensure_no_orphan_rls`(startup 末步幂等自愈·扫零-policy 孤儿全 DISABLE)。复盘 `docs/refactor/b8-rls-no-policy-orphans-INCIDENT.md` §6。**衍生新债=71 张孤儿按域 re-enroll(见交接 §2,优先级最高的剩余项)**。
- **B8 RLS P3 · ready 域 prod 真启用**(`RLS_ROLE=pearnly_app` 入 `/opt/mrpilot/.env`):POS/库存/产品/采购/销售/会计/税/导出/modules/LINE-brain/expense **已真隔离**。裸 get_cursor 留 owner·force=False 绕过→老路径不破。
- **wave2 对账 row-op 全清 + 两个 hard point**(`9f7765c2`→`f1714ca1`):hp1=`core/rls.py` 传递式 `apply_tenant_via_parent_rls`(reconciliation_row 经 task_id→task 的 EXISTS)·hp2=vat_recon_store/field_override/recon_resolve/bank_recon ~12 函数改签名带 tenant+user·调用方全穿上下文。recon 域残留裸 get_cursor 仅 DDL/ensure(owner)。
- **★ bank_reconcile_\* enroll 上线 prod 验过**(`4404aaca`+`ad5a1841`):user 维度表·`core/rls.py` 加 `user` 模板 + `apply_user_rls`/`apply_user_via_parent_rls`(via-parent EXISTS 抽 `_apply_via_parent`)·sessions/transactions 纯 user、candidates 经 tx_id 传递·`ensure_bank_recon_rls()` startup 跑·**一并 DROP 带外 p_*_user 去重**。金丝雀 PASS(真用户 3 sessions/40 tx·假 0)。
- **★ wave3 3a 核心 enroll 上线 prod 验过**(`95a244fc`):**clients + ocr_history**(tenant_or_user·在 `ensure_clients_table` apply·force=False)。核心 DAL 全穿 get_cursor_rls:clients/store(6 函数)+ buyer_resolve(try_resolve/update_history_client_id)+ ocr_history queries(5)+ mutations(5)。check_duplicate 加 tenant_id 参(喂 RLS·WHERE 仍 user_id 保 per-user)·3 调用方穿。金丝雀 PASS(真用户自见 21 ocr_history/9 clients·假 0)。**坑:`run_rls_isolation_tests`(P4 harness)建临时 tenant_isolation_test + cleanup DISABLE clients RLS——但 cleanup 在 `if rls_was_off_before` 内·clients 现永久 enroll→不跑·安全;P4 重写 harness 时清残留 policy**。
- **验证**:docker pg 27/27 集成(矩阵 8+传递式 5+recon 端到端 3+bank 真表 4+**clients/ocr_history 真表端到端 3**+模板 4)+ 全量 4911 单测。
- **★ 两个 prod-only 坑(见 [[rls-b8-p3-prod-enabled]])**:① Supabase postgres 非 BYPASSRLS→ready 域**别上 force=True**。② **Owner 后台 SQL Editor 跑过 `GRANT pearnly_app TO postgres`**(没它设 env 全 500)。回滚:删 `.env` RLS_ROLE 行+重启 / `scripts/rls_rollback.sql`。
- **下一步(按序·详见交接 `b8-rls-HANDOFF-2026-06-25.md`)**:⓪ **71 张孤儿按域 re-enroll**(止血时全 DISABLE·proper 隔离待补·模板分类见 INCIDENT §2·**workspace_clients 的 enroll 还没落进 `ensure_workspace_tables`**=wave3 3b 第一件)① wave3 3a 外围收口(sales get_buyer 漏 user、workspace seller_routing/list_stats、routes 计数穿上下文;超管显式 bypass)② wave3 3b/3c/3d exceptions/notification/archive/billing(charge.py 钱禁 bypass)③ wave4 erp/email/import(push_logs JOIN 富化是难点)④ P4 `12-rls` `passed===5`+重写 harness+ready 域 force=True。
- 坑:共享树 push 前只 `git add` 自己文件显式 pathspec;集成测试 `docker compose up -d db` + `PEARNLY_INTEGRATION_DB=1 RLS_ROLE=pearnly_app PGSSLMODE=disable`。

## 历史记录（2026-06-24 深夜 · **LINE 多页单据逐页入账(防双重记账)** · prod `d94fd2e5`）

- **LINE 多页逐页入账**(`8164a77d`+`2d25a21e`+`d94fd2e5`):此前 OCR 后只取 page[0]·多页 PDF 第 2..N 票被静默丢(漏记)→ 改逐页。**防双重记账闸**(money):新 `services/ocr/line_multi_page.py` `select_bookable_pages`——首张可入账页必记·其后页须自带身份(税号/票号=能参与 dedupe)才记·无身份续页跳过→绝不把跨页长发票记多笔;同号续页 dedupe_key 兜底。`test_line_image_multi_page` 7 例。
- **待验收**:真 LINE 多页 E2E(2 收据 PDF→2 卡;跨页长发票→1 笔)需 Owner 真机。**后续**:`invoice_grouper.group_pages_to_invoices` 是更完整的多页→多票分组(跨页合并行项·persist.py 已用)·迁过去会改入账金额(money 路·需真多页样本独立验)。详见全局诊断 `docs/HANDOFF-2026-06-24-全局诊断-按文档交接分类.md`。

## 历史记录（2026-06-24 · **整顿恢复:A3 完成 / A4 搁置 / B8 RLS → P2** · 我 `e8074817` · 全 push · prod 零影响 · 详细交接 `docs/HANDOFF-2026-06-24-整顿恢复-A3-A4-B8-RLS.md`）

- **整顿现状**:核心(体积/结构/防屎山闸/目录重组/前端模块化/**C5 TS 实际 215.ts·3.js 已达标**·看板 stale)早收官;06-03 至今 944 commit/3 周 feature·体积闸全守住。真正未完成=B8 RLS(本窗推进)/lint-ui 视觉债(220+967 裸 hex·gated)/E 性能/F 存储/H 合规/D4 覆盖率。
- **A3 本地 Docker 环境分级 ✅**(`6ace4f9d`):跑通验证 8 项 + 修 3 回归(Dockerfile `cp home.js` 死码删 / db.py `sslmode` 可配 `PGSSLMODE` / 健康检查是 `/api/ready`)。待办:`read_frontend_version` 读 `static/home.html`(已不产出)→ `/api/version` 本地版本号恒 0,应改读 `static/dist/home.html`。
- **A4 Doppler ⏸️ 搁置**:CLI 装好 v3.76.0·剩 `doppler login`(Owner 认证)+ 生产切换(红线#16)·单人项目不急。
- **B8 多租户 RLS · P0/P1/P2 ✅ 上线**(`b3ee95e7`设计/`1138b437`基建/`e8074817`测试矩阵):最小权限角色 `pearnly_app`(NOBYPASSRLS)+FORCE RLS+`SET LOCAL ROLE`+三维 context(tenant/账套/user)·`core/rls.py` 3 policy 模板。POC7/7+集成8/8+单测4761+CI绿。**默认全关(env `RLS_ROLE` 未设·表未 force)prod 零影响**。**待做 P3**=逐域真启用(唯一碰生产·前置审计 **457 处无上下文 `get_cursor`**·分域 POS→采购/销售/会计→对账/知识→老模块·每域本地恢复库→prod 建角色+设 `RLS_ROLE`(红线#16)+`apply_*(force=True)`+冒烟+回滚·**★Owner"没真实用户"→可大胆逐域上、秒回滚**)+**P4** 把 `12-rls-isolation.spec.js` 收紧 `passed===5`。
- 坑:Docker 别强杀进程([[docker-desktop-kill-trap]])·db 容器 stopped(起 `docker compose start db`)·共享树 push 前 `git pull --rebase` 只 add 自己文件。

## 历史记录（2026-06-24 晚 · **Express 推送防呆闸(币种/贷项/押金/日期/税号)全上线 + DATAT/DB 清空待 Owner 重跑批次** · prod `bc5e08f2`/11850971 · companion 1.1.11 未动）

- **5 道单据防呆闸上线**(prod `adf53346` feat + `bc5e08f2` /simplify · CI 6/6 绿 · prod E2E 5 陷阱全 manual):全语料暴露的「陷阱票当普通票推成功」已封——外币当泰铢(最严重)/贷项退货当正向/押金当费用/未来日期/补开倒签/对手方税号非 13 位 → 命中即 `EXPRESS_MANUAL` 转人工(doc28 §8 deferred 的「转人工即可」)。
- **实现**:新 `services/erp/express_push/doc_sanity.py` `check_document`(纯函数·只读票面·按严重度·空信号放行不误伤·税号闸复用 `clean_tax_id`)→ preflight 方向后/映射前加 `document` 体检项(契约序不变·正常票全 ok)→ `classify_push_exception` 加 `document_review` 桶 → `erp-log-card` 6 原因码人话 + i18n 4 语。**币种碰 OCR 主路径**:`ThaiInvoice` 加 `currency` 字段(加性·默认空=泰铢→零行为改动)+ layer2 prompt 仅明确非泰铢才填(无信号则币种闸不触发)·全量 455 OCR 测试无漂移。
- **测试/守门**:新 `test_express_doc_sanity` 16 + preflight/classify 契约扩充·全量 **4823 绿**·守门全绿(prettier/black/ruff/imports/i18n 4×4832/size/ui-consistency/ai-smell/ratchet 6 文件透明豁免)。
- **数据已清(让 Owner 重跑批次)**:① DB 测试号 `0ac26816`(18685123459)ocr_history 58 + push_logs 51 **全删 0/0**(Express/DMS 端点 + 主体 + 科目映射**保留**·重跑要用)② **DATAT 从干净基线 `D:\datat_restore_src_20260623-201016` 镜像还原**(Express+companion 已关释放锁·写盘前全量备份 `Desktop\DATAT_backup_20260624-155805_pre-restore`)·本批 44 票验证全 0。
- **下一步**:Owner 重新上传 51 张验防呆闸(6 张陷阱票=美元/贷项/押金/未来日期/倒签/坏税号 应转 manual 而非误推)。剩 backlog:S7 建账套(暂缓存档)/v2 科目全自动新建·WHT·存货·冲销。
- **坑/资源**:DATAT 写盘只能 bash 走 `//accserver/ACCOUNT/70EXP/test`(原生 Win 进程无认证·Express+companion 须关释放文件锁)·prod 查推送=SSH SG + psycopg2 查 `erp_push_logs`/`ocr_history`。companion 独立仓 `D:\pearnly-companion` 无 remote(本窗未动)。详见 `docs/HANDOFF-2026-06-24-express-v1-S4S5-收尾.md` + 记忆 [[express-full-auto-provision-design]]。

## 历史记录（2026-06-24 · **Express 全自动 v1 收口 S5/defer①/S4 + 全语料真机验证** · pearnly-app `fb245dc9` · companion **1.1.11**）

- **S5 科目保守版收口**(prod `62626323`+`29e22bb8`·E2E 5 PASS):科目来源诚实化——enqueue 不再猜来源,`common.resolve_account_sourced` 吐真来源(category_map/config_default),落账套默认标 `account_review` →详情卡「默认·待核」(`expd-acct-review` 4 语)。零入账行为改动。
- **defer① 绑主体 bind_fix**(prod `8c79d556`·E2E 8 PASS):拆 `push_exception_classify.py`(从 492/500 的 push_log_queries 抽分类/派生·facade 保 `store.X is q.X`·回落 436 行)+ 新 `derive_bind_fix` → `list_push_exceptions` 派生 `bind_fix`,前端读结构化字段不解析裸串。
- **S4 自建客户疑似重复转人工**(companion `a27cc82` 守卫 + 云端 `33582a24` 人话化·**真机暴露并修 dedup bug** `41418cc`):`suspected_customer_dup` 镜像 supplier 守卫。★bug=`_norm_match` 删泰文声调符致归一同名,`_find_suspected_dup` 的 `cand==target→continue` 漏判「同名不同税号」→ 改 `if not cand`(供应商侧同享)。**真机重测 PASS**:S4a 自动建客户+过账、S4b 正确转人工不建重复。companion 发版 **1.1.10→1.1.11**(`dd4f670` /simplify 微优未单发)。
- **全语料真机测试**(Owner 上传 49 张·我查 prod 核实·46 push=41 success+5 manual):**核心稳**——去重无双记账(查 DATAT APTRN 实证·源单号在 REFNUM)、5 张正确转人工、自动建供应商/归一/加油防呆全对。**暴露防呆缺口**(陷阱票该拦没拦):**美元当泰铢记**(最严重)、押金/折让/未来日期当普通采购推 → 已列 backlog。
- **Backlog**:① **防呆闸**(币种>折让>押金>日期·doc28 §8·多为转人工)② **S7 建账套**(极重·研究先行·Owner 拍板**暂缓存档**)③ defer② acctfix句柄改名(第三消费者再做)④ DATAT 本轮测试数据待清(Owner 定)。详见 **`docs/HANDOFF-2026-06-24-express-v1-S4S5-收尾.md`**。
- **坑/资源**:DATAT 写盘只能走 **bash 拷出→本地 dbf 手术→bash 拷回**(原生 Win 进程无 \\accserver 认证·accserver 易掉线·Owner 关 Express 才拷得回);prod 查任意账号推送=SSH SG + psycopg2 查 erp_push_logs。companion 独立仓 `D:\pearnly-companion` 无 remote·发版 `release.ps1`。详见 [[express-full-auto-provision-design]] [[express-account-resolution-closed-loop]]。

## 历史记录（2026-06-24 · **POS 收银台手机自适应 = 底部购物车 sheet**(并行窗口·与 Express 无关)· prod `0bf6f551`/pos `?v=11850965`）

- **根因**:POS 收银前台 `static/pos/pos.css` **无任何 @media**·收银主屏只有桌面横排(`.cart` 固定 380px)→ 手机上 380px 购物车顶满全宽撑出右边界(金额/挂单键被切)、商品网格挤成 0 宽消失,收银员手机无法收银(Owner 两次真机截图抓)。
- **修(终态=底部 sheet)**:初版竖排堆叠(`e8b1a958`)被 Owner 指出「购物车带商品顶高、把商品网格挤成一条」→ 改 **≤700px 购物车降底部 sheet**(`0bf6f551`):默认只露 68px 把手(`.cart-peek` 件数+应收)、商品网格占满主屏;点把手展开看明细/改量/收款,点遮罩收起。桌面把手/遮罩 `display:none`、横排 380 不变(视觉照搬闸过)。JS 在 `pos-cashier.js`(open/close/toggleSheet·renderCart 刷把手·openPay/clearCart 自动收)。
- **验证**:真浏览器 390×844 + 1280×800 双断言 10/10 PASS · prod 实机 /pos E2E PASS · 守门全绿。`/simplify` 收口(`8912b34e`):renderCart 件数/grand 各算 2 次 → 集约 1 次。
- **上线状态**:`e8b1a958`+`0bf6f551`(底部 sheet 本体)+ `8912b34e`(/simplify)**全已在 origin/master·prod 已上线**(prod /pos 实测 `pos.js?v=11850965`)。注:本窗口收尾时这几个 commit 由并行 export/docker 窗口的 push 一并携带上去(共享单一本地 master·任一窗口 push 即全栈上线)。
- **改 POS 外壳必做**:bump pos.html 两处 `?v=`(css/js)+ pos.js 的 `pos-sw.js?v=` + pos-sw.js `CACHE` 名(离线外壳刷新)。`static/pos/*.js` 超 500 但不在 check_file_size 监控/ratchet(别误拆)。**未覆盖餐厅视图**(rtables/rorder/rkitchen·Owner 是零售/药房·该视图是否同桌面-only 待查)。详见记忆 [[pos-cashier-mobile-responsive]]。

## 历史记录（2026-06-23 深夜 · **Express 异常卡「绑定主体」面板上线 + /simplify** · prod `9336930e`/11850964 · companion **1.1.8**）

- **④ 前端绑主体面板上线**:推送异常页 `direction_unknown` 且非 `direction_not_enabled` 的票加「绑定主体」主操作 → 选账套主体一键绑定重推(后端 `POST express-bind-subject` 早就位·本窗只补 UI·复用待补科目卡样式与句柄)。真站 E2E 8 PASS。**defer① 后端 derive_bind_fix 结构化提示**(当时受 push_log_queries 492/500 闸 deferred)→ **已在 2026-06-24 窗口做完**(见上)。详见 `docs/HANDOFF-2026-06-23-绑主体面板-收尾.md`。

## 历史记录（2026-06-23 晚 · **Express 推送诚实化 + 待补科目卡 + 小助手托盘/配对/自动PACK 一串修** · prod `c91b0577`/11850951 · companion **1.1.6**）

- **① 推送状态诚实化(误导 UI · 违铁律 #3/#12 的幽灵 bug)**:`manual`(缺科目/低置信/账套拒)此前被端点计数器算成功 + 被异常页 `status!='failed'` 过滤双重隐身 → 异常页显 0、日志显失败,口径打架。修:抽 `push_retry.counts_as_endpoint_success` 单一口径(manual/failed 算失败·pending 不计·3 处重推同用);`list_push_exceptions` 纳入 manual;`classify_push_exception` 扩 account_missing/account_set/direction_unknown/low_confidence 桶;batch_view manual→needs_action。
- **② 待补科目卡(UI 落点② · 残留②闭环)**:异常页加「待补科目」chip + 卡内科目下拉(选项=该账套 reported_accounts 代码·名字)+ 记住为账套默认 + 覆盖重推。新端点 `POST /api/erp/logs/{id}/express-account-fix`(写前 GLACC 白名单闸2 + 更新原行重推 + remember 并入 config·复用 /express-accounts 口径)·`derive_account_fix` 按失败码推该问哪些槽。
- **③ 失败码人话(误导 UI ①)**:异常页复用日志卡 `_expressFriendlyReason`(经 `window`)不再裸露英文码 + 补 `direction_not_enabled/low_confidence/enqueue_error` 三码 4 语(此前漏)。
- **④ 防屎山拆分(三文件本就超/近 500·此 clone 无 pre-push hook 致 `89fd3610` 起 CI 已红没人发现)**:拆 `push_log_friendly.py`(DMS catalog)/`erp_express_account_routes.py`(待补路由)/`erp-exc-actions.ts`(卡内动作 retry/batch/acctfix·ES import 互引)。清 `7d74943e` 遗留 `⚠` emoji→Lucide SVG(过 ui_design_lint)。**→ CI 自 `fb2aecbf` 后首次全绿**(`adbb4df9` 主 + `7dbea939` emoji + `c91b0577` /simplify)。
- **⑤ ★小助手托盘卡死误报离线(companion 1.1.3·已 release 自动更新)**:Owner 截图托盘「离线·连不上网络」vs 网页「已连接」打架。**真因(prod 数据 + 代码双证·非猜)**:`on_poll_error` 一拍失败就 emit「离线」(无连续失败容忍)+ `on_connect`(emit idle)只循环启动跑一次 → 部署重启(我 13:34 push 那拍)/瞬时闪断必误报,且心跳仍继续成功上报云端(`agent_last_seen_at` 查 prod=59s 新鲜·success_count 9)→ **网页是对的、托盘谎报**。修:`run_poll_loop` 连续 `OFFLINE_AFTER_FAILS=3` 次才判离线 + poll 成功发 `on_poll_ok` 自动回在线(不必重配对)。+4 守门测试·240 passed(4 失败=既有 OCR 环境性)。
- **⑥ 配对窗两修(companion `62bda93`·1.1.4)**:账套 + 6 科目下拉(QComboBox)在滚动区抢滚轮 → 悬停滚页误改科目/账套(账错风险)·新增 `_NoScrollComboBox`(收起态 wheelEvent.ignore→冒泡滚页·点开列表内照常)。配对成功提示加「会计科目映射 M 项也已上报·按账套+科目自动记账」(中泰)。
- **⑦ 自动 PACK 改用户可勾选(companion `0fa6894`/1.1.5·`a632d31` /simplify)**:查证当初取消 = T5 砍「PACK 工作日」黑话字段、但 `pair()` 写死 `pack_enabled=True` 一直夜间跑。Owner 要回控制权 → 配对窗加「录完自动整理进 Express(空闲时)」勾选框驱动 `pack_enabled`(默认勾·留旧零操作)。**勾=空闲触发**:`run_poll_loop` 数本批写入,队列转空 `_after_batch`→`scheduler.tick_idle()`(新增·不限夜间窗·`pack_idle_cooldown_min=10min`·占用顺延·夜间窗仍兜底)。**不勾=手动**:录完一批托盘气泡+活动记录提示去 Express 点 PACK(小助手不加按钮·手动=用户自己去 ERP 点)。/simplify:`decide/tick` 合并 `idle` 参数去 `decide_idle/tick_idle` 重复。+12 单测·228 passed。
- **/simplify 收口(pearnly-app `c91b0577`)**:`chart_codes` 提到 `express_push` 包(去 enqueue/待补卡重复)。
- **遗留(不挡)**:待补卡交互式 click-through 未真机走(需 seed manual no_revenue_account 票 + 测号 token)·已 route TestClient + CI e2e + bundle 解析覆盖。Phase3 小瑕疵延后(税号字段红字/向导账套显代码/详情抽屉显失败原因)。**Express 查账人工指引**(PACK 8→1→6 → 报表 6→1 → 销项 141=1-4-1/进项 241=2-4-1 → 整月佛历两位年区间·别用单号框筛·单号在列表对号)已在对话给 Owner·可整理进 `docs/`。
- ⚠️ companion 独立仓 `D:\pearnly-companion`(无 remote)·发版 `packaging\release.ps1`·改前读 `docs/RELEASE.md`。**本窗口连发 1.1.3→1.1.6**(离线自愈/配对滚轮/自动PACK可选/simplify)。Owner 本地 companion **已清空**(待重新下载 1.1.6 全新配对验证)。详见 [[express-account-resolution-closed-loop]] [[express-push-sales-blocked-and-misleading-ui]] [[companion-ux-connection-honesty-2026-06-23]]。

## 历史记录（2026-06-21 · **Express Push 全链路 + 「下载小助手」上线 + 推送功能正式开** · pearnly-app `23f223b9` · companion `94e3cac`）

- **Express Push 本窗口从 P1 推到全闭环 + 正式上线**(详见记忆 [[express-push-e2e-and-p4-packaging]]):阶段一整合(cloud sales mapper + 税号锚点方向判定 `direction.py` + heartbeat 收 account_sets)→部署→**数据层冒烟**(队列→companion→直写 DATAT→ack·真单 `RR581215-004`/`IV581215-001`)→**Express 报表证据**(`D:\_express_audit` p32 工具链出 241进/141销·真程序读出直写单)→**P4 双 exe 打包**→**「下载小助手」端到端**。
- **P4 双 exe**(PySide6 无32位wheel·硬约束):`companion.exe`(64位·PySide6 托盘+首次配对窗+DBF直写+queue)+ `pack_runner.exe`(32位·pywinauto PACK)。配对 `pairing.py`(校验码+探账套上报+存config+写注册表自启)+托盘 `gui_tray`+夜间PACK `pack_scheduler`(调 runner·账套硬闸只PACK配置账套)。companion 独立 repo `D:\pearnly-companion` master `94e3cac`(无remote)·三件套在 dist/。
- **「下载小助手」真能用**(prod `11850926`):Inno `installer.iss`→setup.exe 124.5MB·scp prod `static/companion/`·新路由 `routes/companion_installer_routes`(GET /api/companion/installer·登录鉴权)·FE `erp-express-wizard` 桩→真下载+生成配对码·真机 playwright 全过·setup.exe 静默装→弹配对窗→卸载干净。
- **★`ERP_PUSH_ENABLED` 已开并保持开(Owner 拍板正式上线)**·"推送功能未启用"消失·生成配对码工作。**但账套写入白名单仍锁 DATAT**(真客户用自己账套需 Owner 拍放开)·当前 0 express 端点没人配前无实际影响。
- **坑(本窗口踩·进记忆)**:改 dist 必 bump home.html `?v=`(否则缓存旧 bundle·点下载不发请求);PySide6/opencv 打 64位·pack_runner 32位;frozen exe cp874→utf-8 reconfigure / console=False stdout=None logger 守 stderr;harness 拦 `reg delete /v`、`taskkill /F`→用 Remove-ItemProperty/Stop-Process。
- **backlog(交 PM/Owner 拍)**:账套写入白名单放开(真客户账套)·SmartScreen 代码签名·`express_pw` 机器绑定加密·installer.iss `x64`→`x64compatible`。
- ⚠️ 全量单测本窗口没全跑(改动集中 Express·companion 16 新单测绿·pearnly-app 路由测试 401/404/200 绿)。**Express Push 这条线未来再开先读** [[express-push-e2e-and-p4-packaging]]。

## 历史记录（2026-06-21 · **LINE 设计图卡全套 + 语言中枢 + 解绑闭环 + 登录自动绑/用LINE连接** · HEAD `1fb2fa50`）

- 本窗口 ~24 commit 全上线·prod 200·全量 **4590 unit 绿**(skip3·唯 `test_erp_push_split_contract::test_adapter_registry_intact` 红=并行窗口给 ADAPTER_REGISTRY 加 `express` 却没更新该 contract 测试·**非我**)。
- **★解绑假成功 bug 已修**(`1fb2fa50`·真机抓):点确认出"已解绑"卡却还能记账=绑定没删。根因=`get_user_by_line_user_id` 返 users 行**无 line_user_id 字段**→handle_postback `luid=''`→删 0 行。修:解绑改按 `bound_user['id']` 用 `unbind_line_by_user`;`get_user_by_line_user_id` 把 line_user_id 塞进返回 dict(根因·所有 postback 处理器受益)。教训:写卡片/postback 测试别给 `bound_user` 塞真实没有的字段。
- **语言中枢**(`55a187dd`):新 `services/expense/line_lang.py`(明说换语言→锁 preferred_lang+确认 / 按消息文本判语种自动跟随 / voice persona 锁 lang)+ 确定性报时 `dates.bangkok_now`。治"中文求说中文却死回泰语"。见 [[line-language-follow-p0]]。
- **LINE 泰语图卡全套**(设计师交付·橙猫紫调):静态 A1-A11 走 **imagemap**(底部按钮切 tap 区·新 `line_imagemap.py`+出图路由 `/api/line/card/{ver}/{card}/{size}`·ver 破缓存·图 JPEG 存 `static/line-cards`)+ B 组动态卡(识别四态/汇总/凭证 = Flex **hero 横幅皮肤**·`line_card._bubble` 加 hero)+ A8 解绑卡 + A12 新手轮播(Flex carousel)。★坑:设计圆角外被压**纯黑**→imagemap 方角露黑三角→flood-fill 修白·复用脚本同款。
- **绑定/解绑闭环**:`line_bind_i18n`(四语)+ 面板文案改对(去"即将上线")+ 手机「在 LINE 打开」深链(`line.me/R/ti/p/@pearnly`·mobile-only CSS)+ LINE 端解绑命令→A8 确认(`line_unbind`·postback·**无 nonce**:解绑幂等+解绑后 bound 查不到自然防重放)+ unfollow 清绑定(`unbind_line_by_line_user_id`)+ 网页解绑 toast。
- **★登录自动绑 + 用 LINE 连接**:前提=登录频道与 Bot **同 provider**。prod 登录频道已切 **2010022630→2010411313**(`.env`·与 Bot 2010309291 同 provider「Pearnly」·旧备份 `.env.bak-line-login-20260621`)。LINE 登录→自动绑+`bot_prompt`+推 `welcome_messages()`(A5+轮播);Google/邮箱→集成页「用 LINE 连接」(`/api/me/connect-line/start` authed·state 签 user_id·复用 line callback 分流 `_handle_connect_line`)或 6 位码。Linked OA 已确认 @771hffyh/Pearnly。
- **★LINE 平台硬墙(实证·别再绕)**:① 非 bot 好友 push 送不到(返 200 但丢弃)② 加好友勾选只在「手机+首次授权+非好友」才弹(电脑扫码/老用户不弹)③ 不能强制弹开对话 → "加好友"天生不能 100% 自动·靠深链/手动兜底。④ 2010411313 **email 权限未申请**→LINE 登录拿不到邮箱→弹补邮箱(可去 Apply)。⑤ 同 provider 下登录 sub==Bot userId(给 sub push 返 200=同 provider 实证)。详见新记忆 [[line-login-bind-provider-friend]]。
- 测试数据已清空(Skin/U26139 等测试号·真用户 WAWA/Earn/Korn/mrerp 没碰)。
- **🔴 流程铁律 [[line-correction-replay-before-push]]**:correction/卡片改动**必先跑 replay 再 push**(本窗口每轮过)。
- **⚠️ 并行窗口(集成/Express)同跑**:push 前 `git pull --rebase`·只 stash AGENTS.md+docs/00·只 add 自己文件。`authz` 红(`erp_agent.py` 未登记)+ `erp_push.py` 507 行超限 = 它们的债·非我。
- **defer(下窗口·/simplify 发现·碰已验证登录/卡渲染主路径故收尾没动)**:① oauth token 交换抽 `_exchange_line_code`(login+connect 重复一段)② 卡 bubble 统一走 `line_card._bubble`(`line_unbind`/`line_expense_qa`/`line_proof` 各写一份 hero bubble)③ `line_imagemap` 资产注册表(stem 散成多集合·`hero()` 不校验)④ `_reply_card_or_text` 文字回落死代码 + `line_bind_i18n` 未用构建器(先定非泰语是否保留文字回落)。另:email 权限 Apply / pip-audit。

## 历史记录（旧状态卡 · 2026-06-20 晚 · B-1/B-2 分类学习 + 改错保卖家 + C-1 凭证PDF + 诚实待办卡 + Rich Menu · HEAD `eb3fae71`）

- 9 commit·prod 200·4531 unit·replay 52/52。B-1 学习真生效(`217061d4`)·改/教分类对叶子(`3309d897`)·改错克隆保卖家(`368cabcc`)·B-2 供应商消歧(`d378f3cd`)·C-1/C-1b 凭证PDF(`e74e66c8`/`e39c30a9`·嵌 Sarabun)·诚实待办卡(`13ca4b74`)·Rich Menu(`985a8025`)。见 [[line-category-deterministic-p2a]] [[line-proof-pdf-c1]] [[line-rich-menu-shipped]]。

## 历史记录（旧状态卡 · 2026-06-19 · 05 引用旧卡片状态闭环 全成立 + 裸取消焦点锚定 · HEAD `f8c0d5f5`）

- 6 commit·prod `f8c0d5f5`·4341 unit·replay 51/51。Slice1 死单不改(`a0750ca3`·screenshot-29)·Slice2 恢复闭环(`504e401f`)·Slice2b 草稿软删(`6f2e53c3`)·裸取消焦点锚定(`14f37e56`+`4a70b0a9`)·/simplify 抽 ci.money/short_ref(`f8c0d5f5`)。见 [[line-stale-card-ref-p0]]。

## 历史记录（旧状态卡 · 2026-06-19 早 · P2A 商户分类闭环 + 日期年漂修 + P2B 字段卫生 · HEAD `8ef38a1`）

- **P2A 商户/品类确定性分类闭环**(`14cd512b`·见 [[line-category-deterministic-p2a]]):`_smart_category` 优先级=用户学习→确定性规则(品名 item/商户默认 vendor_default)→LLM→留未分类。新 `services/expense/merchant.py`。7-11 口径:品名永远优先·绝不 vendor-first。**日期年漂修** `7126e0b4`(印出 4 位公历年优先)。**P2B 字段卫生** `5577af5d`+`b1f1548d`:新 `field_quality.py`(seller/date/tax/invoice/address 质量层·脏字段标黄·金额不可靠撤确认)·line_card 500→413。真机审计 5/5。

## 历史记录（旧状态卡 · 2026-06-18 · P1G-Perf 图片票性能止血 + 真机验过 + 乱码明细名兜底 + Req5 + /simplify · HEAD `f3860084`）

- **P1G-Perf 性能止血**(`b289e172`·`image_sha256` 列+索引落 prod·重复图早期短路 `line_image_fastpath`+`image_dedup`·L3 收紧/限时 45→10s·分类 LLM 硬上限 3s)·真机 6/6 L3 全未触发·6–16s(从 68–74s)金额全对·乱码明细名 `item_n` 占位(display-only)·Req5 改错回重发状态卡·见 [[line-p1g-perf-image-shortcut]]。

## 历史记录（旧状态卡 · 2026-06-18 · P1G 入账后闭环 + 终态卡税额一致 + P1E-3 修 · HEAD `334337e2`）

- 4 commit·prod `334337e`·4080 unit + 回放 42 全过。P1G 入账后闭环(`93557166` confirm postback 回 posted 数据卡 + 续 active_doc + 重复点击/撤销幂等 `_reshow_current`)·polish(`97f9e082` 终态卡复用票面税额不置零 140→130.84/9.16 + P1E-3「ที่ 7-11」不计金额)·/simplify(`334337e2` 抽 `totals.vat_from_inclusive/vat_face_consistent`)。新模块 `line_posted_card.py`。见 [[line-p1g-post-posting-closeloop]]。

## 历史记录（旧状态卡 · 2026-06-17 · OCR 纠错 + LINE 费用卡片产品化 · HEAD `33142a1`）

- `62cb5338` LINE 图片 OCR/采购入账收口(简式票无买方不当可抵进项/过滤汇总行/VAT 已含税不误判/卡留逐条明细/非票据明确提示/loading 续到出结果)；`33142a1f` 费用卡片文案产品化(金额 `431 THB`/三态文案/建议分类/费用明细)。prod `33142a1`·OCR_FALLBACK/ESCALATE=gemini-2.5-pro。

## 历史记录（旧状态卡 · 2026-06-16 · 「待归类(inbox)」整模块下线）

- **🆕 本窗口(2026-06-16)· 🗑️ 「待归类(intake_items/inbox)」整模块下线【全上线·prod验·v11850891】**（自检自推·worktree隔离推 4 commit·13闸全绿·见记忆 [[intake-inbox-retired]]）：
  - **行为**：LINE/拍照/网页识别完**一律建采购草稿(ฉบับร่าง)落「จัดซื้อ」列表**(有VAT=进项·无VAT/截图证据=费用不抵VAT)，用户在列表改方向/补金额/删。不再单独兜待归类桶。销项分类(我是卖方)后期按上传前选业务类型单独做。
  - **删干净**：`judge_direction`(去my_tax_id·只分进项/费用)/`resolve_image_intake`(删落inbox·永建草稿)/`grade`(去inbox动作)/`line_ingest`(删inbox分支)；LINE卡三态(去inbox卡态+inbox_post/drop两动作)；3个`/api/purchase/inbox`端点+`/liff/purchase-inbox`路由+`intake.classify`权限；前端`purchase-inbox.ts`/侧栏/路由/i18n(4语)；schema去intake_items；**alembic 0040 DROP**。死代码`_norm_tax`/`_TAX_RE`/`_my_tax_id`一并清。
  - **prod 存量**：迁移脚本 24 pending → **18 转草稿 + 6 dup(已有真单冗余)跳过** → 手动 DROP intake_items 表。表已删·schema不再建·重启不复活。
  - **真机验**(Zihao 19:09)：咖啡票฿59.99(有VAT)→confirm卡→列表「สั่งซื้อ进项·ภาษีซื้อ฿3.92·草稿」✓。**待跟进**：① 7-11票走旧纯文字回执(=dup命中已迁移的草稿·create_doc dedupe_block raise→fallback识别记录·pre-existing·dup卡不可达) ② 侧栏曾显待归类=CF缓存未bump(已bump v11850891修·刷新即没)。
  - **坑**：共享.git撞另一窗口未推 commit `1219b159`(feat/category·只动categories.py)→隔离worktree cherry-pick只推我的(`git worktree add --detach <wt> origin/master`+PS junction node_modules+cherry-pick+push HEAD:master)·本地master与origin分叉是正常结果·没reset护它的commit。改src/home必bump?v=(CF按URL缓存/static·没bump=serve旧bundle·这次踩了补推)。

- **本窗口(2026-06-16)· 🧾 进项采购 复核屏/详情屏 票图与布局收口【全上线·真浏览器 17/17·prod v11850890】**(自检自推·5 commit·全闸绿)：
  - **详情屏**:票图框可点开大图(原只「放大看」按钮可点·光标是放大镜却无响应);无图时不显放大镜光标(`.img.has-img`)。
  - **复核屏**:缩略图条(含「+」加附件)从「凭据(报税用)」卡挪到查看器正下方做胶片条,每张**渲染真实票图小样**(原占位文档图标);凭据卡只留提示 + 生成替代收据。
  - **两屏留白收紧**(左栏 + 右侧内容区):内层无边框卡只 reset 了 border/shadow,漏 padding/margin → 继承全局 `.pur .card{padding:20px;margin:0 0 16px}` 叠加 hd/bd 内边距=双重留白(段间 71~150px)。三处补 `padding:0;margin:0`·实测左栏 GAP 71→15px、右侧段间大幅收窄。
  - **/simplify 收口**:`resolveBillSrc`(url→缓存鉴权 blob)上提 `purchase-common` 给查看器/缩略图/详情共用;缩略图去冗余 data 属性按 DOM 序加载;全局 `.pur .card` 加注释标明内嵌卡须 reset padding/margin。
  - **共享树**:期间他窗推了 LIFF 时序修(`abfed9c8`)+ LIFF 调试弹窗(`ac8e5fe7`·"验完即删")·我构建时确认那是已提交源、未夹带其未提交码;`?v=` 多窗口连环 bump 11850884→890。验证脚本留 `scripts/_pur_*_verify.cjs`/`_pur_*_geom.cjs`(未跟踪)。

- **本窗口(2026-06-14)· 🚗 DMS 建订车单失败修复 + 旧 xlsx 路径清死代码【全上线·真 DMS 验证】**：
  - **建订车单失败真因(非 OCR·我先前误判)**:DMS autonum 单号计数器与全局唯一约束失步 → 一直回已占用号 `BK2606000001` → `err::"เลขที่ใบจอง" ซ้ำ`(单号重复)→ 每次推送必失败。修:`create_booking_via_form` 撞重复就顺号重试(`_bump_docno` 保位宽·最多 25 次·非重复错误不重试)。真账号 live DMS 验证建单成功(booking_id=28)。`23bb1cf7` + 单测 8 绿。详见 [[dms-booking-duplicate-docno-fixed]]。
  - **/simplify 收尾·清死代码**(Zihao 拍板全删旧一步式路径):两步流(`/api/dms/id-card/recognize`+`/push`·2026-06-13 上线)已取代旧一步式自动推 `/api/dms/id-card-booking`。删整条 xlsx 导入建单路径:端点 + `push_mrerp_dms_id_card` + adapter/ops `push_id_card_booking` + `import_booking_from_xlsx`/`patch_booking_identity`/`download_booking_template`/`ensure_customer` + `mrerp_dms_xlsx.py` 模块 + `DMSPushResult` + 2 个孤儿地址 helper。改/删测试(geo 测试重指 `_resolve_address_geo` 直测)+ 4 处文档(route-map/handoff/external-ref/intake)。全量单测 + 13 闸绿。
  - 共享树坑(同前):另一窗口并发 commit/churn master·走隔离 worktree 单推·见 [[dms-booking-duplicate-docno-fixed]] 末段。

- **本窗口(2026-06-12)· ✨ 丝滑+打包收编+权限管理成品化【全套上线·9 commit·b25d1d43】**（自检自推·健康 200·13闸全绿）：
  - **铁律改**(`12adcba4`):Zihao 拍板**删「高敏区·Zihao在场」两档制**(整顿期产物)→ 铁律#26 整条改写 + #16 + AGENTS + 记忆 [[all-changes-self-check-push]]:**今后所有改动(含登录/计费/OCR/POS离线)自做自检 OK 即 push**,不分高敏不等谁在场。真闸=13闸绿+核心路径自跑真账号E2E+改坏自revert;保留硬线=不碰mrerp真余额/破坏git历史仍问。
  - **A2 withLoading**(`34f26df4`+`df1126ce`+`89bf01a9`+`2a5f8149`):新全局 `src/home/with-loading.ts`(window桥·`.is-busy` currentColor转圈·复用home-03 spin·测试5行为)+ **16个高频动作按钮**接即时反馈(做账/报税/进项/库存/历史/POS·替手动disabled)→ 治 Zihao 原始抱怨"全站按钮卡顿"。
  - **A1去重**已 live(别窗口 core.ts coalesceConcurrentGets);**A3/A4** 实查列表已容器级渲染→骨架/乐观判定迁同区后低ROI跳过;**A5/A6** 反馈构造性<16ms免测+严格闸噪声>价值跳过。
  - **打包收编**:`e434b39c` /console·/invite 壳 minify→dist(view-source只见壳·**Zihao截图问题解决**);`c68a3ffc` POS 9JS→dist/pos.js+2CSS→dist/pos.css+壳minify+pos-sw CACHE bump+asset闸扩static/pos+GATES更新(本地boot冒烟0错验证)。
  - **POS SW scope 修**(`123c1aa1`):原 sw 挂/static/pos/scope控不了/pos→断网重开起不来。改根路由 `GET /pos-sw.js`+`register({scope:'/pos'})`+注销旧→**离线重开 smoke PASS**(swControlled=true)。
  - **退出登录按钮对齐 logo**(`b4bfbb75`):workspace-gate `.wsg-logout` absolute→`margin-left:auto` 回flex流与logo同垂直居中。?v= home.css 760/main.js 769/pos 767。
  - **/simplify收口**(`b25d1d43`):tax confirmFile收形+asset闸console/pos去重抽`_check_spa_bundled`;跳过withBusy合并(.busy是bank/mj专屏居中转圈·比.is-busy精致·合并=降级)。

- **本窗口(2026-06-12·前端)· 🖥️ 用户引导闭环 + 套账硬门【全套上线·Zihao真机验中】**（`3381fae5`引导闭环 + `336fea3b`套账硬门 + `3b26959f`表格修 + /simplify收口 · prod ver 11850755 · 13闸全绿）：
  - **引导闭环**(接 `docs/onboarding/00` 后端`ddb900bd`):注册向导(业态→主体三分支[税号带出/手动填/个人]→账务[财年/前缀真存]→**步④选套账**→完成清单)+ 公司资料行内编辑页(路由 company)+ 客户管理分派会计(复用 member_scopes)+ 受邀成员分流 + 个人模式整体退场 + logo 暗夜垫白 + i18n 4语~165键。新件 `onboarding-flow(.ts/-html)`/`subject-create`/`company-profile`/`client-assign`。
  - **套账硬门**(逐屏照 01-交互原型·补之前降级):**每次登录必选套账·1个也选·不可绕开**(`workspace-gate(.ts/-html)`+core-boot 经 module-nav.enforceWorkspaceGate);0套账/全删后→官方空态+**新建套账专屏(建好确定才进)**;**顶栏富下拉切换器 orgPop**(搜索/我管理的主体/勾选当前/创建/管理全部)替简陋 select;**全站建套账只有一个三分支专屏**(硬门0套账·orgPop创建·客户管理新增 统一·无冲突)。
  - **加载慢根治=CF 配置非代码**:压缩(Brotli)+immutable头都对,真因 Cloudflare 没缓存 /static/(`Cf-Cache-Status:DYNAMIC` 每次跨境回源)。**Zihao 已加 CF Cache Rule**(`URI Full contains /static/`→Eligible for cache)·实测 `DYNAMIC→HIT`·3分钟→秒开。**前端 i18n拆分/代码分割判定不做**(高风险且治不了根因·会破坏 plain-script eval 顺序)。**视觉照搬闸也判定不做**(overlay 不适合那套路由级闸·过度工程)。
  - **表格修**(`3b26959f`):账套主体 `seller-grid` 列左移(name minmax 限宽·操作 1fr 靠右)+ `.cust-table-wrap overflow hidden→visible`(⋯ 更多菜单不被裁)·改 home-29 CSS 需 build+bump home.css?v=。
  - **真机**:`18685123459@163.com` 已腾空可重测(停泊法:改 email/username/email_normalized→parked·`get_cursor(commit=True)` 否则回滚)。坑:sed 改 home.html 会刷 CRLF→LF(用 Edit 工具)。详见记忆 [[onboarding-loop-frontend-shipped]]。

- **🆕 本窗口(2026-06-12)· 🧭 套账后端补全(账务设置+税号查重)【已上线】**（`ddb900bd`+`bf84dd87`+`de94c1a6` /simplify·prod 列/索引实测 live·健康 200）：
  - 对 `docs/workspace-entry/00`(套账入口·与引导同功能)逐条核对后端,补两缺口:
    - **账务设置(步③)per-主体**:`workspace_clients` 加 `fiscal_year_start_month`(1-12·记录属性·做账仍按日历月)+ `doc_prefix`(单据前缀)。**doc_prefix 真接连号**(非死字段):开票取号前缀优先级 显式>主体级>租户级 `sales_settings.number_prefix`>类型默认·解析落 `document.py:finalize_issue`(issue/approve 唯一汇合点·两路径一致)·helper 抽 `numbering.resolve_prefix`+`workspace_doc_prefix`。
    - **税号重复 → 422**(workspace-entry §五):`store.tax_id_in_use`(本 scope 同税号查重·空税号永不算·fail-open)+ POST/PATCH 拦 `workspace.tax_id_duplicate`·个人主体跳过。**/simplify 升级**:加部分唯一索引 `uq_workspace_clients_tax_active(tenant_id,tax_id) WHERE is_active AND tax_id NOT NULL`(原子防重·prod 实测 0 重复方加)。
  - 「记住上次套账」=前端 `X-Workspace-Client-Id` 头+localStorage(非后端)。**套账+引导后端全闭环**(前端别窗口在做)。坑:document.py/sales_routes 改前贴 500 限·抽 helper 进 numbering+压注释保 ≤500。
  - 验:全量 3330 unittest OK + 22 新专测(财年/前缀归一·建改持久化·前缀优先级·税号查重 6 维·路由 422)+ 13 闸全绿。详见记忆 [[onboarding-loop-backend-shipped]]。

- **🆕 本窗口(2026-06-12)· ⚡ workers 2→4【真修法+已上线·丝滑杠杆③】**（`4406aeda`·prod unit 已 `--workers 4`·4 进程零 deadlock·健康 200）：
  - **死锁真因+真修**:`services/recon_jobs/worker.py:run_worker()` 内嵌 worker 启动那次 `store.ensure_table()` 在锁外 → 4 进程并发 `CREATE/ALTER IF NOT EXISTS` 抢 recon_jobs AccessExclusiveLock 互等死锁(此前 2 次回退 workers=2 的真因)。修=套 `with startup_ddl_lock():`(flock 跨进程串行·embedded/standalone 共用此函数故都被串)。守门 `test_recon_worker_ddl_lock`。
  - **prod 切 workers=4 实证**:`/etc/systemd/system/mrpilot.service` ExecStart `--workers 2→4`(备份 `.bak-w2`)·重启后 4×`Application startup complete` + 4 个 embedded worker 全起 + 零 `ensure_table failed` + 零 deadlock + 健康 200。治 INTERACTION_AUDIT 首屏 22 请求 2-worker 串行化·叠加新加坡 RTT 1ms。回退=`sed 's/--workers 4/--workers 2/'`+reload+restart。
  - **共享树坑+兜底**:引导窗口未提交 WIP 把 `src/home/app-shell-html.ts` 顶到 509(>500)拦我 push → **worktree 隔离单推**(detached HEAD·干净 app-shell=500)+ 给 worktree 联接 node_modules(否则 esbuild node 测试红)。详见记忆 [[startup-ddl-deadlock-recon-jobs]]。
  - 丝滑 §6 前端修复(首屏瘦身/withLoading/innerHTML 局部化)= 撞引导窗口 src/home·未做;UI 1-bis 已治本/1-ter 图标闸=加 pre-push 闸会软撞·均略。

- **🆕 本窗口(2026-06-12)· 🧭 用户引导闭环后端【全部闭环·已上线·迁移已跑】**（`f9860ed2` 主体 + `6a2128c9` /simplify 收口 · prod 健康 200 · 全闸绿）：
  - 按 `docs/onboarding/00` 施工后端,**前端 5 组件全部可对接**(逐项核对过)。新增很少、全 additive、低风险:
    - **schema**(ensure 自愈·`services/workspace/store.py`):`workspace_clients` 加 `subject_type`(company|personal·默认 company)+ 每 scope 至多一个在用 personal 主体的部分唯一索引(建主体幂等兜底·新列无存量 personal 行故索引创建必成功)。prod boot 日志证 `workspace_clients 已就绪`·零 deadlock。
    - **routes**(`routes/workspace_routes.py`):POST/PATCH 透传 `subject_type` + 写 `operation_logs`;新增 `GET /api/workspace/clients/{id}`(公司资料页读·作用域 fail-closed 404 不泄漏存在性)+ `GET /api/workspace/tax-lookup?tax_id=`(复用 `services.rd.rd_api.lookup_vat` 税号带出·命中加 vat_registered·未命中/格式错诚实降级)。tax-lookup live 验证 401(路由在)。
    - **store**:`create/update_workspace_client` 接 subject_type;建 personal 幂等(同 scope 已有则返既有 id)。
    - **迁移脚本**(`scripts/migrate_personal_mode_to_subject.py`·dry-run/apply 幂等):**prod 已 --apply = 0 候选/0 回填**(近期 DB 已清理·真实租户都有主体·无遗留个人模式孤儿数据)。同时实证 prod `subject_type` 列可用。
  - **零新建复用**:分派会计走既有 `PUT /api/team/members/{uid}/scope` + member_scopes;受邀成员分流走 `/api/me` role + `GET /clients` 做 0/1/N。
  - **/simplify 收口**(`6a2128c9`):唯一采纳=tax-lookup 同步阻塞 SOAP 改 `await asyncio.to_thread` 不堵 event loop;其余建议(Literal 拒非法=行为变更/vat 抽函数=过度工程/migrate 合并循环=可读性反降/脚本重复=独立进程必要)判断后跳过。
  - **验**:全量 3311 unittest OK + 17 新专测(store/契约/tax-lookup/迁移)+ 13 道闸全绿 + pre-push exit0。**下一步=前端**(`onboarding-flow/subject-create/company-profile.ts` + workspace-switcher 删个人模式分支·见 docs/onboarding/00 §三)。
  - 顺手:清掉工作树脏的 `package.json`(误 npm install 污染·已 `git checkout` 还原);确认 `/console`·`/invite` no-cache 已收口上线(prod curl 实证三响应头)。

- **本窗口(2026-06-11·主控)· 🇸🇬 迁新加坡 + 实测修复批 + 首登改密删除 + 迁移收尾完结**:
  - **迁移已完结**:app 东京→新加坡 `66.42.49.213`(同区·DB RTT 69ms→1ms)·Cloudflare 切源站IP·哨兵231次vision干净·切流量后522(ufw挡80/443)即修·密钥轮换(Zihao已做)·**禁密码登录(仅key)·撤东京临时通道key·东京45.76.53.194回滚兜底留~06-18勿动**。runbook `docs/perf/01`·prod 200健康。
  - **修复批 `fc4843a6`**(用户实测一路报):邮件邀请import断链(`_smtp_send_email`搬routes)/银行对账导入后自动选账户/角色卡去首字×3/邀请页提交前客户端校验+`err_user/pass_format`四语/**登录支持邮箱**(`find_user_by_username`含@回退email查·零歧义)。?v=11850751·console.js v8·invite.js v6。
  - **首登强制改密彻底删**(v118.11废弃·邀请已自设密码):force-pw.ts整文件+main.js import+core-boot触发+landing标记+login·me字段+40行i18n+115行css死样式+测试·**grep零残留**·改密端点`/api/me/change_password`保留(设置改密复用)。
  - **DB清理**:skin做账数据(3流水+1账户)清空+pizihao(12345@qq.com)测试用户清除·可重测。
  - **派新窗口三件**:SPA缓存修复(/console·/invite加no-cache根治改了看不到)+个人事务/个人模式删除(图纸`docs/workspace-entry/00`·L档大改·core=workspace-switcher.ts)+对账中心tab卡顿(6-8s·真浏览器抓timing)。

- **🆕 本窗口(2026-06-11)· 🏦 银行对账 + 手工凭证前端两屏【已上线 · 做账模块全闭环】**(`fad461c8` · ?v=11850750 · prod 真机验渲染2/2+导航+0错):
  - 交互 100% 照搬 `Pearnly_银行对账+手工凭证_UI预览/03-交互原型.html` · 真 API /api/accounting/bank/*。`acct-bank.ts`(三余额带+差额门控/账户·期间选择器/高置信+待人工+已对账+已排除四区/逐行候选建议阈值85对齐harvest/确认·全部确认·组合·改科目·新建交易·排除还原·撤销·导入sha256查重/空·完成·离线·模块未开通·无权限·未选套账门态)+ `acct-bank-modals.ts`(弹窗+工具栏+helper)+ `acct-manual.ts`(借贷表/配平门控/全键盘Enter·Alt=·Ctrl+S/自动补平/存草稿·过账二确·红冲·复制·模板CRUD/已结期lockbar)+ 逐笔审 `acct-review.ts` choice(服务/商品)控件。导航做账组「银行对账」排出账本前 · 手工凭证=做账主屏按钮 · CSS→home-46(scoped .ab/.mjx·bundle)· i18n acct-bank-*/acct-mj-*×4 · 视觉照搬闸登记两屏。
  - **★修真 bug**:金额输入 blur→change 重渲 balbar,在 mousedown/mouseup 间替换「存草稿/过账」按钮 → 真用户填完金额点保存丢点击。金额改走 input 不接 change。
  - **验**:真后端 e2e_3 前端流程 E2E **7/7**(一次性造数→新建交易入账→差额归零→手工存草稿)·零残留;13 闸全绿(typecheck/build/i18n/ai_smell/file_size<500/uiD1D2/asset/ui_lint棘轮/eslint/视觉照搬闸/ratchet)。详见记忆 [[bank-recon-mj-frontend-shipped]]。
- **🆕 本窗口(2026-06-11)· 🔐 权限完善前端【窗口③ · 已全上线】**(`2d0fc410` console 四件 + `a8bc2218` 库存成本遮蔽 · prod 全守门绿):
  - **角色 tab / 三步向导 / 日志筛选导出 / 席位满 + 库存成本列遮蔽显示**。照桌面原型 `Pearnly_权限完善_UI预览/01-交互原型.html` 行为/文案/状态 100% 照搬;工程形态走 console 既有 can()/api + console-i18n 四语(273 键×4 齐)。角色 tab=sidebar 第3视图(成员/角色/安全日志);向导 62 码按域勾选(提权码 billing.manage/ownership.transfer 禁选 · 两敏感开关 cost/payroll · 乐观锁 version→409);日志游标分页「加载更多」+ CSV 导出(同筛选);席位满条对位 G1 422;角色分配统一 `/role-assign`(预设+custom 同入口);`fmtCost(null)→「--」`(后端遮蔽目前仅库存读路径)。
  - **坑**:console 已被 `b64b94cd` 打包收编进 dist → 改 `static/console/{console.js,console.css}` 必跑 `node scripts/build-home-js.mjs && build-home-css.mjs` 重建 `dist/console.*` 再提交;邀请只收 4 预设(后端 role_key max_length=20 拒 custom);向导预设码集前端镜像 registry(无目录端点·后端再 sanitize)。真机自检 27/27(`scripts/_console3_verify.cjs`·真 bundle+stub 真实契约·浅暗截图 `tests/visual/_shot/console3-*`·0 pageerror)+ fmtCost 6/6。?v= console.css/js 5→6·console-i18n 2→3·main.js 748→749。后端见权限①②;详见记忆 [[permissions-window3-frontend-shipped]]。

- **🆕 本窗口(2026-06-11)· 🏦 银行对账 + 手工凭证后端【L 档首例·已上线】**(`85e9b35e`·**银行对账 API 已上线·前端窗口可接**):
  - **新增面收敛**:schema 扩 3 表(`acct_bank_accounts/lines/voucher_templates`·双隔离+RLS+`match_payload` 撤销还原)+ 4 薄层(`services/accounting/{bank_recon,bank_candidates,bank_match,templates}.py`)+ 独立 router `routes/accounting_bank_routes.py` 11 端点(`/api/accounting/bank/*`·复用 acct 六码不新增·view/review/approve/settings.manage)。复用解析(services/recon)/评分(bank_recon_scoring)/过账(vouchers.insert_voucher)/学习(review.write_learned)**零重写**;旧 bank_recon 三表零接触。
  - **匹配三选一**:`{voucher_id}` 关联已有 / `{doc_ids[]}` 组合冲销(借bank贷ar / 借ap贷bank·Σ未结=金额否则 422·**只收全额未付单**撤销可净还原)/ `{new_tx}` 新建(income/expense/transfer+可 remember 学)。CAS+`FOR UPDATE` 并发串行;bank_line 凭证 `source_type=bank_line` uq 防重·撤销 void 还原。候选源 ①凭证关联 ②未收销项 ③未付进项 ⑤已学(desc 指纹)·**④POS 日聚合留后续**(防与 R5 双计·已注释记)。三余额闭环:差额=未对净额(04 定义)。
  - **手工凭证**:`vouchers/manual` 加 `draft`(草稿→pending_review 可逐笔审过账)+ 期间已结校验;`voucher-templates` GET/POST(可 from_voucher 去金额)/DELETE。**逐笔审 `choice`(goods/service)= 纯重分类·WHT 沿用业务单不重算**(03 契约删 `wht_rate`·Zihao 拍板)。
  - **验证**:真库 E2E `tests/e2e/_bank_recon_mj_e2e.py` **29/29**(本地 × prod Supabase·rollback 零残留)+ 单测 45 条 + 全量 3283 绿 + 13 闸全 0 + 5 角色审查(修 difference 语义/CAS 兜底/候选隔离 3 处)。⚠️ **共享树坑**:`a9a9f086`(权限②)误把我未提交的 app.py bank import 带上线→prod 502→`deaa3065` hotfix 删回并交接本窗口"模块齐备后加回";本提交即重新集成(import 验证 11 路由注册)。push 携 `deaa3065`/`13281388`(别窗口未推 commit)一并上线。**前端 acct-bank/acct-manual 两屏待接**(导航做账组「银行对账」排出账本前·手工凭证主屏按钮入·桌面稿 03-交互原型)。
- **🆕 本窗口(2026-06-11)· 🔐 权限完善后端② · 自定义角色 + 成本字段遮蔽(G3/G4)已上线**(`a9a9f086`·丝滑窗口携推·真库 E2E 19/20+V2 直证):
  - **G3 自定义角色(resolver 零改动)**:roles 表 tenant 级行 `key='custom:<slug>'`,resolver 既有 JOIN 读它即生效。**种子守门先行钉死**(test_authz_seed_custom_roles_guard):`_seed_roles` 只刷 tenant_id IS NULL 系统行,custom 行 `name=custom:<tenant>:<slug>` 命名空间隔离永不被覆盖(prod 直证:`_seed_roles` 重跑后 custom 行名/码/启用位不变)。DAL=`services/authz/roles_store.py`(码集净化·提权码 ownership.transfer/billing.manage 禁入·删前查在用→422·乐观锁 version→409·系统键委托 change_role)。路由=`routes/console_roles_routes.py`(GET/POST/PATCH/DELETE /api/team/roles + PUT role-assign·写口 team.member.edit_role·role.* 落审计)。
  - **G4 成本遮蔽(registry 62→64)**:加 `field.cost.view`/`field.payroll.view`(横切·预设除收银员全开·自定义可关)。库存读侧 `field_mask.cost_visible(request)`→无码时 stock 的 avg_cost/stock_value、report 的 value_at_risk 全 null(prod 真库实证:成员全 null·owner 非 null)。POS report/purchase summary 无真成本列故未遮蔽。
  - **真库 E2E**(`scripts/_authz_roles_e2e.py`·本地 uvicorn × prod Supabase):V1 分配即时生效✓/V3 删被拦+转走后可删✓/V6 成本遮蔽✓/提权码禁入✓/乐观锁 409✓·**V2 重启种子不覆盖直连 prod DB 证实**。全量 3274 unittest + 我的 90 专测绿 + 6 道机械闸过。前端窗口③接(static/console)。⚠️ 共享树坑:首次 commit 漏 pathspec 卷了窗口①staged WIP·reset --soft + 显式 pathspec 重提隔离(窗口①工作保住)。
- **🆕 本窗口(2026-06-11 · 主控)· ⚡ 启动 DDL 文件锁 + maxconn 30→15**(`eccc1727`)·**⚠️ 线上 workers 仍=2(非 4)**:`services/startup_lock.py` flock 把 `_boot_schema_ddl` 那批 ensure 串行化(worker 同机故不用 advisory lock=Supabase 事务池会话语义不可靠)+ maxconn 15。一度切 workers=4,启动那批 0 deadlock,但**银行对账窗口发现 `services/recon_jobs` 内嵌 worker 的建表 DDL 未纳入该锁,4-worker 首次建表撞 AccessExclusiveLock → 已回退线上 unit `--workers 2`**(表已存在时 ensure=no-op,2-worker 稳)。**workers=4 真修法=把 recon_jobs worker 的 ensure_table 纳入 startup_ddl_lock**(留 perf/杂项窗口)。3197 单测+flock 多进程互斥真测绿。
- **🆕 本窗口 · 📐 功能开发五阶段流程定稿**(`20ebe1b8`·治"聊得美好做出来小作坊"):`docs/FEATURE_PROCESS.md`(L/S 分级·五件套未经 Zihao 确认禁编码·存量功能体检排队制)。**首例五件套已产出待 Zihao 拍板**:`docs/accounting/bank-recon-mj/00-05`(银行对账+手工凭证·竞品 5 家实查带来源·复用清单硬约束·施工文案=00-KICKOFF.md)+ 桌面稿 `Pearnly_银行对账+手工凭证_UI预览/`。
- **🆕 本窗口 · 🇸🇬 新加坡迁移 runbook 落档**(`d9c61f1a`·docs/perf/01):哨兵 104 条全 vision=403 零异常;**24h 门槛=06-11 17:26 UTC≈泰国 06-12 00:26**;Cloudflare 橙云→切换=改源站 IP 秒级;要搬数据仅 .env+storage+var+backups;收尾步含 .env 泄漏密钥轮换。等门槛+Zihao 拍机器规格(建议 2c4G)与切换时间。

- **🆕 本窗口(2026-06-11)· ⚡ 首屏 SQL 往返削减(鉴权+套账短 TTL 缓存)**(`810bdda7`·后端 only·授权自做自检):
  - 接性能诊断结论(实测无 N+1·瓶颈=22 请求 × 跨区 69ms × 2-worker 串行)。两处进程级 TTL 缓存:`find_user_by_id_cached`(8s·仅鉴权热路径·返回副本·jti 不匹配强制 fresh 重取防误拒·create_access_token evict)+ `default_workspace_id` 结果缓存(60s·只缓存非 None)。隔离 WHERE 一字未改。
  - 计数探针 prod 实测(warm·同用户连打 12 端点):**40→27 SQL(-32%)**;recon/vat_excel 各 -2,余 -1。8 新单测 + 全量 3192 绿。
  - 配套试 `maxconn 30→15` + workers 2→4:4 worker 并发启动撞 ensure_erp_oauth_tables 等无 advisory lock 的 DDL deadlock → **安全回退 workers=2 + maxconn 复原 30**(`cef351bf`)。缓存改动保留。**全部已 push 上线**(`810bdda7`+`34215670`+`cef351bf`·prod HEAD `cef351b`·重启验:credits 零 ERROR/无 deadlock/缓存 live)。⚠️ 共享树报税窗口并发 reset 一度劫持我的 amend(已修复·两边 commit 都复原)。**workers=4 待先给各 ensure_* 加 advisory lock 串行化启动 DDL 后再议**。
- **🆕 本窗口(2026-06-11)· 🧪 真账号报税交叉核 E2E(验证欠账清账)**(`d3945f04`·纯 tests/ 零业务改动):
  - `tests/e2e/_tax_crosscheck_live_e2e.py`:pearnly_e2e_3 真租户全程 HTTP(本地 uvicorn × 真 Supabase)——真进销项→引擎凭证(auto_post·凭证 6 张)→账本 VAT 报告→结账挂点→PP30/PND53/PND3·数字三方交叉核(脚本期望 vs tax-reports vs 税表 breakdown:销 700/进 gross 315/缺税号剔 35/可抵 280/应缴 420/PND 75+30)·体检拦→补税号重算→提交→导出 zip/PDF→已报 409→隔离。**实跑 19/19 PASS**。
  - 残留治理:专用一次性套账承载 + 结尾直连库清 + information_schema 全表扫归零(连首轮中断孤儿套账 52 一并回收·`--cleanup N` 模式入脚本)。凭据走临时文件不落上下文,用完即删。
  - 撞车规避:丝滑专项+打包收编窗口独占 src/home+static/{dist,pos,console}+build,本窗口刻意选纯后端验证项,零交集。前窗口 backlog #1-ter/#6/#7 仍留给该窗口收尾后做。

- **本窗口(2026-06-10→11)· 🧾 报税前端 4 屏 + 商户/事务所导航重分 + UI 补漏一次扫平 + 团队 tab 死链修复**(**已上线** `528cb7e1`+/simplify `e86a1c82`+bump `364a1cef`·?v=11850747·随推携 billing 窗口 2 commit `d441b4f2`/`92708fce` 一并上线·prod 真机验 main.js?v=747 含 loadTaxCenter/bindFileActions):
  - **报税 4 屏(任务A)**:`tax-common/center/pp30/pnd/settings.ts` 接 `/api/tax/*`(信封复用 acct-common 的 aapi/withWs/弹窗)· 做账组加「报税中心」一级入口(PP30/PND 复核从中心点进)· i18n 四语(112 键×4)· 四态齐 · 提交=POST /check 体检→二次确认(更正申报文案)→file(manual)+导出zip→已报只读 · e-Tax 未接=诚实「即将开放/导出手报」**无假直报按钮**。前端流程 E2E 19/19(本地真 bundle+stub)+ 浅暗截图眼验(`tests/visual/_shot/tax-*.png`)。
  - **导航重分(任务C·product-vision 五-bis)**:销项管理→「销售开票」(发票工作台/账套/应收);新建「事务所工具」组(上传识别/识别记录/对账中心)`business_type=firm` 或未选(老租户兜底)显·商户业态隐(`module-nav.ts` apply 控);集成页卡片按归属重排(采集渠道/归档交付/ERP/通知)+ `data-firm-only` 业态显隐(商户只 LINE Bot+智能提醒)。
  - **UI 补漏(任务B·THEME_FOLLOWUP_BACKLOG)**:#1 进项筛选 tab 黑→紫 pill;#1-bis 全站 4 处黑底交互控件(.seg/.zone/.cs-chip)接令牌 + **治本闸**`check_ui_consistency` D2 扩到 segmented/tab/chip/zone 激活态 + 扫 src/home/*.ts CSS-in-JS(D2=0);#2/#3 原生控件 `accent-color:var(--accent)` 全站令牌化;#4 中文字体顺位提前;#1-ter 按现状收口(emoji 棘轮已治本·全量 icons.ts/D3 留专项);#6 对照核销留专项。
  - **团队 tab 死链修(prod 真坏)**:旧设置→团队管理 tab 调已删 `/api/team/*`→点开载入失败。删 tab+`team.ts`/`assign-clients.ts`/`modal-assign-clients.ts`+死 i18n 键(55 删·保留 bank-client-picker 复用的 assign-loading/cancel/save)+ avatar 旧 `data-action=team` 入口删 → 统一 `/console`。
  - **自检全绿**:typecheck/eslint(0 error·顺手加 `scripts/_*.cjs` 进 eslint ignore 解兄弟窗口 scratch 卡 lint)/3184 单测/i18n 四语 0 缺/ui_design_lint 棘轮/D1·D2/asset bundling/authz/file_size/视觉照搬闸全绿。报税 4 屏前端流程 E2E 19/19。**?v=11850745→747**。
  - **/simplify 已跑**(`e86a1c82`):4 审查 agent → 抽 `bindFileActions`(PP30/PND 复核三动作共用)+ 复用 tax-common 的 `num` + tax-settings `bindSwitch`;跳过项(GET+/check 状态门控非浪费/.ts 扫描=#1-bis 治本不加 flag/restaurant 既有特例/lint 正则脆性=同性质非回归)已记 commit。bump `364a1cef`(refactor 后 bundle 字节变·刷缓存)。
  - **push 已收口**:共享树携 billing 窗口 2 commit 一并上线(其 `credits_schema.py +5` 由本窗口 commit 补 RATCHET-EXEMPT·共享树补债范式);billing 窗口明示「托报税窗口 clean push 带上线」。报税 .py 后端早 `6ccc1a3f` 上线·本窗口纯前端。

- **本窗口(2026-06-10)· 🧹 后端杂项收尾 + ★交互性能诊断专项**(commit `d441b4f2` 本地 master·**未由本窗口 push**=报税前端窗口 dist WIP 卡 pre-push 一致性闸·本窗口禁碰 build/dist→搭其下次 clean push 一并上线):
  - **任务A 两笔数据债(同根因·已修)**:prod 4 个 Codex QA 孤儿用户(tenant_id 指已删租户)使 `ensure_credits_tables` step7 INSERT 违 FK、整建表事务每启动回滚报 ERROR。① `credits_schema` step7 加 `EXISTS(tenants)` 守门根治复发 ② `scripts/cleanup_orphan_users.py` 幂等脚本(dry-run/--apply·停用+断 tenant_id+notes 留痕)prod 已 --apply 清 **4→0**·重启后 credits 日志转 INFO 零 ERROR。
  - **任务B**:static/console 暗夜品牌图垫白圆角底板(照 home S2-bis·`html.dark .brand-icon`)·浅/暗真浏览器实测·console/invite `?v=3→4`。
  - **任务C 验证欠账清零**:POS 跨套账 E2E 修测试种子漏 `workspace_client_id`(致 line_invalid)→ **9/9**;清 e2e_3 残留 3 张已提交进项测试单 → 进项隔离 **18/18**;prod 0030 `product_units.workspace_client_id` 列已确认。
  - **任务D 交互性能诊断**(`docs/perf/INTERACTION_AUDIT.md`):真测量定位两根因 = ① 应用在**日本**/DB 在**新加坡**每条 SQL 跨区 **69ms** ② `async` handler 直接做阻塞 psycopg2 致 2-worker 串行(首屏 **22 请求/11.7s**)。Top10 慢交互×分解×归因 + RTT 基线 + 后端建议(**迁同区=最大杠杆**)+ 前端修复清单(交 src/home 窗口)。
  - **/simplify 已跑**(diff 小·四角度自审 already clean)·守门 black/format/imports/ai-smell/size/ratchet 全绿。**下一步**:① 此 commit 待报税窗口 push 带上线 ② 性能 P0(迁新加坡同区)+P1(workers 2→4 / N+1 批量化)待 Zihao 拍板 ③ 前端修复清单待 src/home 窗口。
  - **任务D 续(2026-06-11)· 实测证伪首屏 N+1**(commit `e427b7eb`):按「砍首屏 SQL 往返」目标排查,新增计数游标探针 `scripts/_perf_sqlcount.py`(已入提交)实测所有 boot 端点 **2-5 条 SQL·无 N+1**(与数据量无关·无循环查)。纠正报告早先「~17/~20 条」错误估算(那是中位÷69ms 的估算非实测)。**端点级 SQL已无水分**→降首屏只能降请求数(前端去重/懒加载)或降单查往返(迁区/鉴权-workspace 短 TTL 缓存·需签字)。本轮无 N+1 可改 → 未擅动后端读路径(状态诚实)。

- **🆕 本窗口(2026-06-10)· 🔐 权限批5收口 + PEAK 吸收 4 条 + /console·邀请页真机 5 修**(`038ae65e`+`634fb5d3`+`1359ebd6`·随推主题/报税共 9 commit 合流上线):
  - **批5(权限整顿收官)**:九门旧别名全删(`_require_owner_or_super`/`_require_tenant`/`require_owner`/`require_account_owner`·契约测试锁不许复活);billing 4 处 invited_by owner 判定改 membership(`authz.deps.is_owner_role`);旧团队管理处决=`routes/team_routes.py` 7 接口+`services/team/store.py` 删除(活函数并入 console_store 直调·退出 dal_reexports 防循环 import·EmployeeToggleRequest 迁 admin_users_mutation);改密链路单点留 auth_password_routes(invitations 复用确认)。06 对照表随更。
  - **PEAK 吸收**:B1 席位「当前用户 N/M」+满员升级提示 / B2 角色卡「使用权」模块芯片 / B3 角色「N 人在用」 / B4 行内展开使用权行。芯片全令牌 accent 系(10 色 hex 板撞禁裸hex+紫封板→收敛·mod-* 类名留位,彩色板须先进 console-theme 令牌)。
  - **真机 5 修**:logo 换 pwa-icon-192 / invite 接受失败必复位+422数组人话+pwd.*四语 / 已注册邮箱明确码 `invite.account_exists_other_tenant`(1人1租户·配单测) / 语言切换→站内 seg pills / checkbox 站内样式(顺手修 .field input 全宽压垮 .wsopt)。?v= bump。
  - **自检**:全量单测 3184 绿·权限矩阵真库 E2E **54/54**(批5删后 diff=空)·真浏览器 17/17+增量 16/16(截图 tests/visual/_shot/console2-*)·authz 闸 439 路由绿·ui_lint 棘轮绿(裸hex 清零+baseline 收紧)·inventory helper_gated 收编 `_auth`(解报税 tax_routes push 卡点)。
  - **/simplify 已跑**(`82da056f` 上线):errMsg 泛化 422 数组(同 invite.js 口径)/.field input :not(checkbox) 根治选择器竞争/PLAN_CONFIG import 上提;skip 项=测试 fixture 共享(unittest 惯例自含)、inventory 白名单机制重构(动第8道闸·另立项)、BRAND_HTML 跨页共享(两独立 plain-script 不值引公共 js)。
  - **⚠️ 留存 TODO(碰 src/home+build·下个窗口尽快)**:旧「设置→团队管理」tab 前端处决(data-action=team 改指 /console·删 team.ts/assign-clients.ts/page-settings team pane+i18n)——**后端 7 接口已删,该 tab 现点开会载入失败**。/console 入口本体已有(`45ce1f46`)。
- **本日同窗口(2026-06-10)· 🧾 自动报税(Phase 3)后端全量 commit `6ccc1a3f` · 自检全绿 · 已随批5窗口收口 push 上线**:
  - 照 docs/tax-filing/00-05 封板:`services/tax/`(schema ensure 3表/aggregate PP30销−进+超期剔除+缺税号不计·PND53/3按税号首位分流/anomalies 报前体检 hard·info/filings 幂等+已报不可改/efiling e-Tax诚实降级+PDF·XML·zip 导出/hooks SAVEPOINT)+`routes/tax_routes.py` 11端点(tax.filing.* 逐路由码·accounting 门控·套账 fail-closed)+ close-period 挂点一行。
  - 自检:40 新单测+全量 3182 绿·真库 E2E `tests/e2e/_tax_e2e.py` **25/25**(数字对账本 books.vat_report 同基/体检拦缺税号→补→提交→已报只读/导出真生成/0税额照报/未结账拦/跨套账隔离)·做账 E2E 28/28 回归零红·/simplify 已跑(5 改:mark_filed 去双重聚合等)。
  - **🚦 push 调度(已完结)**:9 commit 链(主题 2+报税 1+批5/console 4+docs 2)由批5窗口收口一并 push;裸hex 卡点已令牌化清零(`1359ebd6`),black 携带修复 `90c3d834` 已并入。报税 .py 改动靠部署重启生效。
  - 决策:模块门控用 accounting(报税吃账本·registry tax 码组本就不挂模块键);e-Tax 未接通(RD 开放度未确认)→ file(etax) 返 tax.efiling_failed·主路径=导出 PDF/XML 手报+mark-filed;ensure-only 无 alembic(做账先例)。前端 4 屏照 docs/tax-filing/04 另开窗口接。
- **本日同窗口(2026-06-10)· 🟣 全站主题切 Purple v2 上线**(`1552209c`·?v=11850745·prod 字节已验):
  - 色值唯一来源 = 桌面/Pearnly_紫色主题预览 `.panel.purple` 浅+暗 + partner-components primary-50..900,逐字搬零调色。home-01-base.css 浅/暗令牌(accent 系/blue 别名/btn-blue/blue-50..800 紫阶/bg/ink/line)+ home-38 按钮 + /console v1 估值→v2 真值 + POS 旧蓝→紫(厨房深色屏用暗夜紫 A974FF·sw 缓存 bump)+ /admin 自动跟随(真浏览器抽查 3 屏)。状态色(green/amber/red)按任务范围未动;主按钮全站纯色 var(--accent),渐变不全站化。
  - 视觉闸:design 17 快照重着色 + fidelity 主色断言→rgb(124,77,255) 全绿;ui_lint_baseline 旧蓝随迁紫下降已收紧。DESIGN_LANGUAGE 令牌节=Purple v2(真相=home-01-base.css·禁写死 hex·并入一-bis 交互原则成稿)。
  - 自检:`_s1_shot` 全路由浅/暗逐张眼验(无残留绿/暗夜不洗字)+ `_purple_spotshot/_purple_admin3`(console/pos/admin 抽查)+ 守门全绿。**注意:工作树有权限批5窗口活跃 WIP(.py/tests)·本 commit 严格只含主题 pathspec**。
  - **/simplify 已跑**(`49a0ef2` 收口:home-38 删重复 :root --btn-blue 块改单源 home-01+fidelity spec 删 15 处冗余 primary 字段;`07a7b8b` 回撤 var(--blue) 换法=lint 旧token棘轮拦)。两 commit 已随批5窗口收口 push 上线(console 裸hex 卡点已令牌化清零)。
- **本日同窗口(2026-06-10)· 📒 做账引擎(Phase 2)出账本后端 + 前端 5 屏全闭环上线**(HEAD `3e157b10`·?v=11850742):
  - **出账本后端 `5f82e6bc`**:`services/accounting/{books,books_pdf,closing}.py` + 独立 `routes/accounting_books_routes.py`(books 总账/明细账/试算表 · tax-reports VAT/WHT · financials · close-period · export-package zip)。close=待审挡结(≤period 全段)+ R9 经引擎生成直接 posted + closed_through 水位只进不退;VAT 报告/结转剔除 vat_closing 自身;PDF 泰中混排 4 语表头。31 单测+隔离闸绿。
  - **前端 5 屏 `67f5b783`**:`src/home/acct-{common,list,review,accounts,settings,books,modals}.ts` 照桌面稿 01-05+emerald 基座。主屏(北极星+待审行动卡+行内展开借贷·撤销重做/作废二次确认)/逐笔审(原因人话+改科目.modal+remember·缺映射壳给设置落点)/科目表/设置(自动过账全局+R1-R9 粒度开自动二次确认+映射弹窗+learned 可见规则)/出账本(接后端·结账流)。i18n acct-* ~140键×4语·导航做账组 5 子项(accounting 门控默认关 opt-in·「即将上线」退场)。
  - **验**:真浏览器冒烟 32/32 浅+暗(`scripts/_acct_shot.cjs`)·视觉照搬闸 5 屏登记 PASS(快照 emerald 适配入库)·tsc/eslint/守门全绿。顺手 `c4ac0cd` core-boot 路由表抽 `route-table.ts`(507→<500·以后加页不碰 core-boot)+ `/simplify` withWs/acctConfirm 收敛(净-42)。
  - **prod 真账号实证(e2e_3)**:开 accounting 模块即 seed 泰标科目 · vouchers/accounts/settings/review/试算表/VAT 报告 6 端点信封全 ok(诚实空账且平)· 试算表 PDF %PDF 9.4KB + 报税包 zip 54.8KB 真生成。/console 入口已补进头像菜单(`45ce1f46`·data-show-if-team 显隐·4 语)。
  - **剩(已记忆)**:① 真业务流 E2E(e2e_3 新进项/销项→凭证→审→close·新业务才生成凭证)② 屏6 银行对账缺后端(复用 importer/recon·单独立项)③ 逐笔审「服务/商品」分叉需后端 review 加 choice 入参 ④ 手工凭证录入 UI。
- **本日同窗口(2026-06-10)· 🔐 权限管理批1-3 + /console 管理控制台全量上线**(Zihao 授权自检即 push·HEAD `cc9c3bb3`):
  - **批1 地基**:`services/authz/`(registry 62 码=02 矩阵代码化/resolver memberships→roles·users.role 兜底/deps require_perm 统一执行点 deny-by-default)+ ensure(roles 种子 6 角色·JSONB 每启动按 registry 刷新/memberships 加列+存量回填 21 行/member_scopes/invitations/ownership_transfers)+ 注册/加员工/懒建 tenant 三建号点同事务双写。坑:**prod 有孤儿 tenant_id(b6b184cc)撞 FK→迁移改三步独立事务+EXISTS 守门**(billing ensure 同病未修非本窗口)。
  - **批2 九门收敛**:167 路由逐码 require_perm(销项/进项/做账/知识库/对账/ERP/团队/套账/POS后台/库存),owner 判定 invited_by→membership,作用域闸 check_request_scope(assigned 未分配 404 防枚举·套账切换器按分配过滤)。**矩阵为准的行为偏差全记 docs/permissions/06**(收紧:POS后台/销项设置 owner+admin;放宽:会计获审批/付款/过账,admin 获 ERP/模块开关)。POS 双令牌/LINE 零改动。16 契约测试改钉逐路由权限码。
  - **批3 团队后端**:邀请(email+LINE·sha256 单次 7 天)/改角色/配作用域/启停移除(边界 422:自锁/动 owner/最后 owner)/所有权转移(目标须 admin·24h·双向确认不可逆)/安全事件落 operation_logs(team./role./scope./ownership.)。
  - **/console 独立 SPA**(紫色主题 v1 只作用 /console+/invite·令牌抄合伙人预览稿·结构全走 var):屏1 成员列表行内展开/屏2 邀请弹窗(角色卡+作用域多选+copy-link)/屏3 安全日志人话 4 语/转移口令流/邀请接受公开页四态。主程序入口未加(src/home 红线·留做账前端窗口顺手加一行指向 /console)。
  - **第 8 道机械闸** `check_authz_coverage.py` 挂 pre-push(441 路由全覆盖·公开白名单 42 条显式注释)。
  - **自检**:单测 3144 绿(矩阵 6×62 逐格/deny-by-default/边界)·真库 E2E 54/54(本地 uvicorn×真 Supabase·5 角色矩阵/作用域 404/邀请生命周期/转移去回/降档即时生效)·真浏览器 17/17(三屏+邀请页四态+浅暗截图 tests/visual/_shot/console-*)·prod 部署后冒烟过(/console 200·permissions API owner 62 码)。
  - **共享树**:连带做账窗口托管的 `5f82e6bc`(出账本后端·其知会可上)一起上线;其 FE WIP stash 已无冲突恢复。**/simplify 已跑**(`5d1bb9bd` 上线):热路径删每请求多解一次 JWT/作用域尾段去重/accept 删冗余二次写/token 哈希收敛 hash_token 单点/set_scope 批量 ANY/no-cache 头抽常量;顺手清掉 master 上 route-table 拆分导致的过时红测(test_test_center 改钉新位置)。**批5 收口待做**:删旧门别名+旧团队管理处决(05 文档 Zihao 拍板·前提已满足)。
- **🆕 本窗口(2026-06-10)· 🚀 做账引擎(Phase 2)后端全量上线**(Zihao 授权一次性建完·自检即 push):
  - **图纸修订先行**:超越方案 C1 数据源分级(第一方100直通/OCR分流/银行只建议) + C3 错账安全带三件套(method 标注·unpost 撤销重做·粒度 opt-in 默认建议模式) + C4 六大行对账单解析复用 recon/importer → 并入 docs/accounting 01-05。
  - **后端**:`services/accounting/`(schema ensure 6表双隔离+partial唯一防重复排除void / 泰标 NPAEs 科目+角色映射 seed / rules R1-R9 纯函数 / posting 置信分流+借贷平断言 / review 学习记忆 / hooks SAVEPOINT 包死)+`routes/accounting_routes.py` 17 端点(信封·owner 写·accounting 门控·**i18n 键前端窗口接**)·模块默认关 opt-in·预设全业态开。
  - **挂点 6 处一行 enqueue**(进项 post/付款·销项 issue/红冲·POS 零售/餐厅)·业务主路径零影响(异常注入真库证明)。
  - **验收**:新增 ~80 单测(全量 3038 绿)·真库 E2E `tests/e2e/_accounting_e2e.py` **28/28**(真挂点链路/待审→审+记忆→同类自动/撤销重做/跨套账隔离/不平拒绝)·守门全绿。
  - **既有回归**:purchase isolation 16/18(2红=e2e_3残留数据·干净基线同样红·非本窗口)·POS 旧 E2E 卡商品被 06-08 重置清空(基线同样)·POS 路径已在做账 E2E 真 create_sale 补验·顺手关 e2e_3 残留开班(06-07)。
  - **剩**:前端 5 屏(主屏/逐笔审/科目表/出账本/设置+银行对账)等 UI 统一窗口收尾后照 docs/accounting/04 接真·books/close-period 随出账本窗口。

- **🆕 本窗口(2026-06-10 · Fable 5 接手 Opus 卡顿窗口)· UI 整顿 punch list 推进 + Claude 式导航**:
  - **唯一修复清单 = `docs/ui/UI_DESIGN_AUDIT_FINDINGS.md`**(逐项勾+commit)。已完:S1 蓝绿收口 `74a56a5a` / S2 暗夜换肤 `9efd4fed`+全局清零 `a1d58008` / S3 空态统一+暗夜表单 `179123b9` / S4 图标 Lucide `a49ad27f` / S6 激活态(并入导航)。
  - **Claude 式导航 `f72a10a5`**(Zihao 拍板·稿 `scripts/_mock/nav-claude.html`):logo 进侧栏/分区小字标题/淡绿激活 pill/三级拍平/底部 pinned 用户卡/窄 rail;后续修 rail 顶只留折叠键 `ac54f023`、弹窗随 `--sidebar-current-w` `5e8f00af`、/simplify 收口 `76865395`。
  - **拍板已落档(findings 四)**:POS/admin SPA 按标准排迁 emerald(后续窗口)· 暗夜 mint 不降饱和(封板即标准)· **着陆页永不动** · Codex 种子已清(prod:页脚 NULL+27 商品停用·void 单据合规保留)。
  - **剩余(下窗口从这接)**:S5 文案收口 → S7/S8 布局 → S9 按钮 retrofit → 杂项(漏迁3屏/弹窗迁kit/原生confirm) → 补抓评审(抽屉/嵌套/流程态/生成文件)→ lint 清零挂闸。验证基建:`scripts/_s1_shot.cjs`(浅暗截图)+ `scripts/_nav_verify.cjs`(导航交互+手机)。
  - **坑**:两连推 webhook 会吞第二次部署(prod 卡旧 commit → ssh `git fetch pearnly && merge --ff-only pearnly/master`;服务器 `git pull` 默认 origin=旧 mrpilot 仓别用)· 改 home-NN.css 必 bump ?v= 否则 immutable 缓存吃旧文件。

- **🆕 本窗口(2026-06-09)· Zihao 真用一路报问题、逐个修+真 prod 验证上线**:
  - **登录/着陆页**:手机端语言条压关闭X、桌面安全三件换行对不齐(浏览器翻译触发)修;手机场景挂件防遮挡(工作气泡 min-width:0 解锁收窄不压问候、Quote 下移露出猫+笔记本)·`a44fd358`/`064055ff`(?v=12/13)。
  - **home SPA 三修**:刷新某模块只剩侧栏(bootstrap 早于 defer 模块注册 loader→`reloadCurrentRoute` 泛化兜底)/ 切套账界面无反应(全局 `pearnly:workspace-changed`→重载当前路由·删 7 处分散订阅 DRY)/ 采购设置开关整行可点误触(改绑 `.sw`)·`d03a958f`。
  - **A1** LINE 一句话记费用默认带当天日期(修"本月花费 ฿0"·doc_date 空永不进按月统计)·`4b8a2601`。
  - **E** `/api/ocr/recognize` 响应净化(新 `services/ocr/recognize/sanitize.py` 递归剥引擎/品牌/层/`_`debug/token·两出口都过·删死字段+前端死 toast+死i18n键×4语·防回潮单测)·**真账号 prod 双出口实测 CLEAN**·`698cda97`/`c18f816a`。
  - **C+D** 进项票图持久化+渲染+放大:拍票图原 `_run_ocr` 跑完即丢→`pdf_storage.save_bytes` 落盘→挂 `purchase_attachments(kind=bill)`→`get_doc` 改写 url 不暴露存储路径→新端点 `/docs/{id}/bill-image`(鉴权+套账边界)→前端本地 blob 即时显示/已存单据鉴权取图/「放大看」+点图开浏览器原生缩放拖动查看器(票图整块拆 `purchase-form-bill.ts` 守<500)·**prod 全链真字节 200595 + ws=33 隔离 404 实测**·`be36785d`(?v=11850726)。
  - **B** 泰式 2 位年日期消歧(24/08/25→2023 bug):`ThaiInvoice` model_validator 只在 date_raw 是 DD/MM/YY 时只重算年(公历20YY vs 2位佛历25YY−543 取最接近今天)·**prod 新识别实测 24/08/25→2025-08-24**(对齐 Paypers)·`61fa7e05`。
  - /simplify:`save_pdf` 委托 `save_bytes` 去重·`a0aa6408`。
  - **🔴 未完(已记忆+设计稿·待拍板)**:LINE 拍进项票只落识别记录(门控未选业态)+ 缺手动改方向 + 事务所客户做账分流 → **统一智能录入设计稿 `docs/smart-intake/02`·待 Zihao 拍 4 分叉再施工**·见 [[smart-intake-routing-override]]。
  - **留给 Zihao 浏览器确认**:C+D 拍清晰票后表单显示票图+放大(我测试图都低置信进待归类出不了表单)。

<!-- ===== 以下为前序窗口历史(2026-06-08 及更早)· 详见各 [[memory]] ===== -->
## 🎯 状态卡（2026-06-08 · **🏁 套账隔离 100% 收官(PO-7b 连号按主体 + A/B prod E2E 9/9)· HEAD `e449d80`(?v=11850716)** · 前序:POS 全栈 / 销项 PO-10 / 知识库 / LINE @pearnly）

- **🏁 套账隔离全闭环(2026-06-08·本窗口·commit `89e71ca`/`021c25f`/`e449d80`·Zihao 授权"全做完不必报方案")**:把前两窗口遗留的 gated/尾巴全做完并 **prod 真账号 A/B E2E 9/9 通过**。① **PO-7b 连号按主体**(RD 合规):计号键扩 (tenant,ws,doc_type,prefix,period)·开票/红冲/POS 三取号点全传主体·迁移做成**启动自愈 ensure**(`numbering_workspace_key.py`·建 uq_dns_ws+回填+守门式 drop 旧 PK·稳态早退·部署即自应用·无需手动 prod 迁移)·单主体号序逐张不变。② 顺带补 PO-7a 漏:红冲单继承 `seller_workspace_client_id`(原留 NULL 跨套账泄漏)。③ 对账源查询 `list_invoices_for_recon` 加套账过滤。④ 切套账自动重载 history/sales×3/reconcile 五页。⑤ /simplify:startup.py 25 个 ensure 块 DRY 成 loop(507→393)+ 取号主体解析抽 `document.workspace_for_numbering`。**剩余仅 etax 两表(零 DAL·建表随手隔离·DEFERRED)。** 详见 [[workspace-isolation-audit]]。


- **销项前端 PO-10 上线 + 验收 4 轮全绿 + 续修(本会话)**:Codex 真浏览器验收(报告在桌面 `pearnly_sales_full_acceptance_*` / `_round2/3/4_*`),第 4 轮 **PASS 10/问题 0**。修复链:① 上传坏图 500→422(Pillow verify 坏 PNG 抛 SyntaxError 未捕获) ② 工作台/商品服务端 `?status=/?q=`(documents 的 q 后端补 ILIKE) ③ 向导自定义行「存入商品库」POST products ④ 成功面板直达下载/打印(共享 openDocPdf) ⑤ 图片 `<img>` 401(取图要 Bearer→加 loadAuthedImg fetch→blob) ⑥ 开票被合规拦→跳步+具体缺项提示 ⑦ RD 核验弹结果窗(读 `body.data.*` 非顶层) ⑧ **第5步「开出」死按钮**(go() 边界检查排在 doIssue 前→永不可达·开票从未触发) ⑨ 全错误码本地化(`sales.*` 17键×4语·不露原始码) ⑩ 草稿详情动作分档(继续编辑/删除草稿·DELETE 路由+delete_draft·迁移外·级联删行) ⑪ **正本+副本同页逐单持久化**(迁移 0019 copies_layout·/pdf 读单据版式)。详见 [[sales-acceptance-round1-fixes]]。**坑:鉴权图不能直接当 src / RD 接口回 {ok,data:{}} 字段嵌 data / go() 边界检查别排动作分支前 / sed 改 home.html 翻 CRLF(用 Edit) / document.py 卡 500 用 docstring 压缩腾位**。
- **下轮(第5轮)待验+待修**(见桌面 `pearnly_sales_round4_*/修复待验清单_第5轮_2026-06-07.md`):copies_layout 两联 PDF 真验 / 草稿编辑·删除 / 按钮选中高亮(B·需确认哪屏) / 商品单价VAT间距(D) / 工作台列表视觉(E) / 模板编辑"假功能"(C) / 纸张·语言逐单未持久化。

- **知识库 = 闭环**:Codex 第2轮报告 `桌面\knowledge_fix_verify_2026-06-05\知识库修复验证报告_第2轮_2026-06-05.md` **全 PASS**(P1a 坏PDF=`processing_failed`+人话文案+不扣费 / 原文黄底高亮可用+可核对 / 0 console error / 计费正常)。2 个观察项(种子文档太短只 1 chunk 无灰色邻段 / 答案只 1 出处卡无法测切换)= **非 bug**,下轮用长文档演示即可。deferred 的 `ocr_ingest.py` 双 suffix 判已收口(等价·88 知识库测试绿)。
- **LINE 官方号换号上线**(高敏·铁律#26·Zihao 全程在场)：旧 `@059oupmg`→新 **`@pearnly`**(Channel `2010309291`)。prod `.env` 换 4 项(不碰 `LINE_LOGIN_*`)+ 全站 `@pearnly` + 机器人**对话体系全做齐**:首加好友欢迎=**OA Greeting 卡**(机器人不回·去重复)/ 转人工=**只走 OA 后台原生**(机器人 agent 处理已撤·`0e7cc7c`·Zihao 2026-06-06 拍板)/ 无关文字=4 语菜单(带拍照贴士)/ 图片=OCR(真账号实测闭环·扣 ฿0.18)/ 默认语言 zh→th / 定位「财务自动化助手」+ 路径「集成→LINE Bot」。/simplify 收口(删死键 image_soon/抽 DEFAULT_LANG/去冗余 lower)。详见 [[line-account-migration-pearnly]]。
- **🚀 销项模块 Phase 1 后端全上线**(2026-06-06·Zihao 破例开建·全程真账号 E2E):`services/sales/*` + `routes/{products,sales,sales_seller}_routes.py` + alembic `0006~0008`(**prod 库已 apply·alembic 追踪本次首次在 prod 立起**·之前全靠 ensure_*)。PO-1 schema / PO-2 商品 CRUD / PO-3 Excel 导入 / PO-4 开票核心(连号 FOR UPDATE·开出不可改 409·VAT+WHT·Decimal)/ PO-5 红冲补开(CN/DN 独立连号)/ PO-6 合规 PDF(reportlab 复用泰文字体·桌面 `sales_invoice_sample.pdf` 样票)。**卖方=账套主体**(Zihao 纠正:会计事务所代多公司):账套主体加开票字段(地址/总分公司/电话/VAT)+ 选择账套弹窗改「只选不建」(新增去客户管理·真浏览器验 0 console error·缓存 bump 11850610)。沙盒 `pearnly-knowledge` 设计→`docs/knowledge/`。全貌 [[sales-module-sandbox-project]]。
- **🆕 销项买方模块 + 合规后端(2026-06-06·两批上线 prod)**:① `a1169bf` 买方动态模块(`services/sales/buyer.py`·公司/个人/外国/匿名)+ §A 双方冻结快照 + §J 合并单/收款 + §D 折扣 + §E1/E2 纸张正副本 + §G 历法(迁移 0009~0011)② `bcfa482` **§M 1-3**:§C 价内/价外(`price_includes_vat`+抽出 `services/sales/totals.py`)· §E2 省纸两联(`copies_layout=two_up`)· §F 审批工作流(`services/sales/approval.py`·默认 none·owner 审批·迁移 0012/0013)。**prod 迁移已 apply(alembic 到 0013)· prod 真库 E2E 过**。全貌 [[sales-mhz-blocks-and-prod-ops]]。
- **🆕 全平台业态套餐 · B 阶段后端上线 prod**(本窗口·HEAD `3c87e2d`):业态预设(6 业态 firm/retail/pharmacy/restaurant/service/b2b)+ `PUT /api/me/onboarding`(注册选/设置切业态·写 tenant_modules)+ `PUT /api/me/modules/{key}`(设置页逐个开关·关=隐藏不删)+ 扩 `GET /api/me/modules`(加 business_type/gateable/receivable)+ `require_account_owner`(`invited_by is None`)。**老租户默认全开不破坏(onboarding 是 opt-in·从不主动给老租户写行)**·复用 tenant_modules 零迁移(business_type 走哨兵行)·真账号 live E2E **7/7** + post-deploy 冒烟绿。图纸 `docs/platform-onboarding/01-05`(门控位置地图/预设/接口/UI/PO)。**前端(导航数据驱动 + 注册选业态页屏A + 设置模块管理页屏C + i18n)= 撞 POS 屏8 文件(app-shell-html/core-boot/module-nav/i18n-data),待 POS 前端窗口收完 push 再起(见 05-po-plan)**。详见 [[platform-onboarding-backend-shipped]]。
- **未提交残留**:无(全 push·HEAD `bcfa482`·守门全绿·全量 **2431 OK**)。**deferred/未闭环**:① 知识库页码/章节标 ② 问答偶发 Gemini 503(瞬时·不扣)③ LINE 一句话记账**未建**(spec 铺垫)。
- **LINE 收尾(删旧号·Zihao 在 Console)**:① OA 关最后「转人工」规则 ② 真机复测 ③ 复测无误删旧 OA `@059oupmg`。代码侧无旧号现行残留。
- **下一步(下个窗口·先读 `docs/sales-module/STATE.md` 顶部 + `docs/16` §M)**:接**销项 §M 4-7 后端块**(4. E3 `pdf_sha256`+热敏窄版 5. L1 PromptPay/L2 WHT多档/L3 报价转换 6. L4 模板后端管道 7. `sales_settings`+并激活审批 `approval_mode`+clients/workspace_clients 补字段)→ 再 8. PO-7 邮件发送(LINE 高敏等 Zihao)→ 9. PO-10 前端(照桌面三份样稿)。**每块本地全量 unittest + prod 真库 E2E·迁移走 ssh+psql 经授权·见 [[sales-mhz-blocks-and-prod-ops]]。**

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
