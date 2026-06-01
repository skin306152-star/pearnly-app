# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-01 · **整顿暂停**·Zihao 新例外任务:**DMS 推送日志/异常栏 UX 闭环**(身份证→订车单 ≠ 发票推送·别混在发票框架里)· DMS 集成第3轮已闭环 · C3 拆到 home.html 1495 暂停)

- **模式**:整顿封锁期 · **整顿主线【暂停】**(Zihao 2026-06-01 再拍板:先做 DMS 推送日志/异常栏的 UX 闭环问题,整顿记录后暂停)。**C3 进度封存**:home.html 1730→**1495**(R13 page-history `4d3b9e0` + R14 onboarding `99c5da4`·均 prod E2E 验过)·目标 <1000 还差 495·下个候选 bank-cand-drawer/on-demand modal/page-ocr(最后)。app.py 1731→500 仍卡 auth 专窗口。
- **🔧 当前 task:DMS 推送可视化 UX 闭环**(commit tag `MRERP-DMS-INTEGRATION`·非整顿)。Zihao 指出真问题:身份证→订车单(`mrerp_dms`)是**独立于发票推送**的业务,现被塞进发票中心的「推送日志/异常栏」用**发票字段**(发票号/买方/卖方)框、ERP 筛选硬编码 [MR.ERP/Xero/FlowAccount即将]、裸露 `ERR_ID_CARD_REQUIRED_FIELDS`。要求:① 推送日志 ERP 筛选改**下拉**·只列真实配置端点·选一个看一个不混 ② 身份证→订车单的日志/异常按 DMS 字段(订车单号/客户/身份证)正确展示·错误码 i18n 友好不裸露 ③ 异常栏同理不混进发票推送异常 ④ 真闭环。自己设计/做/测。
- **C3 进度**:home.html 1730→**1495**(-235 本窗口)· **R13** 抽 `#page-history`(96 行)→ `src/home/page-history.js` 运行期注入(import 置 history-list.js 前)`4d3b9e0` · **R14** 抽 `#onboarding-modal`(141 行·登录后欢迎向导)→ `src/home/welcome-wizard-html.js` + welcome-wizard.js showOnboarding() **懒注入**(wizard 暂下架·永不触发·复活即生效·事件全 document 委托→安全)`99c5da4`。两者注入 HTML 与原 innerHTML 字节等价 · prod E2E 01-login/04-history 绿(R14 首跑因部署冷启动瞬态失败·重试即过)· CRLF 保真。**下个 C3 候选**(由易到难):bank-cand-drawer(~24)/ 客户编辑等 on-demand modal / page-ocr(~150·识别主页·高耦合最谨慎·留最后)。app shell(顶栏~128/侧栏~143)boot 关键勿轻动。
- **首轮(R1)6 缺陷已修上线**:003(身份证不转PDF+PDF栅格化兜底)/005(DMS 不入推送列表)/TC1.4(测试按钮 POST)/006(错误码 i18n)`733b3a9` · 001(登录点击竞态)`4c35dce` · **004(Critical 新建客户 ERR_DMS_CUSTOMER_CREATE)`256df28`**=根因建客户时省/区/街道/邮编 select 发空串被 cus/new.php 拒,修=`_resolve_address_geo` 把地址文字级联解析成 DMS 主档 ID(泰文前缀归一+逐级兜底)。测试计划 `docs/integrations/mrerp-dms-ui-test-plan.md`。详见记忆 [[mrerp-dms-integration]]。
- **✅ Codex 第2轮复测结果(报告 `_uitest/dms-ui-20260601-r2-full/report.md`)**:**R1 硬门槛 PASS**(全新身份证→建客户 91 + 订车单 PNTEST6010180601·省/区/街道/邮编已填)·**无 Blocker**。R2/R3/R4/R6 全 PASS。两 non-Blocker FAIL 已修上线:**R5(i18n)**=`_DMS_FRIENDLY`(erp_push.py)只有 zh/en/th/zh_TW·错凭据日文回退英文→补全 7 条真日文 `ja` 键 + 回归测试 `test_dms_friendly_i18n.py` 锁 ja≠en;**R7(视觉)**=DMS 卡按钮 测试→修改→停用 改 **修改→测试→停用** 对齐财务卡。另按 Zihao 要求 **向导隐藏「DMS 地址」字段**(地址写死·只此一个 DMS 实例·只留 账号/密码/订车单号前缀)。commit `63197c6`+`0d1c380`·全量 2147 OK·prod bundle 字节验过。
- **✅ DMS 集成已闭环(Codex 第3轮全 PASS · 报告 `_uitest/dms-ui-20260601-r3-full/report.md`)**:R5(日文错凭据显正确日文·`error_friendly.ja` 命中·无英文回退/无 raw key)/ R7(DOM 序 edit→test→toggle=編集→テスト→無効化)/ 隐藏地址(`hasSystemUrlInput=false`·只剩账号/密码/前缀·正确凭据保存成功)/ R6(发票抽屉无 DMS 候选·`auto_push` 恒 false)**全 PASS · 无 Blocker · console 0 serious error · version 11850050**。首轮 6 缺陷 + 二轮 2 项 + 隐藏地址全部上线坐实。DMS 任务收尾,Zihao 拍板继续整顿。
- **2026-06-01 另修的 Zihao 例外 UI(非 DMS·非整顿)**:① 超管后台 `/admin/*` 设计语言整体崩坏——根因=整顿拆 home.css 后 admin.html 仍引空 home.css(`b078e39` 改引全套 home-01..38)+ `home-18-admin-users.css` 早被 `fa08ecc` 当死码误删(`7c80ee7` 从 git 恢复·修用户表格/抽屉)·见记忆 [[admin-spa-independent-css]]。② MR.ERP 财务卡按钮顺序/样式/文案对齐 DMS 汽车销售卡(`ea422f9`)。均真浏览器验过。
- **DMS 集成已完成上线**(主体 `2b63ecd`+`a355451`+`80bdc23` / 登录修复 `4c35dce`·prod 版本 `11850043`·deploy ok 无回滚)。后端 live 端到端真验:DMS 测试站真建订车单(customer 65 / booking_id 16 / PN0010100531 / sc::1)。架构=Playwright 真登录 + 鉴权上下文驱动官方表单契约(铁律#7)。落点:`services/erp/mrerp_dms_{models,xlsx,client,adapter}.py` / `dms_routes.py`(app.py 仅 include_router) / `services/ocr/id_card_extract.py`(独立 prompt 不碰发票) / 前端 `src/home/{erp-mrerp-dms-connect,ocr-document-mode,dms-id-card-results}.js`。详见记忆 [[mrerp-dms-integration]] + 交接文档 `docs/integrations/mrerp-dms-integration-handoff.md`。
- **已修 DMS-UI-001(Blocker)`4c35dce`**:DMS 登录 `#btnlogin` 处理器绑在 window `load`(非 DOMContentLoaded)·原 login() 等 domcontentloaded 就点击=空操作→间歇 `ERR_DMS_AUTH`。修=`wait_until="load"` + 监听 `checklogin.php` 响应判成败(`lct::*::*`=成功 / `al::`/`err::`=拒绝·DMS 拒绝走自定义 modal 非原生 alert)+ 点击重试3次。验:好凭据 5/5、坏凭据 1.4s 秒判 AUTH。
- **防误推三重保险(高危·别动)**:mrerp_dms `auto_push` 强制 false · 不进发票抽屉推送列表(ocr-push.js 过滤)· push_to_endpoint 硬拒(`ERR_DMS_NOT_INVOICE_ENDPOINT`)· 身份证自动推送另用 `config.id_card_auto_push`。schema:Alembic 007 + push_schema ensure 双跑(canonical 加 mrerp_dms·skip 改全量校验防 CheckViolation)。计费按普通图片 OCR(kind=pdf units=1·不污染发票额度)。
- **测试账号**:Pearnly `18685123459@163.com` / `xiaopi19950730..`(真数据账号·谨慎);DMS 测试站 `https://www.mrerp4sme.com/dms/index.php` `dmstest`/`dmstest`(只本地 env 注入·绝不入库/日志/commit)。e2e_1/2/3 见 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`。
- **部署铁律**:改 src/*.js 必 `npm run build` + `git add static/dist` + bump home.html `dist/main.js?v=`(纯后端 .py 改动免 build/免 bump);home.html/css/i18n-data.js 是 CRLF+prettierignored·禁 sed/prettier·只 Edit 或 node split/join;pre-push 机械闸跑 ruff/black/eslint(0 error·会扫本地 scratch 文件勿留)/build·先 format 再 push。
- **home.js 拆迁全收官**(33768→0)·拆迁范式沉淀记忆 [[home-js-batch-split-bridge]]。
- **最后 commit**:`7c80ee7`(恢复 home-18·修超管用户页)/ `b078e39`(admin 引全套 home-NN)/ `ea422f9`(MR.ERP 卡对齐)/ `256df28`(DMS-UI-004 地理解析)· `git log --oneline -8` 查最新。**均已 push 上线·prod 健康**。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
