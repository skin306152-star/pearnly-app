# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-01 · ✅ **C3 完全收官 home.html 1495→398**〔R25 app shell 抽 JS 上线〕· 5 大巨石 4/5 · 仅剩 app.py · prod 11850064 健康)

- **模式**:整顿封锁期 · ✅ **C3 拆 home.html 全部收官 1495→398**(refactor_progress 100%)。本窗口 **R25 把 app shell(顶栏 `.topbar` + 侧栏 `#sidebar`)抽进 JS** → `src/home/app-shell-html.js` 运行期注入(`d720185`·home.html 661→398·-263)。view-source 连导航框架都只见外壳,达成 Zihao 要的 Claude 级。**5 大巨石 4/5 完成**(home.js 0/home.css 0/db.py 344/home.html 398 ✅·仅剩 **app.py 1731→500** 卡 auth 专窗口·需 Zihao 在场·铁律 #26 🔴)。
- **R25 app shell 范式+验证**:空壳 `<div class="topbar" id="topbar"></div>` + `<nav class="sidebar" id="sidebar"></nav>`(保 class/id·尺寸全由 CSS 给→空壳=满壳·零位移)·import 置 **core-boot 前**(main.js line 12·core-boot bootstrap `routeTo→querySelectorAll('.nav-item')` + sidebar-nav `getElementById('sidebar-toggle')` 无守卫消费者·漏则 boot 崩全 app 导航瘫=R3)。**本地反代真浏览器 + prod 双验透**:逐页路由/sidebar-toggle/cmdk/头像/移动端汉堡+遮罩全绿·官方 E2E 01/03/04 全过·无 console error·**CLS<0.05**。FOUC:重绘期约 12ms 单帧白条→内容浮现(白色定尺容器本身即骨架·不塌不变色)·Zihao 验收拍板上线。bump main.js?v=11850064。范式见记忆 [[wb-src-home-c3-split-playbook]]。
- **🛡️ 守门第 7 道 `check_ai_smell`**(2026-06-01·堵「去AI味」漏)：pre-push 机械拦本次改动 src JS 的【注释 emoji】+【console.log 调试残留】(模板内产品 emoji 放行)。脚本 `scripts/check_ai_smell.py`。
- **🔑 部署 cache-bust 铁律**:静态资源 `Cache-Control: immutable max-age=30d`·改 `static/dist/main.js`(npm run build 后)/`static/i18n-data.js`/`static/home-NN.css` 后**必须 bump home.html 对应 `?v=`**,否则缓存用户拿不到(Playwright/Codex 无缓存→E2E 过≠真用户生效)。`/api/version` 从 `dist/main.js?v=` 自动读。整顿轮 bump `?v=` 但不重写 release_notes(记忆 [[refactor-skip-version-banner]] [[fe-cache-bust-vparam-required]])。
- **部署铁律**:改 src/*.js 必 `npm run build` + commit `static/dist` + bump `?v=`(纯后端 .py 免 build/免 bump);home.html/css/i18n-data.js 是 CRLF+prettierignored·禁 sed/prettier·只 Edit 或 Python `newline=''`;pre-push 机械闸跑 ruff/black/eslint(0 error)/build/check_ai_smell·本地 scratch 文件勿留。**E2E 部署后首跑常因后端冷启动登录瞬态失败·重试即过**。
- **防误推三重保险(高危·别动)**:mrerp_dms `auto_push` 强制 false · 不进发票抽屉推送列表(ocr-push.js 过滤)· push_to_endpoint 硬拒 `ERR_DMS_NOT_INVOICE_ENDPOINT` · 身份证自动推送另用 `config.id_card_auto_push`。计费 kind=pdf units=1 不污染发票额度。MR.ERP DMS 全链路闭环详见记忆 [[mrerp-dms-integration]]。
- **测试账号**:e2e_1/2/3 见 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`(e2e_1=`pearnly_e2e_1`/`Pe@rnly-E2E-1k9`·只读验证用·**无 DMS 数据**);Pearnly 真数据号 `18685123459@163.com`(谨慎·当前 401 勿反复试);DMS 测试站 `dmstest`/`dmstest`(只本地 env 注入)。
- **最后 commit**:`d720185`(R25 app shell 抽 JS·11850064·已 push 上线·prod 双验绿)。home.html 拆迁全收官 1730→398(本窗口仅 R25·-263·新增 src/home/app-shell-html.js)。home.js 33768→0。`git log --oneline -10` 查最新。**下个 task = app.py 1731→500(高敏 auth·需 Zihao 在场·铁律 #26)**。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
