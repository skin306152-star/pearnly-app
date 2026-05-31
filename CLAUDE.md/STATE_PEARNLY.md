# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-05-31 批9g-1 收尾重写)

- **模式**:整顿封锁期 · 0 新功能 · 当前主线 = **home.js 拆迁**(批1-9g1✅·home.js 5344→381·降93%·进度97%→见 refactor_progress。下一步=9g-2 状态迁 window + 收 preboot 彻底删 home.js·见末)。
- **批1-9f 全闭环**(批1-9e 已上线 prod 逐一验过;**批9f `2c2ea78` 已 commit·待 Zihao 拍板 push**):批6-9e=toast/settings-core/permissions+layout/recon-drawer/ocr-fields/force-pw🔴/line-panel🔴/confirm-modal。**批9f 真核心 cutover**:t/escapeHtml/svgIcon/_showSessionRevokedModal🔴/api簇🔴(铁律#26)→`src/home/core.js`(254行);applyLang/setupDropdown/routeTo/loadAll/render助手/installNetworkBanner+VALID_ROUTES+bootstrap→`core-boot.js`(471行);main.js 第1/2 import。每批 6 道守门全绿 + 真账号 E2E(9f:登录→8路由→4语→apiGet→render·0 pageerror·bootstrap loadAll 真后端 resolve)。
- **批9g-1 已上线(`276145e`·home.js 874→381)**:删 4 段死码(_planDisplayLabel/openDiagnoseDialog/renderPageHeadInfo/nav-locked 空 no-op)+ 抽 7 独立 IIFE/绑定→bundle:`sidebar-nav`/`integration-drawer`(window.openIntegrationDrawer 等)/`settings-bind`/`engine-poll`(window.start/stopEnginePolling+_engineCheckTimer)/`drawer-events`/`misc-bindings`/`pearnly-confirm`。守门 6 道+prod 真账号 E2E(路由/侧栏/集成抽屉/pearnlyConfirm·0 pageerror)。
- **🔴 剩 9g-2「状态迁 window + 收 preboot 删 home.js」(高敏·plan-first)**:home.js 现 381 行=状态壳(`let currentLang/_userInfo/_quota/_results/_historyState...`)+ 全局错误拦截 IIFE(最早 wrap fetch)+ I18N/subscribeI18n + 大量注释残留。**关键机制已验证**:`let X`→`window.X=初值`后,模块裸读/裸写自动经全局对象解析到 window.X(只要 init 先于 bundle 跑)→**几乎不用动那 ~40 处模块**。9g-2 步骤:① state `let`→`window.X`;② 错误IIFE+state init+I18N+subscribeI18n+token检查 收进极小 `static/preboot.js`(sync 排 bundle 前)或内联;③ `<script src=home.js>`→preboot·删 home.js。白屏是首要风险·重点验 bootstrap/auth/切语言/路由。
- **⚠️ 部署铁律(9f/9g 踩坑补)**:改 home.js/main.js 内容必 bump home.html 的 `home.js?v=`+`main.js?v=` 到同新值(静态文件 `immutable` 30天·不 bump=回头客旧缓存+部分驱逐 mismatch 白屏)·bump 会改 /api/version(读 static/home.html 的 home.js?v=)→弹横幅→按铁律#6 写中性4语 release_notes。**禁 sed home.html(整文件 CRLF→LF 翻·实测中招)·只用 Edit 工具行内替换或 node split/join**。
- **大块拆法(批4/5 验证·批7-9 照用)**:单块 >500 拆 N 个 <500 子模块;共享态(_historyState/_selectedFiles/mergeFields)留 home.js 顶层当桥(两边 bare 读写·属性 mutation 不触发 no-global-assign·重新赋值标 :writable);子模块循环依赖经 window 桥 OK(调用都在 handler 内·延迟解析);bootstrap 期(applyLang/用户初始化)裸调移出函数加 `typeof window.fn==='function'` 守卫+模块按 currentRoute 自举。
- **拆迁范式(批2-9 照用)**:home.js 是经典脚本(非IIFE)→ 顶层 `let`(_results/_drawerIdx 等)模块裸读写自动桥;移出函数 home.js/别的模块仍调需 `window.X=X` 挂出;`/* global */` 写全局·要**写**的标 `:writable`;移文件用 node split/join 保 home.js CRLF(对边界行先断言防误删·两块不连续要分别删)。
- **真浏览器验法(本窗复用成功)**:本地 node 反代(`_uitest/proxy.cjs`:拦 /static/home.js+dist/main.js(.map)返本地·其余透传 prod·改写 Origin/Referer→prod·删 CSP·Location 改回 localhost)+ tests/e2e 临时 spec(内联轻量登录·**别用 auth.js 的 waitForURL until:load·经反代长连接会拖住 load 假超时**·改等 token+window.showToast 就绪)· 用完即删不 commit。
- **测试账号**:e2e_1/2/3 余额满999999·密码在 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`(**格式:密码后接3空格+说明·只取首段非空白串·grep 须锚 `^username:` 否则命中 $env 行取错·tr -d '\r'**·env注入不打印)。真数据账号= 邮箱 `18685123459@163.com` / `xiaopi19950730..`。
- **剩余瓶颈**:home.js 381→目标200(剩~181·=状态壳+错误IIFE+I18N+注释残留·9g-2 收 preboot 后归 0)· app.py 1727→500· 模块化缺 CSS。
- **9g-2 落地要点(高敏·plan-first·下轮做)**:① home.js 状态 `let X=初值`→`window.X=初值`(机制已验证·模块裸读写自动解析·**基本不动那 ~40 处模块**·仅留 eslint /* global */ 注释);② 错误IIFE+state init+I18N+subscribeI18n+token检查 收进极小 `static/preboot.js`(sync·排 i18n-data 后/bundle 前)或内联 `<script>`;③ `<script src=home.js>`→preboot·**删 home.js**(view-source 只剩外壳);④ bump ?v=+真账号 E2E(白屏首要风险·验 bootstrap/auth/切语言/路由/OCR热路径)。app.py 拆登录/OCR/计费仍属 🔴高敏需 Zihao 在场。
- **最后 commit**:658c5b0(批9e)· `git log --oneline -5` 查最新。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
