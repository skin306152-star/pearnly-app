# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-05-31 批7 收尾重写)

- **模式**:整顿封锁期 · 0 新功能 · 当前主线 = **home.js 拆迁 9 批**(批1-7✅,批8-9 待续·下一批8=权限/quota/sidebar isSuperAdmin/isOwner/isEmployee系+renderQuotaBanner/applySidebarVisibility/renderInfoBar→src/home/permissions.js+layout.js·权限函数被多模块+home.js裸调·桥要全)。
- **批1-7 全闭环**(…/1ea8a50/cf0b0f5 已上线·prod 逐一验过):批1 `ocr-results.js`;批2 `ocr-push.js`;批3 `export.js`;批4 `history-list.js`+`history-drawer.js`;批5 上传/OCR主流程拆4;批6 toast/提示/错误人话化 `toast.js`(showAlert/hideAlerts/_humanizeBackendError/humanizeError/showToast);批7 设置/资料 `settings-core.js`(switchSettingsTab/fillSettingsForms/saveProfile/saveCompany/renderSettings+_renderCreditsSettings)。**home.js 5344→2535(净减2809·降53%·进度93%)**· 每批 6 道守门全绿 + 真账号真后端 E2E 验过。
- **批7 关键认知**:settings 函数交错夹在非本批代码间(高敏 showForceChangePasswordModal 密码块+2 个 IIFE 绑定 initSettingsTabs/bindSettingsForms 留 home.js·裸调经 window 桥);renderSettings 被 applyLang(615)/routeTo(795) 引导期可达 + fillSettingsForms 被用户初始化(1116)调 → 三处加 `typeof window.X==='function'` 守卫;**saveProfile/saveCompany 重新赋值 `_userInfo` → eslint.config.mjs 把 _userInfo readonly→writable**(home.js 顶层 let 跨 realm 词法绑定可写);renderSettings 内 `tt` 是历史死代码(被 if(apiKeyCard) 守住·BYO Key 下线后永不执行)verbatim 保真+列 /* global tt */。
- **大块拆法(批4/5 验证·批7-9 照用)**:单块 >500 拆 N 个 <500 子模块;共享态(_historyState/_selectedFiles/mergeFields)留 home.js 顶层当桥(两边 bare 读写·属性 mutation 不触发 no-global-assign·重新赋值标 :writable);子模块循环依赖经 window 桥 OK(调用都在 handler 内·延迟解析);bootstrap 期(applyLang/用户初始化)裸调移出函数加 `typeof window.fn==='function'` 守卫+模块按 currentRoute 自举。
- **拆迁范式(批2-9 照用)**:home.js 是经典脚本(非IIFE)→ 顶层 `let`(_results/_drawerIdx 等)模块裸读写自动桥;移出函数 home.js/别的模块仍调需 `window.X=X` 挂出;`/* global */` 写全局·要**写**的标 `:writable`;移文件用 node split/join 保 home.js CRLF(对边界行先断言防误删·两块不连续要分别删)。
- **真浏览器验法(本窗复用成功)**:本地 node 反代(`_uitest/proxy.cjs`:拦 /static/home.js+dist/main.js(.map)返本地·其余透传 prod·改写 Origin/Referer→prod·删 CSP·Location 改回 localhost)+ tests/e2e 临时 spec(内联轻量登录·**别用 auth.js 的 waitForURL until:load·经反代长连接会拖住 load 假超时**·改等 token+window.showToast 就绪)· 用完即删不 commit。
- **测试账号**:e2e_1/2/3 余额满999999·密码在 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`(**格式:密码后接3空格+说明·只取首段非空白串·grep 须锚 `^username:` 否则命中 $env 行取错·tr -d '\r'**·env注入不打印)。真数据账号= 邮箱 `18685123459@163.com` / `xiaopi19950730..`。
- **剩余瓶颈**:home.js 2535→目标200(批8-9)· app.py 1727→500(ocr_recognize/LINE 高敏)· 模块化缺 CSS。
- **批8-9 路线**:批8 权限/quota/sidebar→permissions.js+layout.js;批9【最高风险·地基】routeTo/loadAll/applyLang/apiGet系/全局态→core.js(极小步+每步真浏览器全功能回归·搬完只剩 IIFE 外壳→删 home.html script 标签)。
- **最后 commit**:cf0b0f5(批7)· `git log --oneline -5` 查最新。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
