# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡（2026-06-11 · **🧪 真账号报税交叉核 E2E 落档**(本窗口·`d3945f04`)· 前序见下）

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
