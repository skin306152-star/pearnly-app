# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-01 · ✅ **C3 超额达标:home.html 1495→661**(R15~R24·目标<1000)· 5 大巨石 4/5 · 仅剩 app.py · 上线 prod 11850062)

- **模式**:整顿封锁期 · **✅ C3(拆 home.html → <1000)本窗口超额达标**:home.html 1495→**661**(目标 <1000·refactor_progress 100%)。**5 大巨石 4/5 完成**(home.js 0/home.css 0/db.py 344/home.html 661 ✅)· **仅剩 app.py 1731→500**(卡 auth 专窗口·剩高敏 @app 路由·需 Zihao 在场·铁律 #26 🔴)。**下个 task = app.py 或 Zihao 指派**。**home.html 已到实际压缩地板 ≈661**:剩余最大块全是 app shell(顶栏 topbar-right~108 + 侧栏 nav ~96·**boot 关键·R3 曾竞态 revert·勿动**)+ 内联 `<style>`~73(**故意 inline 防 home.css.gz 陈旧·勿移**)+ `drawer`(OCR详情·ocr-results 重建 innerHTML 纠缠)/`int-drawer`(DOM-move)/`exc-drawer`(改 VAT·C9-blocked)—— 再压必碰高风险/高敏·非必要不动。孤儿 i18n key(billing-modal-title/help/google-open)无害·可日后清。
- **✅ MR.ERP DMS 例外任务全链路闭环**(commit tag `MRERP-DMS-INTEGRATION`·非整顿):① 集成上线(身份证→订车单·Playwright 真登录+表单契约·防误推三重保险)② Codex 3 轮 UI 复测全 PASS(首轮 6 缺陷+二轮 R5/R7+隐藏地址全修)③ 推送可视化 UX(推送日志/异常栏 ERP 下拉筛选 + 身份证订车按 DMS 字段〔订车单号/客户/身份证末4〕展示 + 4 语友好错误不裸露 ERR_* + 详情/弹窗 DMS 标签)④ 导航文案统一(上传发票→上传识别 / 发票记录→识别记录·4 语)。**全程发票推送零改动**·全量 2153 + prod E2E 绿。详见记忆 [[mrerp-dms-integration]] + 交接 `docs/integrations/mrerp-dms-integration-handoff.md`。
- **C3 收官封存**:home.html 1730→**661**(本窗口 R15~R24 共 **-834**·抽 12 modal/drawer/page + 删 1 死 modal·全 R6 运行期注入范式):R15 bank-cand-drawer + R16 client/wsclient-modal + R17 camera-tips/bank-client-picker + R18 endpoint-modal(⚠️无守卫IIFE) + R19 **删**死 billing-modal + R20 两 confirm-modal + R21 **page-ocr**(默认主页·高扇出 `eaa1299`) + R22 **cmdk-mask**(命令面板·跨<1000 `3d7f7db`) + R23 **email-modal**(邮箱抓取·≠LINE高敏 `b5a9e35`) + R24 **page-test-center**(skin-only `4f59bdb`)(更早 R13 page-history/R14 onboarding)·抽出均字节等价〔脚本提取+校验模板===git HEAD inner〕+prod E2E 验〔R16/R20 开弹窗·R21 选文件→file-list·R22 Cmd+K·R23/R24 注入检查+boot 零 error〕)。新增 src/home/*-html.js 注入模块 8 个。范式见记忆 [[wb-src-home-c3-split-playbook]](留空壳 + eval 注入 inner + 子树初译 + import 置消费模块前;消费者 on-demand/DOMContentLoaded/eval-IIFE 守卫或无守卫均可·eval 注入恒早于首次绑定·非竞态)。
- **🔑 部署 cache-bust 铁律(今日血泪·必守)**:静态资源 `Cache-Control: immutable max-age=30d`·改 `static/dist/main.js`(npm run build 后)/`static/i18n-data.js`/`static/home-NN.css` 后**必须 bump home.html 对应 `?v=`**,否则缓存用户拿不到(Playwright/Codex 无缓存→E2E 过≠真用户生效)。`/api/version` 从 `dist/main.js?v=` 自动读·bump 版本必配 4 语 release_notes(`meta_aliases_routes.py`·铁律 #6)。详见记忆 [[fe-cache-bust-vparam-required]]。
- **部署铁律**:改 src/*.js 必 `npm run build` + commit `static/dist` + bump `?v=`(纯后端 .py 免 build/免 bump);home.html/css/i18n-data.js 是 CRLF+prettierignored·禁 sed/prettier·只 Edit 或 Python `newline=''`;pre-push 机械闸跑 ruff/black/eslint(0 error)/build·本地 scratch 文件勿留(会被扫)。**E2E 部署后首跑常因后端冷启动登录瞬态失败·重试即过**。
- **防误推三重保险(高危·别动)**:mrerp_dms `auto_push` 强制 false · 不进发票抽屉推送列表(ocr-push.js 过滤)· push_to_endpoint 硬拒 `ERR_DMS_NOT_INVOICE_ENDPOINT` · 身份证自动推送另用 `config.id_card_auto_push`。计费 kind=pdf units=1 不污染发票额度。
- **测试账号**:Pearnly 真数据号 `18685123459@163.com`/`xiaopi19950730..`(谨慎);e2e_1/2/3 见 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`(e2e_1=`pearnly_e2e_1`/`Pe@rnly-E2E-1k9`·只读验证用·**无 DMS 数据**·DMS 真实视觉须 skin306152 眼验);DMS 测试站 `dmstest`/`dmstest`(只本地 env 注入)。
- **最后 commit**:`4f59bdb`(C3 R24 抽测试中心页 `#page-test-center`→运行期注入 · bump `?v=` 11850061→11850062)· `git log --oneline -14` 查最新。**均已 push 上线·prod 11850062 健康**。**整顿轮 cache-bust:仍 bump `?v=` 保缓存正确,但不重写 release_notes(Zihao 2026-06-01:纯重构忽视新版本横幅·见记忆 [[refactor-skip-version-banner]])**。home.js 拆迁全收官 33768→0(范式 [[home-js-batch-split-bridge]])。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
