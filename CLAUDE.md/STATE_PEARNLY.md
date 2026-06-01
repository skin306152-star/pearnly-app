# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-01 · ✅ **C3 超额达标 home.html 1495→661** + 去AI味/DRY 整改 · **下个 task = app shell 抽 JS**(Zihao 坚持·见计划书)· prod 11850063)

- **模式**:整顿封锁期 · **✅ C3 拆 home.html 1495→661 超额达标**(refactor_progress 100%)+ **去AI味/DRY 整改上线**(抽 `wb-inject.js` 公共助手·10 模块去重·注释 emoji 清·净 -171 行 `a9ab308`)。**5 大巨石 4/5 完成**(home.js 0/home.css 0/db.py 344/home.html 661 ✅·仅剩 app.py 1731→500 卡 auth 专窗口·需 Zihao 在场·铁律 #26 🔴)。
- **🔴 下个 task = app shell(顶栏 L155-281 + 侧栏 L284-422)抽进 JS**(Zihao 2026-06-01 坚持要做到 Claude 级「view-source 连框架都只见外壳」)。**最高风险一块**(永久可见框架 → FOUC 闪屏险 + core-boot eval 期绑 .nav-item 的 R3 竞态雷区 + 全 app blast radius)。**必读完整作业书 `docs/refactor/APP_SHELL_EXTRACTION_PLAN.md`**:用 `wb-inject` + import 置 core-boot(line 12)前(page-ocr-html 已证此位 line 11 可行)+ **CSS 骨架屏防闪** + **本地反代真浏览器逐页验**(切每页/权限显隐/汉堡/cmdk/无闪)验透才 push·红即回滚。**别直接 push 试 = 重蹈 R3**。
- **🛡️ 新增守门第 7 道 `check_ai_smell`**(2026-06-01·堵「去AI味」漏)：pre-push 机械拦本次改动 src JS 的【注释 emoji】+【console.log 调试残留】(模板内产品 emoji 放行)。脚本 `scripts/check_ai_smell.py`。前 6 道无一查 AI 味→自动 loop 必漏,故机械化。
- **✅ MR.ERP DMS 例外任务全链路闭环**(commit tag `MRERP-DMS-INTEGRATION`·非整顿):① 集成上线(身份证→订车单·Playwright 真登录+表单契约·防误推三重保险)② Codex 3 轮 UI 复测全 PASS(首轮 6 缺陷+二轮 R5/R7+隐藏地址全修)③ 推送可视化 UX(推送日志/异常栏 ERP 下拉筛选 + 身份证订车按 DMS 字段〔订车单号/客户/身份证末4〕展示 + 4 语友好错误不裸露 ERR_* + 详情/弹窗 DMS 标签)④ 导航文案统一(上传发票→上传识别 / 发票记录→识别记录·4 语)。**全程发票推送零改动**·全量 2153 + prod E2E 绿。详见记忆 [[mrerp-dms-integration]] + 交接 `docs/integrations/mrerp-dms-integration-handoff.md`。
- **C3 收官封存**:home.html 1730→**661**(本窗口 R15~R24 共 **-834**·抽 12 modal/drawer/page + 删 1 死 modal·全 R6 运行期注入范式):R15 bank-cand-drawer + R16 client/wsclient-modal + R17 camera-tips/bank-client-picker + R18 endpoint-modal(⚠️无守卫IIFE) + R19 **删**死 billing-modal + R20 两 confirm-modal + R21 **page-ocr**(默认主页·高扇出 `eaa1299`) + R22 **cmdk-mask**(命令面板·跨<1000 `3d7f7db`) + R23 **email-modal**(邮箱抓取·≠LINE高敏 `b5a9e35`) + R24 **page-test-center**(skin-only `4f59bdb`)(更早 R13 page-history/R14 onboarding)·抽出均字节等价〔脚本提取+校验模板===git HEAD inner〕+prod E2E 验〔R16/R20 开弹窗·R21 选文件→file-list·R22 Cmd+K·R23/R24 注入检查+boot 零 error〕)。新增 src/home/*-html.js 注入模块 8 个。范式见记忆 [[wb-src-home-c3-split-playbook]](留空壳 + eval 注入 inner + 子树初译 + import 置消费模块前;消费者 on-demand/DOMContentLoaded/eval-IIFE 守卫或无守卫均可·eval 注入恒早于首次绑定·非竞态)。
- **🔑 部署 cache-bust 铁律(今日血泪·必守)**:静态资源 `Cache-Control: immutable max-age=30d`·改 `static/dist/main.js`(npm run build 后)/`static/i18n-data.js`/`static/home-NN.css` 后**必须 bump home.html 对应 `?v=`**,否则缓存用户拿不到(Playwright/Codex 无缓存→E2E 过≠真用户生效)。`/api/version` 从 `dist/main.js?v=` 自动读·bump 版本必配 4 语 release_notes(`meta_aliases_routes.py`·铁律 #6)。详见记忆 [[fe-cache-bust-vparam-required]]。
- **部署铁律**:改 src/*.js 必 `npm run build` + commit `static/dist` + bump `?v=`(纯后端 .py 免 build/免 bump);home.html/css/i18n-data.js 是 CRLF+prettierignored·禁 sed/prettier·只 Edit 或 Python `newline=''`;pre-push 机械闸跑 ruff/black/eslint(0 error)/build·本地 scratch 文件勿留(会被扫)。**E2E 部署后首跑常因后端冷启动登录瞬态失败·重试即过**。
- **防误推三重保险(高危·别动)**:mrerp_dms `auto_push` 强制 false · 不进发票抽屉推送列表(ocr-push.js 过滤)· push_to_endpoint 硬拒 `ERR_DMS_NOT_INVOICE_ENDPOINT` · 身份证自动推送另用 `config.id_card_auto_push`。计费 kind=pdf units=1 不污染发票额度。
- **测试账号**:Pearnly 真数据号 `18685123459@163.com`/`xiaopi19950730..`(谨慎);e2e_1/2/3 见 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`(e2e_1=`pearnly_e2e_1`/`Pe@rnly-E2E-1k9`·只读验证用·**无 DMS 数据**·DMS 真实视觉须 skin306152 眼验);DMS 测试站 `dmstest`/`dmstest`(只本地 env 注入)。
- **最后 commit**:`a9ab308`(去AI味+DRY·抽 wb-inject.js·11850063)之后再 1 个 docs/gate commit · `git log --oneline -16` 查最新。**均已 push 上线·prod 11850063 健康**。**整顿轮 cache-bust:仍 bump `?v=` 保缓存正确,但不重写 release_notes(Zihao 2026-06-01:纯重构忽视新版本横幅·见记忆 [[refactor-skip-version-banner]])**。home.js 拆迁全收官 33768→0。本窗口收尾:home.html R15~R24 共 -834·新增 8 注入模块 + wb-inject 助手·去AI味机械闸·app shell 计划书待下窗口执行。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
