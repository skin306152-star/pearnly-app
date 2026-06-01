# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-01 · MR.ERP DMS 第2轮复测:R1 硬门槛 PASS·无 Blocker · R5/R7 两 non-Blocker FAIL 已修 + 向导隐藏 DMS 地址 上线 `0d1c380` · ⏳等第3轮复测)

- **模式**:整顿封锁期 · **整顿主线暂停**。当前是 **Zihao 例外任务:MR.ERP DMS 汽车销售 身份证→订车单 集成**(adapter=`mrerp_dms`·非整顿·commit tag `MRERP-DMS-INTEGRATION`)。整顿主线候选(待 Zihao 拍板恢复):app.py 1727→500 / home.html 1730→1000 / src/home/*.css(现 0·目标 20-30)。**home.js 拆迁批1-9g2 已全收官 33768→0·已上线验**。
- **首轮(R1)6 缺陷已修上线**:003(身份证不转PDF+PDF栅格化兜底)/005(DMS 不入推送列表)/TC1.4(测试按钮 POST)/006(错误码 i18n)`733b3a9` · 001(登录点击竞态)`4c35dce` · **004(Critical 新建客户 ERR_DMS_CUSTOMER_CREATE)`256df28`**=根因建客户时省/区/街道/邮编 select 发空串被 cus/new.php 拒,修=`_resolve_address_geo` 把地址文字级联解析成 DMS 主档 ID(泰文前缀归一+逐级兜底)。测试计划 `docs/integrations/mrerp-dms-ui-test-plan.md`。详见记忆 [[mrerp-dms-integration]]。
- **✅ Codex 第2轮复测结果(报告 `_uitest/dms-ui-20260601-r2-full/report.md`)**:**R1 硬门槛 PASS**(全新身份证→建客户 91 + 订车单 PNTEST6010180601·省/区/街道/邮编已填)·**无 Blocker**。R2/R3/R4/R6 全 PASS。两 non-Blocker FAIL 已修上线:**R5(i18n)**=`_DMS_FRIENDLY`(erp_push.py)只有 zh/en/th/zh_TW·错凭据日文回退英文→补全 7 条真日文 `ja` 键 + 回归测试 `test_dms_friendly_i18n.py` 锁 ja≠en;**R7(视觉)**=DMS 卡按钮 测试→修改→停用 改 **修改→测试→停用** 对齐财务卡。另按 Zihao 要求 **向导隐藏「DMS 地址」字段**(地址写死·只此一个 DMS 实例·只留 账号/密码/订车单号前缀)。commit `63197c6`+`0d1c380`·全量 2147 OK·prod bundle 字节验过。
- **⏳ 闭环判定**:DMS 代码侧首轮 6 缺陷 + 二轮 2 项 non-Blocker **全修上线**,**尚未闭环**——等 Codex **第3轮复测**(R5 错凭据日文真显日文 / R7+隐藏地址 向导外观)。复测过 = 闭环 → 切回整顿主线;有 FAIL → 逐条核对修。**下个窗口先看 Codex 第3轮报告**。R7+隐藏地址 真浏览器视觉本窗口未自验(仅 dist 字节确认)·交第3轮坐实。
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
