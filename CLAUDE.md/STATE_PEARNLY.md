# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-05-31 批8 收尾重写)

- **模式**:整顿封锁期 · 0 新功能 · 当前主线 = **home.js 拆迁 9 批**(批1-8✅,批9 待续·下一批9【最高风险·地基】=routeTo/loadAll/applyLang/apiGet系/全局态→src/home/core.js·极小步+每步真浏览器全功能回归·搬完只剩 IIFE 外壳→删 home.html 的 `<script src=/static/home.js>`)。
- **批1-8 全闭环**(…/cf0b0f5/c9effd3 已上线·prod 逐一验过):批1-5 见 archive;批6 toast `toast.js`;批7 设置/资料 `settings-core.js`;批8 权限/quota/sidebar 拆 2 模块 `permissions.js`(isSuperAdmin/isOwner/isEmployee/isTrial/isLifetime/shouldHideMoney/canManageTeam/canManageApiKey+isMoneyHidden 别名)+`layout.js`(renderQuotaBanner/applySidebarVisibility/renderInfoBar)。**home.js 5344→2248(净减3096·降58%·进度93%)**· 每批 6 道守门全绿 + 真账号真后端 E2E 验过。
- **批8 关键认知**:权限函数是地基但 home.js 自身搬后**不再裸调**它们(原"调用点"全在被搬的 applySidebarVisibility/renderInfoBar 内部 + 1 处局部 isEmployee 同名遮蔽·非全局函数);layout.js 依赖 permissions.js 角色函数·都在函数内经全局解析·import 顺序无关;3 个 render 被用户初始化(loadAll post-await)/applyLang 裸调 → 4 处加 typeof window.X 守卫;**eslint.config.mjs 给 src/** 加 `no-useless-assignment:warn`**(layout.js verbatim 防御式初始化 `let used=0,total=0`·跟 static 块同口径·否则红)。
- **大块拆法(批4/5 验证·批7-9 照用)**:单块 >500 拆 N 个 <500 子模块;共享态(_historyState/_selectedFiles/mergeFields)留 home.js 顶层当桥(两边 bare 读写·属性 mutation 不触发 no-global-assign·重新赋值标 :writable);子模块循环依赖经 window 桥 OK(调用都在 handler 内·延迟解析);bootstrap 期(applyLang/用户初始化)裸调移出函数加 `typeof window.fn==='function'` 守卫+模块按 currentRoute 自举。
- **拆迁范式(批2-9 照用)**:home.js 是经典脚本(非IIFE)→ 顶层 `let`(_results/_drawerIdx 等)模块裸读写自动桥;移出函数 home.js/别的模块仍调需 `window.X=X` 挂出;`/* global */` 写全局·要**写**的标 `:writable`;移文件用 node split/join 保 home.js CRLF(对边界行先断言防误删·两块不连续要分别删)。
- **真浏览器验法(本窗复用成功)**:本地 node 反代(`_uitest/proxy.cjs`:拦 /static/home.js+dist/main.js(.map)返本地·其余透传 prod·改写 Origin/Referer→prod·删 CSP·Location 改回 localhost)+ tests/e2e 临时 spec(内联轻量登录·**别用 auth.js 的 waitForURL until:load·经反代长连接会拖住 load 假超时**·改等 token+window.showToast 就绪)· 用完即删不 commit。
- **测试账号**:e2e_1/2/3 余额满999999·密码在 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`(**格式:密码后接3空格+说明·只取首段非空白串·grep 须锚 `^username:` 否则命中 $env 行取错·tr -d '\r'**·env注入不打印)。真数据账号= 邮箱 `18685123459@163.com` / `xiaopi19950730..`。
- **剩余瓶颈**:home.js 2248→目标200(只剩批9 地基·但 2248→200 还差 2048·批9 后大概率仍 >200 需再分批拆 routeTo/loadAll/apiGet/i18n 引导等)· app.py 1727→500(ocr_recognize/LINE 高敏)· 模块化缺 CSS。
- **批9 路线**:【最高风险·地基】routeTo/loadAll/applyLang/apiGet系/全局态(currentLang/currentRoute/_userInfo/_results 等)→ core.js。⚠️ t/escapeHtml/apiGet/apiPost/showToast/currentLang/currentRoute 被~70模块裸调·搬走后全靠 window 桥+全局解析·任何模块 eval 期(非handler)裸调会崩·极小步+每步真浏览器全功能回归。
- **最后 commit**:c9effd3(批8)· `git log --oneline -5` 查最新。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
