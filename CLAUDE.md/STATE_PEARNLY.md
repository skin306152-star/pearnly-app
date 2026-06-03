# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-03 · **✅ 目录重组(铁律#30)+ view-source 成品化(E7)双双收官 · 整顿核心+抛光全完成**)

- **本窗口②:view-source 成品化(整顿 E7·对标 Claude.ai)** `0209649..ed31f24`(8 commit):所有明文 CSS/JS 打包成 minified bundle + HTML 压成一行。prod 实测 home view-source **228 行→1 行**、login/着陆页同样一行、CSS 39→1 + JS 9→6 script + 0 注释 + 0 明文业务代码。范式与坑见 [[frontend-asset-bundling-playbook]]。**血泪:① BOM 坑——`landing-auth.css` 开头 BOM 合并进 bundle 中间破坏紧跟的 `.auth-card{absolute}`→ 着陆页登录框错位·修=打包脚本 strip BOM(`build-lib.mjs` 集中) ② /simplify 收口抽 `build-lib` 共享 I/O·dist 字节零改**。注:body 骨架+6 中文是传统架构必然(压一行还在·非消失)·真 body 空=SPA 重写(整顿禁·未做)。
- **本窗口①:代码目录重组(铁律#30·整顿最后一步)收官上线** `d05cf6d`:122 个 root .py → 顶层 `routes/`(58)+`core/`(4)+复用现有 `services/<域>/`(60)·方案B(非 `app/` 外壳·app.py 留根·入口不变)·854 处机械改写 verbatim·全量 2176 单测全绿·prod 零 500。范式与五大坑(CRLF翻转/sys.modules/f-string patch/静态路径/ratchet rename)见 [[directory-reorg-playbook]]。
- **下一步**:✅ 整顿核心(所有源文件 <500 + 包结构)+ E7 抛光全收官 → 候选:闲置笔记本 staging(Wave3·[[spare-laptop-staging-then-prod]])/ 品牌资产全站接线 / 回整顿剩余阶段(B3-B10 后端工程化 / C4-C8 前端进阶 / D 测试 / E 性能 / F 数据 / H 安全合规 · 见 `REFACTOR_MASTER_PLAN.md` 看板·上轮已给 Zihao 全貌)。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
