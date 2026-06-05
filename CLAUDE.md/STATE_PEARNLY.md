# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡（2026-06-05 · **✅ 知识库「死规则+客户规矩」整条上线 + 后续修复 · version-banner 删除**）

- **知识库死规则引擎上线接管发票异常检测**(`feat/knowledge-backend` 已并 master · master `c5d1fc7` · 版本 `11850104` · prod 200 · `KNOWLEDGE_ENABLED=1`):
  - 引擎 finding(算术 R-VAT/SUM/LINE/MULTIPAGE、税号 R-TAXID、查重 R-DUP、日期 R-DATE、客户规矩 R-SUP/R-LIMIT/R-CAT)写进**现有异常存储**,异常列表/筛选 chip(收 5 组)/详情抽屉/已学规则全认 **16 个新规则码**(`detail.message_key`→`risk.*` · 4 语复用沙盒字典 · 真浏览器验)。旧码历史行兼容并存。
  - **8 张 Supabase 表 + pgvector 已建**(prod 无 alembic_version → 服务器 venv python 直接跑 5 迁移的 `IF NOT EXISTS` DDL · pgvector 直接可装)。
  - **客户规矩设置弹窗**(异常页右上「规矩设置」· flag 探针门控):类型卡片高亮跟随、停用变灰可恢复(GET `include_inactive`·引擎加载仍 active-only)、删除=确认+删整条、开关**乐观更新**丝滑+toast。
  - **ERP 推送异常块搬到集成页**新增「推送异常」tab(纯位置·`erp-exceptions.ts` 逻辑零改)+ 修溢出/原始报错串。
- **version-banner 更新通知功能彻底删除**(commit `c5d1fc7`):删 js + post.js 清单 + `/api/version` 去 release_notes(留 version+ts)+ 死 i18n 键。⚠️ **铁律 #6(每次部署写 release_notes)作废 · 下个窗口别再写**。见 [[version-banner-removed]]。
- **并行窗口已上线(非本线)**:全站按钮统一品牌蓝 + UI 一致性硬闸 `lint-ui` FAIL(`check_ui_consistency` D1 禁新抽屉/D2 按钮黑底基线 0)· 测试拔 pytest 依赖(unittest only)。见 [[ui-modal-blue-button-gate]]/[[no-pytest-tests-unittest-only]]。
- **未提交残留**:无(全 push · 9 道闸绿 · prod 200)。
- **闭环判断**:**「死规则 + 客户规矩 + 异常 UI」= 闭环上线可用**;**「RAG 带出处问答 + 文档库」= 未做**(后端 P1/P2/P4 路由已 mounted 但零 UI)。
- **下一步(下个窗口)**:继续本线 = 按 [[ui-design-before-build-rule]] **先出「文档库 + 悬浮问答 FAB + 知识中心页」设计稿**再实现(沙盒 `docs/...UI设计...` 有草图);或转整顿 Wave3(闲置笔记本 staging [[spare-laptop-staging-then-prod]] / `lint-ui` B 类视觉清理)。全貌见 [[kb-rag-sandbox-project]]。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
