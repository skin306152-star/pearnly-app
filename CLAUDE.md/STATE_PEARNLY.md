# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-03 · **✅ 目录重组(铁律#30)+ view-source 成品化(E7)双双收官上线**)

- **本窗口②:view-source 成品化(整顿 E7·对标 Claude.ai)** `commit 0209649`(CSS)`29f06d5`(JS):home/admin 的 **39 个明文 CSS link → 1 个 minified bundle** + **5 个明文业务 JS → 2 个 bundle**(pre/post·9→6 script)+ 清 73 行 HTML 注释 · prod view-source 只见外壳(1 css link·0 明文逻辑·0 注释)。**打包范式([[frontend-asset-bundling-playbook]])**:CSS 必独立 `<link>`(阻塞首屏防闪·不塞 JS)·清单固化别从会被简化的 html 读·按原 DOM 顺序保 !important 收口 · JS 按 main.js 前后分组保时序(erp-log 依赖 erp-connect 全局)·i18n-data 715KB 数据保留独立 · `scripts/build-home-{css,js}.mjs` 进 npm build hook(prod 用提交的 dist) · 本地真浏览器验渲染像素一致 + 全局挂载 + 零错误。
- **本窗口①:代码目录重组(铁律#30 · 全项目最大 blast radius)完整收官上线** `commit d05cf6d`(`a10e2cb..d05cf6d`)· prod `/api/version` 11850080→**11850081** · **零 500/502**:登录(`/api/login` 422)/OCR(`/api/ocr/quota` 401)/计费/推送/对账(`/api/bank-recon/sessions` 401)主路径全验路由活+认证正常。
- **方案B(Zihao 拍板 · 非 `app/` 外壳)**:122 个 root 平铺 .py → 顶层 `routes/`(58)+`core/`(4·db/auth/route_helpers/kms_helper)+ 复用**已存在**的 `services/<域>/`(60·新建 vat/report/excel)· app.py 留根(`uvicorn app:app` 入口不变)· 现有 212 文件 services/ 的 import 纹丝不动(blast radius 减半)。
- **854 处机械改写 verbatim**:`import M`→`from PKG import M`(保 `M.attr`)· `from M`→`from PKG.M`· patch 字符串路径(**收窄到 `patch(`/`setattr(`/`import_module(` 调用内**·杜绝误伤 i18n key `"auth.x"`/文件名 `"db.py"`)· `sys.modules["M"]` key · 前缀重叠按模块名长度降序。
- **五大踩坑([[directory-reorg-playbook]])**:① **transform `read_text()`+`write_text(newline="")` 把 10 个原 CRLF 文件翻 LF** → 整文件 diff 噪声 + check_new_debt 误报 → 修法 `git -c core.autocrlf=false add --renormalize` ② sys.modules 注入的 `.get/.pop` key 漏改 → fake 模块毒化全局 ③ f-string `patch(f"recon_routes.{k}")` 字面规则抓不到 ④ 静态审计 `open(ROOT/"x_routes.py")` 硬编码路径 ⑤ ratchet 不解析 rename path(已修)。
- **守门同步**:check_file_size+check_line_ratchet 加 `routes/** core/**` glob · ratchet 修 rename 路径解析 + 5 个 RATCHET-EXEMPT(import 加前缀致 black 拆行净增·纯结构) · refactor_progress `db.py`→`core/db.py` · 铁律#30 文字更新为「已执行」。
- **验证**:全量 2176 单测全绿 · ruff 全规则零错 · import app 275 路由全注册 · 守门全绿 · prod 零 500。mrerp live integration(连真实 MR.ERP·缺凭证 skip)与重组无关(HEAD worktree baseline 同样失败·已铁证)。
- **下一步**:✅ 整顿核心收官(所有源文件 <500 + 包结构达成)→ 闲置笔记本 staging(Wave3·[[spare-laptop-staging-then-prod]])· 或品牌资产全站接线(home/admin/terms/privacy 仍引 favicon.svg)。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
