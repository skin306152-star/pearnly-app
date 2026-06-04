# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡（2026-06-04 · **C5 前端 TypeScript 迁移启动 + 推进 · 59/151**）

- **本窗口:REFACTOR-C5 前端 `src/home/*.js`(151 个)增量迁 TypeScript**(用户界面零变化 · 整顿期 0 新功能 · 不发版本通知)。Zihao 拍板**顶格严格 strict**(选项 A · 拒绝 loose-then-tighten)→ 多窗口长活。
  - **工具链落地**:`tsconfig.json`(strict + bundler 解析 + allowJs:true/checkJs:false + noEmit)· `npm run typecheck=tsc --noEmit` · 环境全局/共享类型集中 `src/types/globals.d.ts`(ambient 全局 + Window 桥 + AppUser/SelectedFile/OcrResult/_contact 等)。**守门接线**:check_file_size 加 `src/home/**/*.ts`、pre-push FE_CHANGED 纳 ts + 新增 typecheck 闸、prettier glob 纳 ts。
  - **关键省力**:Vite 自动把 `import './x.js'` 解析到 `x.ts` → 迁移只 `git mv` 不动 importer 路径。
  - **进度 59/151**:8 提交 `620692c..7217627`(批1-7 + /simplify 收口)· 每 .ts 带 `RATCHET-EXEMPT`(类型标注合理增长)· typecheck 全程 0 · 行为 verbatim · main.js 类型层不变(行为等价微调批才动 dist)· 每批 push 后验 prod 200。
  - **打法全文**:见记忆 [[c5-typescript-migration-playbook]](三大类错误修法 + 共享类型清单 + 守门接线)。
- **未提交残留**:无(8 提交全 push + CI 绿)。
- **剩余**:**92 个 .js**(110-490 行逻辑档 · 每文件类型错更多)。**下一步**:下个窗口照 playbook 继续迁(由小到大成批)。
- **延后**:i18n 子树补译块跨 5+ 文件重复 → 抽 `applyI18nPlaceholders` 共享 helper(/simplify 审出 · 属改底层逻辑超 verbatim 范围 · 留 C-dedup 专项)。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
