# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡（2026-06-06 · **✅ 知识库整条闭环(Codex 第2轮全 PASS)+ LINE 官方号换 @pearnly + 对话体系全做齐 · HEAD `789bc1a`**）

- **知识库 = 闭环**:Codex 第2轮报告 `桌面\knowledge_fix_verify_2026-06-05\知识库修复验证报告_第2轮_2026-06-05.md` **全 PASS**(P1a 坏PDF=`processing_failed`+人话文案+不扣费 / 原文黄底高亮可用+可核对 / 0 console error / 计费正常)。2 个观察项(种子文档太短只 1 chunk 无灰色邻段 / 答案只 1 出处卡无法测切换)= **非 bug**,下轮用长文档演示即可。deferred 的 `ocr_ingest.py` 双 suffix 判已收口(等价·88 知识库测试绿)。
- **LINE 官方号换号上线**(高敏·铁律#26·Zihao 全程在场)：旧 `@059oupmg`→新 **`@pearnly`**(Channel `2010309291`)。prod `.env` 换 4 项(不碰 `LINE_LOGIN_*`)+ 全站 `@pearnly` + 机器人**对话体系全做齐**:首加好友欢迎=**OA Greeting 卡**(机器人不回·去重复)/ 转人工=机器人 `_is_agent_request`(含 `คุยกับคน`·不靠 LINE 原生)/ 无关文字=4 语菜单(带拍照贴士)/ 图片=OCR(真账号实测闭环·扣 ฿0.18)/ 默认语言 zh→th / 定位「财务自动化助手」+ 路径「集成→LINE Bot」。/simplify 收口(删死键 image_soon/抽 DEFAULT_LANG/去冗余 lower)。详见 [[line-account-migration-pearnly]]。
- **沙盒迁主仓库**:`pearnly-sales-module` 计划 → `docs/sales-module/`(含新写 `docs/14-line-quick-entry-spec.md`·对标 Paypers LINE 一句话记账逐功能拆+超越点)。
- **未提交残留**:无(全 push·HEAD `789bc1a`·守门全绿·全量 **2293 OK**)。**deferred/未闭环**:① 知识库页码/章节标(需入库管线存 page→chunk)② 问答偶发 Gemini 503(瞬时·不扣)③ LINE 一句话记账功能**未建**(仅铺垫文案+spec·属销项/凭证中心项目)。
- **等 Zihao(LINE 收尾)**:OA 后台关掉最后那条「转人工」规则(机器人已平替·留着营业时段外会双回)→ 真机复测(转人工/无关字/重新加好友看单条欢迎)→ 满意后删旧号 `@059oupmg`。
- **下一步(下个窗口·Zihao 拍板序列)**：知识库闭环 ✅ → **转 `docs/sales-module/`(销项/智能录入·含 LINE 一句话记账)** → 闭环后转**凭证中心**。先读 `docs/sales-module/STATE.md` + `docs/10-mainproject-constraints.md`。全貌 [[sales-module-sandbox-project]] / [[line-account-migration-pearnly]]。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
