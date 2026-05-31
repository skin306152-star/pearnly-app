# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-01 · MR.ERP DMS UI 实测首轮回归 · 4 缺陷已修上线 v11850050 · ⏳等 Codex 复测)

- **模式**:整顿封锁期 · **整顿主线暂停**。当前是 **Zihao 例外任务:MR.ERP DMS 汽车销售 身份证→订车单 集成**(adapter=`mrerp_dms`·非整顿·commit tag `MRERP-DMS-INTEGRATION`)。整顿主线候选(待 Zihao 拍板恢复):app.py 1727→500 / home.html 1730→1000 / src/home/*.css(现 0·目标 20-30)。**home.js 拆迁批1-9g2 已全收官 33768→0·已上线验**。
- **⏳ 当前状态:UI 实测首轮回归完成 · 4 缺陷已修上线(commit 733b3a9 · prod v11850050)**:DMS-UI-003(Blocker)身份证不转PDF+后端PDF栅格化兜底 / DMS-UI-005(Blocker)DMS 不入发票推送列表(connectors_status 过滤) / TC1.4(Major)测试按钮 GET→POST / DMS-UI-006(Major)错误码 i18n 兜底+4语补键。测试计划已收录 `docs/integrations/mrerp-dms-ui-test-plan.md`。**DMS-UI-004(Critical·新建客户 ERR_DMS_CUSTOMER_CREATE)未修**:疑点=建客户时省/区/街道/邮编 DMS 地理主档 ID 为空 → 待 dmstest live 探查 cus/new.php 表单契约。**当前等 Codex 复测**。
- **DMS 集成已完成上线**(主体 `2b63ecd`+`a355451`+`80bdc23` / 登录修复 `4c35dce`·prod 版本 `11850043`·deploy ok 无回滚)。后端 live 端到端真验:DMS 测试站真建订车单(customer 65 / booking_id 16 / PN0010100531 / sc::1)。架构=Playwright 真登录 + 鉴权上下文驱动官方表单契约(铁律#7)。落点:`services/erp/mrerp_dms_{models,xlsx,client,adapter}.py` / `dms_routes.py`(app.py 仅 include_router) / `services/ocr/id_card_extract.py`(独立 prompt 不碰发票) / 前端 `src/home/{erp-mrerp-dms-connect,ocr-document-mode,dms-id-card-results}.js`。详见记忆 [[mrerp-dms-integration]] + 交接文档 `docs/integrations/mrerp-dms-integration-handoff.md`。
- **已修 DMS-UI-001(Blocker)`4c35dce`**:DMS 登录 `#btnlogin` 处理器绑在 window `load`(非 DOMContentLoaded)·原 login() 等 domcontentloaded 就点击=空操作→间歇 `ERR_DMS_AUTH`。修=`wait_until="load"` + 监听 `checklogin.php` 响应判成败(`lct::*::*`=成功 / `al::`/`err::`=拒绝·DMS 拒绝走自定义 modal 非原生 alert)+ 点击重试3次。验:好凭据 5/5、坏凭据 1.4s 秒判 AUTH。
- **防误推三重保险(高危·别动)**:mrerp_dms `auto_push` 强制 false · 不进发票抽屉推送列表(ocr-push.js 过滤)· push_to_endpoint 硬拒(`ERR_DMS_NOT_INVOICE_ENDPOINT`)· 身份证自动推送另用 `config.id_card_auto_push`。schema:Alembic 007 + push_schema ensure 双跑(canonical 加 mrerp_dms·skip 改全量校验防 CheckViolation)。计费按普通图片 OCR(kind=pdf units=1·不污染发票额度)。
- **测试账号**:Pearnly `18685123459@163.com` / `xiaopi19950730..`(真数据账号·谨慎);DMS 测试站 `https://www.mrerp4sme.com/dms/index.php` `dmstest`/`dmstest`(只本地 env 注入·绝不入库/日志/commit)。e2e_1/2/3 见 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`。
- **部署铁律**:改 src/*.js 必 `npm run build` + `git add static/dist` + bump home.html `dist/main.js?v=`(纯后端 .py 改动免 build/免 bump);home.html/css/i18n-data.js 是 CRLF+prettierignored·禁 sed/prettier·只 Edit 或 node split/join;pre-push 机械闸跑 ruff/black/eslint(0 error·会扫本地 scratch 文件勿留)/build·先 format 再 push。
- **home.js 拆迁全收官**(33768→0)·拆迁范式沉淀记忆 [[home-js-batch-split-bridge]]。
- **最后 commit**:`828bc74`(文档+收录测试计划)/ `733b3a9`(UI 实测修 4 缺陷·v11850050)· `git log --oneline -6` 查最新。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
