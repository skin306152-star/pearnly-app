# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-05-31 批5 收尾重写)

- **模式**:整顿封锁期 · 0 新功能 · 当前主线 = **home.js 拆迁 9 批**(批1-5✅,批6-9 待续·下一批6=toast/错误/alert→src/home/toast.js)。
- **批1-5 全闭环**(57def27/f7244e7/262f86b/ce5e389/73cc016 已上线·prod 逐一验过):批1 结果表+抽屉`ocr-results.js`(474);批2 推ERP`ocr-push.js`(191);批3 导出`export.js`(262);批4 发票记录页拆2 `history-list.js`(282)+`history-drawer.js`(413);批5 上传/OCR主流程拆4 `upload-camera.js`(481)+`upload-files.js`(230)+`ocr-recognize.js`(444)+`ocr-duplicate-dialog.js`(141)。**home.js 5344→2840(净减2504·降47%·进度92%)**· 每批 6 道守门全绿 + 真账号真后端 E2E 验过。
- **大块拆法(批4/5 验证·批6-9 照用)**:单块 >500 就拆 N 个 <500 子模块;共享态(_historyState/_selectedFiles/mergeFields)留 home.js 顶层当桥(两边 bare 读写·属性 mutation 不触发 no-global-assign·重新赋值的标 :writable);子模块间循环依赖经 window 桥 OK(调用都在事件/异步 handler 内·延迟解析·加载顺序无关);bootstrap 期(applyLang/用户初始化)裸调移出函数加 `typeof window.fn==='function'` 守卫+模块按 currentRoute 自举。
- **拆迁范式(批2-9 照用)**:home.js 是经典脚本(非IIFE)→ 顶层 `let`(_results/_drawerIdx 等)模块裸读写自动桥;移出的函数若 home.js 仍调,需 `window.X=X` 挂出;`/* global */` 写全局,要**写**的标 `:writable`(否则 no-global-assign 红);移文件用 node split/join 保 home.js CRLF。
- **批1 踩坑**:① 引导期(applyLang/顶层 addEventListener)裸调移出函数会 ReferenceError(defer模块未就绪)→ 加 `window.fn &&` 守卫 或包箭头 `()=>fn()` 延迟解析 ② verbatim 代码进新模块要过 eslint/prettier(home.js 本豁免)。
- **真浏览器验法(本窗建立·可复用)**:本地 node 反代(`_verify_proxy.cjs` 思路:拦 /static/home.js+dist/main.js 返本地·其余透传 prod·改写 Origin→prod)+ tests/e2e spec(e2e账号登录真后端·注入 _results 跑函数·getComputedStyle 验可见)· 用完即删不 commit。
- **测试账号**:e2e_1/2/3 余额满999999·密码在 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`(**格式:密码后接3空格+说明·只取首段非空白串**·env注入不打印)。真数据账号(Zihao 给·有账套/异常)= 邮箱 `18685123459@163.com` / `xiaopi19950730..`(**是邮箱不是纯手机号**)。
- **剩余瓶颈**:home.js 2840→目标200(批6-9)· app.py 1727→500(ocr_recognize/LINE 高敏)· 模块化缺 CSS。
- **待 Zihao 拍板**:窗口数(3→1专攻?)。home.js 目标不变(Zihao 已答)。
- **最后 commit**:73cc016(批5)· `git log --oneline -5` 查最新。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
