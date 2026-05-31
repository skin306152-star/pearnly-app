# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-05-31 批9a/9b 收尾重写)

- **模式**:整顿封锁期 · 0 新功能 · 当前主线 = **home.js 拆迁**(批1-8✅ + 批9 地基**分多极小步**进行中:9a/9b✅·下一步见末)。
- **批1-9b 全闭环**(…/c9effd3/78cd513/536c317 已上线·prod 逐一验过):批1-5 见 archive;批6 `toast.js`;批7 `settings-core.js`;批8 `permissions.js`+`layout.js`;**批9a `recon-drawer.js`**(泰国RD税务核验 rdFetch/callRdVerify/callRdSync/openRdSyncModal+_helpers·只 callRdVerify/callRdSync 挂 window);**批9b `ocr-fields.js`**(mergeFields/onFieldEdit/updateDrawerEditCount)。**home.js 5344→1992(净减3352·降63%·进度94%)**· 每批 6 道守门全绿 + 真账号真后端 E2E 验过。
- **批9 拆法**:地基不一次搬·分极小步先清**自包含/handler-时**的非核心块(9a RD税务·9b OCR字段)·真核心最后。**真核心(必留 home.js 当桥·~70模块裸读)**:t/escapeHtml/svgIcon/showConfirm/apiGet系/_wsHeader/applyLang/setupDropdown/routeTo/loadAll + 全局状态 let(currentLang/currentRoute/_userInfo/_results/token/_quota/_engineCheckTimer 等·模块顶层 let 是模块作用域·别的脚本读不到·故状态必留 home.js)+ 引导期 IIFE/bootstrap(1786 applyLang/1789 routeTo/1801 loadAll 同步调)。
- **剩余 home.js≈1992 的成分**:① 真核心地基(上条·最后小步搬·搬 applyLang/routeTo 需模块自举重渲);② 🔴**高敏**(铁律#26·需 Zihao 在场):`showForceChangePasswordModal`(改密)、LINE Bot 面板 IIFE(1690·LINE绑定)、apiGet/apiPost 的 auth 重定向、`_showSessionRevokedModal`;③ 高扇出 `showConfirm`(18模块裸调·非高敏但搬需 window 桥先就绪);④ 死代码 `renderPageHeadInfo`/`openDiagnoseDialog`(0 调用方·可删需确认)。
- **大块拆法(批4/5 验证·批7-9 照用)**:单块 >500 拆 N 个 <500 子模块;共享态(_historyState/_selectedFiles/mergeFields)留 home.js 顶层当桥(两边 bare 读写·属性 mutation 不触发 no-global-assign·重新赋值标 :writable);子模块循环依赖经 window 桥 OK(调用都在 handler 内·延迟解析);bootstrap 期(applyLang/用户初始化)裸调移出函数加 `typeof window.fn==='function'` 守卫+模块按 currentRoute 自举。
- **拆迁范式(批2-9 照用)**:home.js 是经典脚本(非IIFE)→ 顶层 `let`(_results/_drawerIdx 等)模块裸读写自动桥;移出函数 home.js/别的模块仍调需 `window.X=X` 挂出;`/* global */` 写全局·要**写**的标 `:writable`;移文件用 node split/join 保 home.js CRLF(对边界行先断言防误删·两块不连续要分别删)。
- **真浏览器验法(本窗复用成功)**:本地 node 反代(`_uitest/proxy.cjs`:拦 /static/home.js+dist/main.js(.map)返本地·其余透传 prod·改写 Origin/Referer→prod·删 CSP·Location 改回 localhost)+ tests/e2e 临时 spec(内联轻量登录·**别用 auth.js 的 waitForURL until:load·经反代长连接会拖住 load 假超时**·改等 token+window.showToast 就绪)· 用完即删不 commit。
- **测试账号**:e2e_1/2/3 余额满999999·密码在 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`(**格式:密码后接3空格+说明·只取首段非空白串·grep 须锚 `^username:` 否则命中 $env 行取错·tr -d '\r'**·env注入不打印)。真数据账号= 邮箱 `18685123459@163.com` / `xiaopi19950730..`。
- **剩余瓶颈**:home.js 1992→目标200(还差~1792·全是真核心+高敏+高扇出·搬完只剩 IIFE 外壳→删 home.html `<script src=/static/home.js>`)· app.py 1727→500· 模块化缺 CSS。
- **下一步建议(批9c+)**:① 安全:showConfirm→ui-confirm.js(18模块·确认无 eval 期裸调后搬·window 桥先就绪)、setupDropdown 留(718 引导期调)、死代码 renderPageHeadInfo/openDiagnoseDialog 确认后删;② 🔴高敏(Zihao 在场):LINE 面板 IIFE→line-panel.js、showForceChangePasswordModal→force-pw.js;③ 真核心 t/escapeHtml/api/applyLang/routeTo/loadAll 最后·极小步·搬 applyLang 需模块自举 `applyLang(currentLang)` 重应用语言(否则引导期 1786 裸调失败→页面初始语言不应用)。
- **最后 commit**:536c317(批9b)· `git log --oneline -5` 查最新。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
