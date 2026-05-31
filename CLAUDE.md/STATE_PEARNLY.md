# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-05-31 批4 收尾重写)

- **模式**:整顿封锁期 · 0 新功能 · 当前主线 = **home.js 拆迁 9 批**(批1-4✅,批5-9 待续)。
- **⚠️下一批5【最高风险】**:文件上传/OCR 主流程(dropZone/renderFileList/updateStartButton/mergeFields/handleDirectPdfFiles 等)→ src/home/upload.js。属铁律#26 OCR 热路径敏感·0逻辑改+真账号 E2E 严验·若 >500 同批4 拆 2 模块。
- **批1-4 闭环**(57def27/f7244e7/262f86b/ce5e389 已上线·prod 逐一验过):批1 结果表+抽屉→`ocr-results.js`(474);批2 推ERP→`ocr-push.js`(191);批3 导出→`export.js`(262);批4 发票记录页拆2→`history-list.js`(282)+`history-drawer.js`(413)· home.js **5344→3955**(净减1389)· 每批 6 道守门全绿 + 真浏览器验过(批4 用真数据账号验列表20行+点行开抽屉跨模块)。
- **拆迁范式(批2-9 照用)**:home.js 是经典脚本(非IIFE)→ 顶层 `let`(_results/_drawerIdx 等)模块裸读写自动桥;移出的函数若 home.js 仍调,需 `window.X=X` 挂出;`/* global */` 写全局,要**写**的标 `:writable`(否则 no-global-assign 红);移文件用 node split/join 保 home.js CRLF。
- **批1 踩坑**:① 引导期(applyLang/顶层 addEventListener)裸调移出函数会 ReferenceError(defer模块未就绪)→ 加 `window.fn &&` 守卫 或包箭头 `()=>fn()` 延迟解析 ② verbatim 代码进新模块要过 eslint/prettier(home.js 本豁免)。
- **真浏览器验法(本窗建立·可复用)**:本地 node 反代(`_verify_proxy.cjs` 思路:拦 /static/home.js+dist/main.js 返本地·其余透传 prod·改写 Origin→prod)+ tests/e2e spec(e2e账号登录真后端·注入 _results 跑函数·getComputedStyle 验可见)· 用完即删不 commit。
- **测试账号**:e2e_1/2/3 余额满999999·密码在 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`(**格式:密码后接3空格+说明·只取首段非空白串**·env注入不打印)。真数据账号(Zihao 给·有账套/异常)= 邮箱 `18685123459@163.com` / `xiaopi19950730..`(**是邮箱不是纯手机号**)。
- **剩余瓶颈**:home.js 3955→目标200(批5-9)· app.py 1727→500(ocr_recognize/LINE 高敏)· 模块化缺 CSS。
- **待 Zihao 拍板**:窗口数(3→1专攻?)。home.js 目标不变(Zihao 已答)。
- **最后 commit**:ce5e389(批4)· `git log --oneline -5` 查最新。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
