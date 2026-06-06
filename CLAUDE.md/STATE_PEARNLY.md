# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡（2026-06-06 · **🚀 销项 Phase 1 后端 PO-1~6 + 买方模块 + 合规 §M 1-3 全上线 prod · HEAD `bcfa482`** · 前序:知识库闭环 + LINE 换 @pearnly）

- **知识库 = 闭环**:Codex 第2轮报告 `桌面\knowledge_fix_verify_2026-06-05\知识库修复验证报告_第2轮_2026-06-05.md` **全 PASS**(P1a 坏PDF=`processing_failed`+人话文案+不扣费 / 原文黄底高亮可用+可核对 / 0 console error / 计费正常)。2 个观察项(种子文档太短只 1 chunk 无灰色邻段 / 答案只 1 出处卡无法测切换)= **非 bug**,下轮用长文档演示即可。deferred 的 `ocr_ingest.py` 双 suffix 判已收口(等价·88 知识库测试绿)。
- **LINE 官方号换号上线**(高敏·铁律#26·Zihao 全程在场)：旧 `@059oupmg`→新 **`@pearnly`**(Channel `2010309291`)。prod `.env` 换 4 项(不碰 `LINE_LOGIN_*`)+ 全站 `@pearnly` + 机器人**对话体系全做齐**:首加好友欢迎=**OA Greeting 卡**(机器人不回·去重复)/ 转人工=**只走 OA 后台原生**(机器人 agent 处理已撤·`0e7cc7c`·Zihao 2026-06-06 拍板)/ 无关文字=4 语菜单(带拍照贴士)/ 图片=OCR(真账号实测闭环·扣 ฿0.18)/ 默认语言 zh→th / 定位「财务自动化助手」+ 路径「集成→LINE Bot」。/simplify 收口(删死键 image_soon/抽 DEFAULT_LANG/去冗余 lower)。详见 [[line-account-migration-pearnly]]。
- **🚀 销项模块 Phase 1 后端全上线**(2026-06-06·Zihao 破例开建·全程真账号 E2E):`services/sales/*` + `routes/{products,sales,sales_seller}_routes.py` + alembic `0006~0008`(**prod 库已 apply·alembic 追踪本次首次在 prod 立起**·之前全靠 ensure_*)。PO-1 schema / PO-2 商品 CRUD / PO-3 Excel 导入 / PO-4 开票核心(连号 FOR UPDATE·开出不可改 409·VAT+WHT·Decimal)/ PO-5 红冲补开(CN/DN 独立连号)/ PO-6 合规 PDF(reportlab 复用泰文字体·桌面 `sales_invoice_sample.pdf` 样票)。**卖方=账套主体**(Zihao 纠正:会计事务所代多公司):账套主体加开票字段(地址/总分公司/电话/VAT)+ 选择账套弹窗改「只选不建」(新增去客户管理·真浏览器验 0 console error·缓存 bump 11850610)。沙盒 `pearnly-knowledge` 设计→`docs/knowledge/`。全貌 [[sales-module-sandbox-project]]。
- **🆕 销项买方模块 + 合规后端(2026-06-06·两批上线 prod)**:① `a1169bf` 买方动态模块(`services/sales/buyer.py`·公司/个人/外国/匿名)+ §A 双方冻结快照 + §J 合并单/收款 + §D 折扣 + §E1/E2 纸张正副本 + §G 历法(迁移 0009~0011)② `bcfa482` **§M 1-3**:§C 价内/价外(`price_includes_vat`+抽出 `services/sales/totals.py`)· §E2 省纸两联(`copies_layout=two_up`)· §F 审批工作流(`services/sales/approval.py`·默认 none·owner 审批·迁移 0012/0013)。**prod 迁移已 apply(alembic 到 0013)· prod 真库 E2E 过**。全貌 [[sales-mhz-blocks-and-prod-ops]]。
- **未提交残留**:无(全 push·HEAD `bcfa482`·守门全绿·全量 **2431 OK**)。**deferred/未闭环**:① 知识库页码/章节标 ② 问答偶发 Gemini 503(瞬时·不扣)③ LINE 一句话记账**未建**(spec 铺垫)。
- **LINE 收尾(删旧号·Zihao 在 Console)**:① OA 关最后「转人工」规则 ② 真机复测 ③ 复测无误删旧 OA `@059oupmg`。代码侧无旧号现行残留。
- **下一步(下个窗口·先读 `docs/sales-module/STATE.md` 顶部 + `docs/16` §M)**:接**销项 §M 4-7 后端块**(4. E3 `pdf_sha256`+热敏窄版 5. L1 PromptPay/L2 WHT多档/L3 报价转换 6. L4 模板后端管道 7. `sales_settings`+并激活审批 `approval_mode`+clients/workspace_clients 补字段)→ 再 8. PO-7 邮件发送(LINE 高敏等 Zihao)→ 9. PO-10 前端(照桌面三份样稿)。**每块本地全量 unittest + prod 真库 E2E·迁移走 ssh+psql 经授权·见 [[sales-mhz-blocks-and-prod-ops]]。**

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
