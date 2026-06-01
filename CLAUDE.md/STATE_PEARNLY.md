# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-01 · **整顿主线 C3 进行中** · R15 抽 `#bank-cand-drawer` · home.html 1495→1473 上线 prod 11850054)

- **模式**:整顿封锁期 · **整顿主线 C3 进行中**(Zihao 2026-06-01 拍板:DMS 全链路收尾闭环 → 回整顿)。**当前 task = C3 拆 home.html → <1000**:本窗口 R15 后 **1473**(还差 ~473)。下个候选(由易到难):on-demand modal(客户编辑/账套等·逐个查消费模块绑定时机)/ page-ocr(~150·识别主页高耦合·留最后)。**app shell(顶栏~128/侧栏~143)boot 关键勿轻动**。
- **✅ MR.ERP DMS 例外任务全链路闭环**(commit tag `MRERP-DMS-INTEGRATION`·非整顿):① 集成上线(身份证→订车单·Playwright 真登录+表单契约·防误推三重保险)② Codex 3 轮 UI 复测全 PASS(首轮 6 缺陷+二轮 R5/R7+隐藏地址全修)③ 推送可视化 UX(推送日志/异常栏 ERP 下拉筛选 + 身份证订车按 DMS 字段〔订车单号/客户/身份证末4〕展示 + 4 语友好错误不裸露 ERR_* + 详情/弹窗 DMS 标签)④ 导航文案统一(上传发票→上传识别 / 发票记录→识别记录·4 语)。**全程发票推送零改动**·全量 2153 + prod E2E 绿。详见记忆 [[mrerp-dms-integration]] + 交接 `docs/integrations/mrerp-dms-integration-handoff.md`。
- **C3 进度封存**:home.html 1730→**1473**(R13 抽 `#page-history`→`page-history.js` `4d3b9e0` + R14 抽 `#onboarding-modal`→`welcome-wizard-html.js` 懒注入 `99c5da4` + **R15 抽 `#bank-cand-drawer` inner→`bank-cand-drawer-html.js` eval 注入 `277b377`(-22)**·均字节等价+prod E2E 验)。范式见记忆 [[wb-src-home-c3-split-playbook]](R15 同 modal-notif-new 款:留空壳 + `*-html.js` eval 期注入 inner + 子树初译 + import 置消费模块前;消费模块 load()/_bindOnce 按需绑定→eval 注入恒早于首次绑定·非竞态)。app.py 1731→500 仍卡 auth 专窗口(剩高敏 @app·需 Zihao 在场)。
- **🔑 部署 cache-bust 铁律(今日血泪·必守)**:静态资源 `Cache-Control: immutable max-age=30d`·改 `static/dist/main.js`(npm run build 后)/`static/i18n-data.js`/`static/home-NN.css` 后**必须 bump home.html 对应 `?v=`**,否则缓存用户拿不到(Playwright/Codex 无缓存→E2E 过≠真用户生效)。`/api/version` 从 `dist/main.js?v=` 自动读·bump 版本必配 4 语 release_notes(`meta_aliases_routes.py`·铁律 #6)。详见记忆 [[fe-cache-bust-vparam-required]]。
- **部署铁律**:改 src/*.js 必 `npm run build` + commit `static/dist` + bump `?v=`(纯后端 .py 免 build/免 bump);home.html/css/i18n-data.js 是 CRLF+prettierignored·禁 sed/prettier·只 Edit 或 Python `newline=''`;pre-push 机械闸跑 ruff/black/eslint(0 error)/build·本地 scratch 文件勿留(会被扫)。**E2E 部署后首跑常因后端冷启动登录瞬态失败·重试即过**。
- **防误推三重保险(高危·别动)**:mrerp_dms `auto_push` 强制 false · 不进发票抽屉推送列表(ocr-push.js 过滤)· push_to_endpoint 硬拒 `ERR_DMS_NOT_INVOICE_ENDPOINT` · 身份证自动推送另用 `config.id_card_auto_push`。计费 kind=pdf units=1 不污染发票额度。
- **测试账号**:Pearnly 真数据号 `18685123459@163.com`/`xiaopi19950730..`(谨慎);e2e_1/2/3 见 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`(e2e_1=`pearnly_e2e_1`/`Pe@rnly-E2E-1k9`·只读验证用·**无 DMS 数据**·DMS 真实视觉须 skin306152 眼验);DMS 测试站 `dmstest`/`dmstest`(只本地 env 注入)。
- **最后 commit**:`277b377`(C3 R15 抽 `#bank-cand-drawer` inner→运行期注入 · REFACTOR-WB-C3 · bump `?v=` 11850053→11850054 + release_notes 改稳定性/性能)· `git log --oneline -8` 查最新。**均已 push 上线·prod 11850054 健康**。home.js 拆迁全收官 33768→0(范式 [[home-js-batch-split-bridge]])。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
