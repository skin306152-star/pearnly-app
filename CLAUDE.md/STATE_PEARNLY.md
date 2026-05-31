# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-05-31 批9a-9e 收尾重写)

- **模式**:整顿封锁期 · 0 新功能 · 当前主线 = **home.js 拆迁**(批1-8✅ + 批9 地基**分多极小步**进行中:9a-9e✅·只剩真核心切换·见末)。
- **批1-9e 全闭环**(…/27a3c46/658c5b0 已上线·prod 逐一验过):批6 `toast.js`;批7 `settings-core.js`;批8 `permissions.js`+`layout.js`;**批9a `recon-drawer.js`**(RD税务核验);**9b `ocr-fields.js`**(mergeFields/onFieldEdit/updateDrawerEditCount);**9c `force-pw.js`**(🔴改密 modal);**9d `line-panel.js`**(🔴LINE绑定面板 IIFE·243行);**9e `confirm-modal.js`**(showConfirm·18模块用)。**home.js 5344→1556(净减3788·降71%·进度95%)**· 每批 6 道守门全绿 + 真账号 E2E·9c/9d 高敏块 Zihao 明确授权搬(0逻辑改+E2E验+红即revert·绝不真付/真改密)。
- **🔴 只剩"真核心切换"(批9f·一次协调式 cutover·非极小步·建议 plan-first/新窗口做)**:t/escapeHtml/svgIcon/_wsHeader/apiGet/apiPost/apiPut/_showSessionRevokedModal/applyLang/setupDropdown/routeTo/loadAll(home.js 256-1072 一簇·~700行)+ 引导期 render 助手(renderBrandWorkspace/updateUploadHint/getMax*/installNetworkBanner)。**难点**:这些被 ~70 模块**eval 期**裸读 + home.js 同步引导(1786 applyLang/1789 routeTo/1801 loadAll)互相调用·不能像前面分块搬·要**整簇一起搬到 core.js(main.js 第一个 import)+ 把 bootstrap 也搬进模块尾**·import 顺序错=白屏。全局状态 let 仍留 home.js(壳)。搬完 home.js≈只剩状态壳→删 home.html `<script src=/static/home.js>`。
- **死代码可删(确认后)**:renderPageHeadInfo/openDiagnoseDialog(0 调用方)。
- **大块拆法(批4/5 验证·批7-9 照用)**:单块 >500 拆 N 个 <500 子模块;共享态(_historyState/_selectedFiles/mergeFields)留 home.js 顶层当桥(两边 bare 读写·属性 mutation 不触发 no-global-assign·重新赋值标 :writable);子模块循环依赖经 window 桥 OK(调用都在 handler 内·延迟解析);bootstrap 期(applyLang/用户初始化)裸调移出函数加 `typeof window.fn==='function'` 守卫+模块按 currentRoute 自举。
- **拆迁范式(批2-9 照用)**:home.js 是经典脚本(非IIFE)→ 顶层 `let`(_results/_drawerIdx 等)模块裸读写自动桥;移出函数 home.js/别的模块仍调需 `window.X=X` 挂出;`/* global */` 写全局·要**写**的标 `:writable`;移文件用 node split/join 保 home.js CRLF(对边界行先断言防误删·两块不连续要分别删)。
- **真浏览器验法(本窗复用成功)**:本地 node 反代(`_uitest/proxy.cjs`:拦 /static/home.js+dist/main.js(.map)返本地·其余透传 prod·改写 Origin/Referer→prod·删 CSP·Location 改回 localhost)+ tests/e2e 临时 spec(内联轻量登录·**别用 auth.js 的 waitForURL until:load·经反代长连接会拖住 load 假超时**·改等 token+window.showToast 就绪)· 用完即删不 commit。
- **测试账号**:e2e_1/2/3 余额满999999·密码在 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`(**格式:密码后接3空格+说明·只取首段非空白串·grep 须锚 `^username:` 否则命中 $env 行取错·tr -d '\r'**·env注入不打印)。真数据账号= 邮箱 `18685123459@163.com` / `xiaopi19950730..`。
- **剩余瓶颈**:home.js 1556→目标200(剩~1356·几乎全是真核心地基簇·见上条 cutover)· app.py 1727→500· 模块化缺 CSS。
- **批9f cutover 落地要点(下窗口做)**:① 建 core.js 放 main.js **最前** import;② t/escapeHtml/svgIcon/api簇/applyLang/routeTo/loadAll +引导期 render 助手整簇 verbatim 进 core.js;③ home.js 1786-1801 bootstrap(applyLang/routeTo/loadAll 同步调)搬进 core.js 尾部(import 自执行·此时 DOM 已 parse·t/api 同模块已定义);④ 全局状态 let 留 home.js;⑤ 每挪一步真浏览器全功能回归(登录→OCR→历史→设置→自动化全点一遍)·任一红立即 revert。app.py 拆登录/OCR/计费仍属 🔴高敏需 Zihao 在场。
- **最后 commit**:658c5b0(批9e)· `git log --oneline -5` 查最新。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
