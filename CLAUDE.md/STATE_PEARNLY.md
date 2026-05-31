# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-05-31 批9f 真核心 cutover 收尾重写)

- **模式**:整顿封锁期 · 0 新功能 · 当前主线 = **home.js 拆迁**(批1-9f✅·真核心已 cutover·home.js 5344→874·降84%·进度97%。下一步=9g 共享状态迁 window 才能彻底删 home.js·见末)。
- **批1-9f 全闭环**(批1-9e 已上线 prod 逐一验过;**批9f `2c2ea78` 已 commit·待 Zihao 拍板 push**):批6-9e=toast/settings-core/permissions+layout/recon-drawer/ocr-fields/force-pw🔴/line-panel🔴/confirm-modal。**批9f 真核心 cutover**:t/escapeHtml/svgIcon/_showSessionRevokedModal🔴/api簇🔴(铁律#26)→`src/home/core.js`(254行);applyLang/setupDropdown/routeTo/loadAll/render助手/installNetworkBanner+VALID_ROUTES+bootstrap→`core-boot.js`(471行);main.js 第1/2 import。每批 6 道守门全绿 + 真账号 E2E(9f:登录→8路由→4语→apiGet→render·0 pageerror·bootstrap loadAll 真后端 resolve)。
- **🔴 9f 已完成·剩 9g「状态迁 window 才能删 home.js」(高敏·plan-first)**:home.js 现 874 行=状态壳(`let currentLang/_userInfo/_quota/token/I18N/_results...`)+ 全局错误拦截 IIFE(最早 wrap fetch·留 sync)+ 若干独立 IIFE/绑定。**彻底删 `<script src=home.js>` 受阻于**:32 模块裸读 currentLang/15 读 currentRoute 等靠 home.js 顶层 let 的全局词法桥 → 要先把这 40+ 处跨模块裸读状态逐一迁 `window.*`(逻辑改·非 0 逻辑改)=9g 范围。死码 renderPageHeadInfo/openDiagnoseDialog(0 调用方)可顺带清。
- **拆 2 文件而非 1 的原因**:整簇 verbatim≈750 行破 <500 铁律 → core.js(叶子工具+鉴权)+ core-boot.js(编排+引导)·均<500·core 先 import·core-boot 裸调经 window 解析到 core。
- **大块拆法(批4/5 验证·批7-9 照用)**:单块 >500 拆 N 个 <500 子模块;共享态(_historyState/_selectedFiles/mergeFields)留 home.js 顶层当桥(两边 bare 读写·属性 mutation 不触发 no-global-assign·重新赋值标 :writable);子模块循环依赖经 window 桥 OK(调用都在 handler 内·延迟解析);bootstrap 期(applyLang/用户初始化)裸调移出函数加 `typeof window.fn==='function'` 守卫+模块按 currentRoute 自举。
- **拆迁范式(批2-9 照用)**:home.js 是经典脚本(非IIFE)→ 顶层 `let`(_results/_drawerIdx 等)模块裸读写自动桥;移出函数 home.js/别的模块仍调需 `window.X=X` 挂出;`/* global */` 写全局·要**写**的标 `:writable`;移文件用 node split/join 保 home.js CRLF(对边界行先断言防误删·两块不连续要分别删)。
- **真浏览器验法(本窗复用成功)**:本地 node 反代(`_uitest/proxy.cjs`:拦 /static/home.js+dist/main.js(.map)返本地·其余透传 prod·改写 Origin/Referer→prod·删 CSP·Location 改回 localhost)+ tests/e2e 临时 spec(内联轻量登录·**别用 auth.js 的 waitForURL until:load·经反代长连接会拖住 load 假超时**·改等 token+window.showToast 就绪)· 用完即删不 commit。
- **测试账号**:e2e_1/2/3 余额满999999·密码在 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`(**格式:密码后接3空格+说明·只取首段非空白串·grep 须锚 `^username:` 否则命中 $env 行取错·tr -d '\r'**·env注入不打印)。真数据账号= 邮箱 `18685123459@163.com` / `xiaopi19950730..`。
- **剩余瓶颈**:home.js 874→目标200(剩~674·=状态壳+错误IIFE+独立IIFE·要删需先做 9g 状态迁 window)· app.py 1727→500· 模块化缺 CSS。
- **9g 落地要点(状态迁 window·高敏·plan-first)**:① grep 全 src 裸读 currentLang(32)/currentRoute(15)/_userInfo/_quota/_results 等共享 let;② 逐个改 `window.X`(home.js 侧 `let X` 改 `window.X=初值` + 全 src 裸读改 window.X·属逻辑改);③ 每改一组真浏览器全功能回归;④ 全迁完 home.js 只剩错误IIFE+少量绑定→评估能否删 `<script src=home.js>`(错误IIFE 须最早 wrap fetch·可能仍需留极小 sync 头)。app.py 拆登录/OCR/计费仍属 🔴高敏需 Zihao 在场。
- **最后 commit**:658c5b0(批9e)· `git log --oneline -5` 查最新。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
