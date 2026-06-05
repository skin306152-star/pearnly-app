# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡（2026-06-05 · **✅ 知识库 /simplify 收口 + Codex 报告 4 修复 + 图标线性化 · 集中上线 `11850607`**）

- **本批集中一次 push**(master `517fba9` · 版本 `11850607` · prod 活)：上窗口留的 /simplify 5 条 + Codex prod 实测报告 4 个问题 + 图标线性化一起上。守门全绿(format/i18n/imports/ruff/ai_smell/vite build)· 全量单测 **2290 OK**(+6)。home.html `?v=` 11850606→11850607(字节级改保 CRLF)。
- **/simplify 5 条**(`368c411`)：① 6 份 i18n helper→`kbT` ② 5 份 esc→`kbEsc` ③ `charge_ocr`/`deduct_thb` 余额 SQL→私有 `_debit_balance` ④ satang 硬编码→`SATANG_PER_THB`/`thb_to_satang`/`satang_to_thb` ⑤ sources/info 两套 modal mask→`kbModalShell` 工厂。(原"citation 没转义"核查后**不存在**·escapeHtml 已转单引号·citeChip 已包)
- **报告 4 修复**(`517fba9`)：**P0** 查不到资料仍扣费 → `ask.py` 哨兵 `NO_ANSWER` 或答案无 `[n]` 出处即 `no_answer=true` 不扣(+2 测)；**P1a** 坏文件 500 → `ocr_ingest` 包文本路径异常 + 路由兜底落 `failed` + 新码 `processing_failed`(4 语·+4 测)；**P1b** 402 → 显「余额不足,请先充值」(4 语)；**P2a** 上传行不即时 → 统一 `renderList` 乐观行。
- **图标线性化**：知识库 emoji 图标(📄📑💬✅✓✕🎯ℹ️🔒 等)→ `kbIcon` lucide 线性 SVG;🎯/ℹ️/🔒 删冗余。**悬浮猫(fab)整体保留**(爆花/猫爪/动画·Zihao 指定)。**图标 Zihao 自验·不进 Codex 清单**。
- **未提交残留**:无(全 push·分支已删)。**未闭环**:原文片段高亮(后端「按 chunk_id 取文」接口)留后续;问答偶发 Gemini 503(瞬时·已降级不扣)。
- **在等 Codex**:用桌面 `knowledge_fix_verify_2026-06-05\`(`验证清单_2026-06-05.md` + `files/kb_bad_broken.pdf` 坏PDF + `files/kb_seed_policy.txt` 种子文档)做 **prod UI 实测**(图标除外),重点验三条"不该扣费"(P0-1 off-topic / P1a 坏文件 / P1b 低余额)→ 出 `知识库修复验证报告_2026-06-05.md`。
- **下一步(下个窗口)**:**等 Codex 报告再决定**(Zihao 拍板)——有问题修、没问题收;顺带可做原文片段高亮接口。⚠️ P0/P1a 碰计费/OCR 热路径·已上线但建议真账号 prod 复验(方向更保守·不会多扣)。全貌见 [[kb-rag-sandbox-project]] / [[knowledge-frontend-ocr-billing-shipped]]。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
