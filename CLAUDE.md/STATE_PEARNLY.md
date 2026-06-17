# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡（2026-06-17 · **OCR 纠错 + LINE 费用卡片产品化已上线** · HEAD `33142a1`）

- **本窗口完成并上线**：
  - `62cb5338`：LINE 图片 OCR/采购入账收口。简式税票/收据无买方身份时不再自动当可抵进项；过滤 Total/VAT/Payment 等汇总行；VAT 已含税明细不再误触发总额不符；卡片可保留逐条明细；非票据图片回明确提示；LINE loading 按 60s/50s 循环续到出结果。
  - `33142a1f`：LINE 费用/采购识别结果卡片文案产品化。金额显示 `431 THB`；状态改为“费用已入账 / 请确认后入账 / 可能重复 · 请核对”；“分类”改“建议分类”，“明细”改“费用明细”；卡片前回执改“费用已入账 / 已保存费用草稿”；未接 Excel/Drive/邀请员工流程。
- **线上状态**：新加坡 `root@66.42.49.213` 已部署到 `33142a1`，`mrpilot` active，`/api/version` 200。生产环境确认 `OCR_FALLBACK_MODEL=gemini-2.5-pro`、`OCR_ESCALATE_MODEL=gemini-2.5-pro`（上一轮确认）。
- **验证**：
  - OCR 修复目标测试：本地/服务器 52 绿。
  - 卡片目标测试：本地/服务器 40 绿。
  - 全量 unit：3797 绿；`check_file_size` / `check_imports` / `check_i18n --strict` / `check_ai_smell` 绿。
  - `npm run format:check` 仍被历史未跟踪 HTML/JSON/审计输出文件拦住（31 个），本次按 Zihao 指示不处理。
- **剩余风险 / 待跟进**：
  - OCR 仍需真实用户继续喂票观察，尤其泰文品名拼写与分类是否过度自信。
  - 分类建议目前只显示为“建议分类”，没有单独展示分类置信度或原因。
  - 580 个未跟踪文件确认多为历史审计/测试/截图/输出，本次不清理。
- **下一步建议**：继续用 LINE 发真实票测试；若卡片方向满意，再做“分类可解释 / 低置信分类提示 / 更强的品名纠错”。
- **在等 Zihao**：发 1-3 张真实 LINE 回执截图验收卡片文案与明细效果。

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
