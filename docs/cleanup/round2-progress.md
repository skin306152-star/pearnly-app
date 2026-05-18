# Pearnly 屎山清理 Round 2 · 进度记录

> **会话日期**:2026-05-18
> **起始 HEAD**:`c46b20b`(OCR phase 3.3 收尾后)
> **工作模式**:用户授权激进清理 · 自主判断 · 不中途汇报
> **禁区**:services/ocr/ · OCR 接入点(app.py 主路由/LINE bot OCR、email_ingest、recon_routes)· db.py OCR cost 函数 · /api/health · services/ocr/pdf_utils.py

---

## 当前会话累计 commit(按时间顺序)

| # | Commit | 类型 | 说明 |
|---|---|---|---|
| 1 | `(pending)` | 📄 docs | round2-progress.md 初版 |
| 2 | `(pending)` | 🟢 infra | .gitignore 补 4 个 tests/*.json benchmark pattern(防真发票数据进 git)|
| 3 | `(pending)` | 🟢 infra | 新增 scripts/check_imports.py(从临时位置永久化到项目内)|
| 4 | `(pending)` | 🔄 | line_client.py + report_routes.py 2 处 empty except 按 §3.2 处理 |
| 5 | `(pending)` | 🟢 | 删 quality_check.py 整模块(OCR 迁移完成后零引用)|

---

## 关键决策

### A. email_ingest.py 3 处 empty except 跳过

**理由**:用户的禁区清单显式列出 `email_ingest`。该文件几乎整体围绕 OCR pipeline(IMAP 拉附件 → OCR 识别),为避免与今天 OCR 会话刚结束的 cleanup 冲突,本 round 不动整个文件。

**影响**:
- email_ingest.py:328-329(OCR 字段置信度判断 - 真 OCR 相关)
- email_ingest.py:596-597(IMAP conn.logout)
- email_ingest.py:627-628(IMAP folder_count int 解析)
- 后两处其实是非 OCR 的 IMAP 容错,但稳妥起见整文件不碰

### B. line_client.py:306 归 A 类(保留 pass + 注释)

**理由**:已在 `except urllib.error.HTTPError` 错误路径内,body 读不到就保持空串,下行 `logger.error` 仍会记 HTTP code。再加 logger.warning 会刷重复日志。

### C. report_routes.py:265 归 B 类(改 logger.warning)

**理由**:client 信息扩充失败如果静默,用户可能拿到默认 client_name 不会知道。加 logger.warning 让运维能发现 client 表查询问题。

### D. quality_check.py 整模块删

**复查**:`grep -E "from quality_check|import quality_check"` → 0 命中。`grep "assess_page_quality|assess_pages_quality"` → 只剩模块内部 + 旧 audit doc 引用。

**为什么 Round 1 没删**:Round 1 时 OCR 迁移未完成,标 🟡-0 "等 OCR 新 validators.py 上线"。今天 OCR 会话 Phase 3 完成,新 pipeline 已有自己的字段校验逻辑(services/ocr/),quality_check.py 彻底无主 → 可删。

### E. bank_reconcile.py 整迁移 → 不动

**复查**:grep `/api/bank-recon/` in `home.js` → **15+ 处真调用**,跨多个前端功能模块(对账中心 stats / 上传 / sessions 列表 / tx 候选 / override / dev seed 等)。

**结论**:`/api/bank-recon/*` 路由族 + `bank_reconcile.py` 是**前端在用的活体系**,不是死代码。Round 1 调研文档 `bank-reconcile-migration.md` 早已警告"这是一整套老体系不是孤立文件"。本 round 完全不碰,挂到 Round 3 决策清单。

---

## 工具基线复查

**`scripts/check_imports.py` 运行结果**(commit 前基线):
- 项目根目录 35 个 .py 文件
- 27 个 import 全 OK
- 8 个 FAIL(全是已知第三方包:fastapi / bcrypt / passlib / psycopg2 / uvicorn / jwt / xlrd · 服务器有装,本机无)
- **0 个本地模块缺失**(Round 1 抢救的 7 个幽灵模块全部就位)

---

## 进行中

继续处理:
- 6: app.py compat C 第 2 步扫描(找纯墓碑可秒删的)
- 7: 决策清单 / Round 3 建议归档
- 8: 最终 push + 写 round2-final-report.md
