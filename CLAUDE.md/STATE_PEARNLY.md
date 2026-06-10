# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡（2026-06-10 · **做账 Phase 2 前后端全闭环 + 权限批1-3/console 上线** · HEAD `?v=11850744` · 前序见下）

- **🆕 本窗口(2026-06-10)· 📒 做账引擎(Phase 2)出账本后端 + 前端 5 屏全闭环上线**(HEAD `3e157b10`·?v=11850742):
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
