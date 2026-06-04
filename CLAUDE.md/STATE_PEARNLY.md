# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡（2026-06-04 · **✅ REFACTOR-C5 前端 TypeScript 迁移收官 · 151/151**）

- **REFACTOR-C5 全部完成**:`src/home/` 151 个文件全迁 TypeScript(0 个 .js)· 顶格严格 strict · typecheck 0 · 用户界面零变化 · 全部 push + 部署 200。一窗口扫完最后 92 个(批 8-12)。
  - **提交**:批1-7 `620692c..45d90a7`;批8-12 `7266832`/`cdbc84d`/`eff29a5`/`8894055`/`ced3654`(每文件带 `RATCHET-EXEMPT`)。
  - **行为零变化**:全程类型层(注解/as/!/泛型/type 别名/@ts-expect-error · 编译期擦除)· emit JS 行为不变。批 11 因累积擦除令 esbuild 重排 main.js minified 局部名(已逐行核验=纯改名零行为差) · 连 dist 一起提交;其余批 main.js 字节不变。
  - **工具链**:`tsconfig`(strict+bundler+allowJs/checkJs:false+noEmit)· `npm run typecheck` · 共享类型集中 `src/types/globals.d.ts`(ambient 全局 + Window 桥一大批 + AppUser/SelectedFile/OcrResult/HistoryState 等)。守门:check_file_size/ratchet 纳 `src/home/**/*.ts` + pre-push typecheck 闸。
  - **打法 + 六大坑全文**:见记忆 [[c5-typescript-migration-playbook]](收官打法/脚本全局碰撞/逆变/跨文件签名/esbuild改名重排+size硬闸/静态契约测试)。
  - **⚠️ 第六坑(CI 红补救)**:C5 把 src/home/*.js→.ts 后,5 个静态契约测试(`test_brv2_anchor_audit_static`/`test_brv2_export_lang_follows`/`test_test_center_extraction_static`)按写死 `.js` 路径读源码 → CI unit 步自批 11 起红。pre-push 不跑 Python 单测(没改 .py)故本地没暴露。已修(glob 纳 `.ts` + 计数放宽)· commit `180fc43` · **CI 现 success 全绿**。教训:大改 src/home 后必本地 `python -m unittest discover tests/unit` 再收官。
- **✅ 删 easyocr 死栈(2026-06-04 · commit `72ff38f` · REFACTOR-A3)**:requirements.txt 唯一直接声明的 easyocr 全仓库零 import(OCR 走 Gemini)· 经它传递拽进整棵 torch/torchvision/opencv/scipy/numpy ML 栈。手术删(via 反向依赖图算闭包 · lock 299→229 · 不重跑 pip-compile)+ Dockerfile 去 libglib2.0-0/libgomp1 → 镜像 5-7GB→数百 MB。干净 venv 实装验证 + CI 绿。**注:prod 现有 venv 的 torch 要等重建才真卸**(git-deploy 不全量重装)。详见 [[dead-ml-stack-removal-easyocr]]。
- **未提交残留**:无(全 push + 9 道闸绿 + CI success + prod 200)。
- **遗留(留专窗口 · 非阻塞)**:① globals.d.ts 遗留桥的 `(...args:any[])=>any`/动态 JSON 显式 `:any`(未迁 home.js 边界的合理松类型)· ② 14 处 `@ts-expect-error TS6133`(真死只写占位 · 删会改 emit)· ③ i18n 子树补译块跨 6+ 文件重复 → 抽 `applyI18nPlaceholders` 共享 helper(超 verbatim · 留 C-dedup)· ④ CI ci.yml 未加 typecheck step(缺 workflow OAuth scope · 靠 pre-push 兜底)。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
