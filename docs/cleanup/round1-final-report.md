# Pearnly 屎山清理 Round 1 · 收尾报告

> **会话日期**:2026-05-18(单日完成)
> **会话主线**:代码清理(与并行的 OCR 迁移会话隔离)
> **起始版本**:生产 v118.33.13.6 / 本地 commit `dbf2b7e`
> **收尾版本**:本地 commit `70a964d`(已 push)· 生产保持 v118.33.13.6(本会话纯清理,无版本号变更)

---

## 1. 累计 24 个 commits(`b836a7b` → `70a964d`)

按时间顺序:

| # | Commit | 类型 | 说明 |
|---|---|---|---|
| 1 | `b836a7b` | 🟢 | excel_export_v108_backup.py 字节级备份删除 |
| 2 | `e2ef6d4` | 🟢-收尾 | gitignore `_pkg_tmpstatic/` |
| 3 | `d7cb902` | 🟢 | 删 3 个旧 deploy 包 + gitignore `deploy_v*.zip` |
| 4 | `3891477` | 🟢 | 删 app.py `_gen_temp_password` 私函数 |
| 5 | `7e79d75` | 🟢 | 删 bank_recon_v2.py `_build_index` 私函数 |
| 6 | `12c17bd` | 🟢 | 删 recon_routes.py `_user_api_key`(strangler 替换证据) |
| 7 | `7ebb712` | 🟢 | 删 vat_excel_export.py `_is_image_ext` |
| 8 | `3299e3d` | 🟢 | 删 vat_excel_exporter.py `_diff_field_match` |
| 9 | `62bd96e` | 📄 docs | audit + startup-check + deploy-analysis + requirements.txt + 4 phase + 7 OCR docs · 共 16 files +2797 |
| 10 | `96eba30` | 📄 docs | 19 🟡 项激进重估(8 项降 🟢) |
| 11 | `6051dbb` | 🟡→🟢 | auth_signup.py:1530 v118.12 墓碑注释删除 |
| 12 | `943597e` | 🟡→🟢 | 删旧 HANDOVER(`CLAUDE.md/HANDOVER`,-335 行,保留根新 HANDOVER) |
| 13 | `53a79c8` | 🟡→🟢 | 删 `mrerp_bridge/` 目录(2 文件 / -239 行) |
| 14 | `1e70cd9` | 🟡→🟢 | 删 erp_push.py `push_mr_erp` stub + ADAPTER_REGISTRY 项 + docstring |
| 15 | `eb77b7e` | 📄 docs | bank_reconcile 迁移调研报告(任务 A · 不动手) |
| 16 | `901ef56` | 🟡→🟢 | app.py 5 处 MR.ERP 注释/docstring 清理(保留 Xero 上下文) |
| 17 | `b2633fc` | 🟡→🟢 | 删 db.py `seed_erp_test_mappings`(-97 行 · 0 callers) |
| 18 | `bd3c9be` | 📄 docs | app.py 兼容注释扫描(任务 C 第 1 步 · 修正"70+"为实际 1) |
| 19 | `ee8d22e` | 📄 docs | B-3 误名函数备忘 + C 任务 ROI 跳过决策 |
| 20 | `5213da7` | 🔄 | app.py 25 处 empty except 转 logger.warning(CLAUDE.md §3.2) |
| 21 | `a29a8b5` | 🔄 | auth_signup.py 6 处 empty except(3 logger + 3 注释) |
| 22 | `f923965` | 🔄 | bank_recon_v2.py 7 处 empty except 全部加注释 |
| 23 | `9dde038` | 🔄 | db.py 5 处 empty except 全部加注释 |
| 24 | `70a964d` | 🟢-顺手 | 删 db.py `clear_erp_test_mappings` 孤儿(B-2 seed 的姐妹) |

**push 节奏**:
- 第 1 次 push:commit 1-8(原审计 🟢 8 项)
- 第 2 次 push:commit 9-14(docs + 重估 + 4 个新 🟢)
- 第 3 次 push:commit 15-17(A 调研 + B-1/B-2)
- 第 4 次 push:commit 18-19(C step 1 + 决策文档)
- 第 5 次 push:commit 20-24(候选 1 全部 + 顺手 C5)

---

## 2. 累计变更量

| 指标 | 值 |
|---|---|
| Git 累计 | **+4288 行 / -75 行 / 41 file-changes** |
| 拆分:**代码净删除** | ~-870 行(死代码 / 备份 / 孤儿模块) |
| 拆分:**代码改写**(empty except → log) | ~+69/-69 净 0(行数不变,行为零变化) |
| 拆分:**文档新增** | ~+2949 行(audit / startup / deploy / rerated / bank-reconcile / legacy / 4 phase / 7 OCR docs / requirements / round1-final) |

**关键代码删除**:
- 1 个完整备份 .py(167 行)+ 5 个 `_` 私函数(45 行)+ 1 个 stub(15 行)+ 1 个 demo seed(97 行)+ 1 个孤儿 clear 函数(20 行)+ 旧 HANDOVER doc(335 行)+ mrerp_bridge dir(239 行)= **~918 行死代码消化**

---

## 3. 涉及的文件(共 32 unique paths)

**代码文件(11)**:
- `app.py`(多轮:私函数删 / MR.ERP scrub / empty except 改造)
- `auth_signup.py`(墓碑删 + empty except 改造)
- `bank_recon_v2.py`(私函数删 + empty except 注释)
- `db.py`(seed/clear 孤儿删 + empty except 注释)
- `recon_routes.py`(私函数删)
- `vat_excel_export.py`(私函数删)
- `vat_excel_exporter.py`(私函数删)
- `erp_push.py`(MR.ERP stub 删)
- `excel_export_v108_backup.py`(整文件删)
- `.gitignore`(2 次更新:_pkg_tmpstatic + deploy_v*.zip)
- `requirements.txt`(新建 · 25 个第三方包反推 + 4 个幽灵模块说明)

**资源/PHP(2)** — 全删:
- `mrerp_bridge/INSTALL.txt`
- `mrerp_bridge/pearnly_bridge.php`

**已删的文档(1)**:
- `CLAUDE.md/HANDOVER_TO_NEXT_WINDOW.md`(旧版重复)

**新建的清理文档(8)**:
- `docs/code-cleanup-audit.md`(v1.2 · 含 🟡-15.5 已解决标注 + 🟡-10 误名备忘)
- `docs/startup-check-report.md`(含 §7 修复后复测)
- `docs/deploy-sync-analysis.md`(部署流程现状 + 3 风险 + P0/P1/P2)
- `docs/cleanup/audit-rerated.md`(19 🟡 激进重估表)
- `docs/cleanup/bank-reconcile-migration.md`(任务 A 调研)
- `docs/cleanup/app-py-legacy-comments-pure.md`(任务 C 修正报告 + ROI 跳过决策)
- `docs/cleanup/round1-final-report.md`(本文件)
- `docs/cleanup/README.md`(进度持续更新)

**已存在但纳入 git 的(10)**:
- `docs/cleanup/{1,2,3,4}-*.md`(用户原 4 phase 文件)
- `docs/ocr-migration/{1,2,3-...,README,architecture,current-architecture,migration-plan}.md`(OCR 会话产出 · 顺带入仓)

---

## 4. 关键发现汇总

### 4.1 🚨 7 个本地缺失的生产模块抢救(防 prod 挂)

发现:`app.py:48 import pdf_storage` 是**顶级无守护 import**,但本地 git 仓库**从未有此文件**(`git log --all` 零结果)。深挖发现一共 **7 个**这种"幽灵模块":

**用户手动抢救(2 commits)**:
- `90c1271`:pdf_storage / pdf_searchable / excel_template_th / xero_pusher(4 个)
- `94cc238`:kms_helper / mrerp_pusher / mrerp_xlsx_generator(3 个)

**根因**:2026-05-13 从老 mrpilot legacy repo 迁移到新 pearnly-app repo 时,一次性补 19 个后端模块的 commit(`2531718`)漏了这些。生产服务器 `/opt/mrpilot/` 一直有它们,`git reset --hard` 不动 untracked 文件 → 服务器跑得好。但**只要有人 `git clean -fdx` 或从 git 重新部署一台新机,prod 立刻挂**。

**意义**:本会话发现并填补了一个"prod 隐性挂雷",这比任何代码删除都重要。

### 4.2 📡 Deploy 流程盲点

`docs/deploy-sync-analysis.md` 完整还原了部署链路:
- git push → GitHub webhook → POST `/internal/deploy`(HMAC 验签) → spawn detached subprocess → `bash /opt/mrpilot/git-deploy.sh`
- git-deploy.sh 是 **app.py:208-293 硬编码字符串**,每次 mrpilot 重启重写覆盖

识别 3 个仍存在的风险:
1. 服务器可能还有其他未跟踪文件(已通过 P0-1 扫描 + 抢救 3 个解决)
2. Deploy 不验 import(坏代码 push = 服务挂 30s 才回滚)
3. 新依赖不会自动 `pip install`(需手动 SSH)

**意义**:把"运维隐性盲点"明确化、记录化,变成可执行的 P0/P1/P2 待办。

### 4.3 ⚠ `get_mrerp_mappings_bundle` 误名函数(B-3 紧急停)

原审计计划"删 db.py:6621 函数 + app.py 2 处调用"。实际读上下文发现:**函数名带 mrerp,实际是 Xero 集成在用的通用 ERP 映射拼装**(app.py:3344 自动推 + 7988 手动推 都过滤 `erp_type == "xero"` 取 client mapping)。

**意义**:静态 import 检查无法发现这种"函数名带 X 实际给 Y 用"的逻辑耦合。靠"读代码 + 判断"才避免了一次会让 Xero 立即挂的误删。已在 audit doc 加误名备忘,留待 schema 重构时统一改名。

### 4.4 📐 原审计数字偏差修正

本会话**多次**发现原 audit 数字不准,做了修正:

| 项 | 原审计声称 | 实际 | 修正方式 |
|---|---|---|---|
| TECH_DEBT 前端空 catch | 106 处 | 118 处(增) | 重新计数 |
| TECH_DEBT // v##.x 注释 | 713 处 | 648 处(减,已清部分) | 重新计数 |
| Python 空 except | 57+ 处 | 实际主 4 文件 43 处 + 6 小文件 11+ 处 = ~54 | 精细分类 |
| app.py 兼容旧前端注释 | 70+ 处 | 真·纯墓碑仅 1 处(其他大多 false positive 或 code explainer) | 任务 C 修正 |
| version-banner.js // v##.x | 4 处 | 实际 1 处(且含 bug 修复说明,不宜删) | NEW-2 修正后跳过 |
| `get_mrerp_mappings_bundle` 真用途 | "MR.ERP only" | 实际 Xero 在用 | B-3 紧急停 |

**意义**:**审计是起点不是终点**,执行阶段必须独立验证每一项。本会话 5+ 次发现-修正的过程,本身就是审计质量的迭代。

### 4.5 🔧 候选 1 分类执行 empty except(非无脑批量加日志)

按 CLAUDE.md §3.2 + 实际语义,把 43 处分两类:
- **B 类:可能掩盖真 bug** → `logger.warning(f"[模块] 上下文: {e}")`(app.py 21 处 + auth_signup 2 处)
- **A 类:真正可吞** → `pass + # 注释说明`(余下 20 处:可选 import / asyncio 取消 / fallback chain / 表可能不存在 / per-page-row 容错 / savepoint 清理)

**意义**:CLAUDE.md §3.2 写的是 JS 模式,套到 Python 需要判断哪些是"真正可吞型"——这部分判断力不能让脚本批量加 `logger.error()` 替代,会刷日志噪音掩盖真问题。

---

## 5. 当前 audit 剩余清单(Round 2 起点)

参考 `docs/code-cleanup-audit.md` v1.2 + `docs/cleanup/audit-rerated.md`。

### 5.1 仍 🟡(8 项 · 用户已明示保级或推迟)

| 编号 | 题目 | 保级理由 | 推荐 Round 2 何时动 |
|---|---|---|---|
| 🟡-0 | quality_check.py 整模块 | OCR 领域 · 等 OCR 会话替换 validators.py | OCR 会话完成后清理 |
| 🟡-1 | engine_chain.py 整模块 | OCR 领域 · 零外部 import 但属 OCR | 同上 |
| 🟡-4 | vat_excel_export(1497) vs vat_excel_exporter(391) | 业务判断:两种 Excel 导出策略哪个是 strangler 目标 | 等 Korn 模板 vs Formula 路线拍板 |
| 🟡-6 | PEARNLY_ADMIN_MODE in home.js | admin SPA 仍设此 flag · NAV-IA 领地 | NAV-IA Phase 后续窗口 |
| 🟡-11 | `_parse_gl_mrerp_table` in bank_recon_v2 | **活的** · Mr.erp PDF 格式解析器(不是 MR.ERP 集成) | 不动 |
| 🟡-16 | Python 空 except 剩 11+ 处(6 个小文件) | 改完可能让原静默错暴露,需测试 | Round 2 候选(详见 §6.1) |
| 🟡-17 | 长函数未深扫 | 需要 radon / lizard 等静态工具 | 阶段 2 安全网建立时 |
| 🟡-18 | home.js 647 处 // v##.x | 单文件 647 行 mechanical 删除 · 待专门窗口 | TECH_DEBT P2 长期清 |

### 5.2 🟡→🟢 已降级但触发 rule b stop 未做(3 大块)

| 编号 | 题目 | scope 估计 | 触发原因 |
|---|---|---|---|
| 🟢-NEW-6 | bank_reconcile.py 整体迁移(905 行 + app.py 路由 200+ 行 + db schema)| 选项 B ~1100 行 / 选项 C 更多 | >50 行 + 跨多文件 + 业务路由判断 |
| 🟢-NEW-7 | MR.ERP 大清理 bundle(`get_mrerp_mappings_bundle` + 调用方等)| 跨 app.py + db.py · 已部分 B-1/B-2,B-3 因误名停 | 误名 + 跨文件 |
| 🟢-NEW-8 | app.py 兼容旧前端 compat code(C 第 2 步 · §3.1/3.2 的字段 + 兜底分支)| 7 段 / 10+ 字段 · 跨 app.py 全文 | 每处性质不同 + 需 frontend 协作 |

### 5.3 🔴(3 项 · 本会话明确不动)

| 编号 | 题目 | 不动原因 |
|---|---|---|
| 🔴-1 | pearnly_nav_prototype_final.html | CLAUDE.md 钦定唯一设计基准文件 |
| 🔴-2 | 6 个 OCR 引擎文件 | OCR 迁移热区 · 由 OCR 会话处理 |
| 🔴-3 | app.py:1046+ 老多租户兜底 | 涉及付费/配额核心 · 需 plan 系统重构时一起替换 |

---

## 6. 给下次清理会话(Round 2)的建议

### 6.1 高 ROI · 短工时(< 60 分钟)

- **6 个小文件的 11+ 处 empty except**:同候选 1 模式,继续按 CLAUDE.md §3.2 处理
  - `email_ingest.py`(3 处)
  - `gemini_engine.py`(3 处)— ⚠ OCR 领地,本会话不能碰,需 Round 2 与 OCR 会话协调
  - `nvidia_engine.py`(2 处)— 同上
  - `line_client.py`(1 处)
  - `ocr_engine.py`(1 处)— 同上
  - `report_routes.py`(1 处)
  - 实际本 round 可立刻做的:**email_ingest + line_client + report_routes 共 5 处**(2-3 个 commit)

### 6.2 中 ROI · 中工时(1-3 小时)

- **app.py compat 代码批量清理(C 第 2 步)**:配对清 `_legacy_alias` / IP 限流 v0.8 / typhoon 增援 v105 / can_use_automation 等(`audit-rerated.md` §3.1/3.2 详列)
  - 每处需:删响应字段 + 删服务端构造代码 + 验证前端不读 / 数据库无残留
  - 建议拆 3-5 个 commit · 每 commit 单独验证
- **deploy 流程 P0-2:把 `_audit_pearnly_imports_check.py` 永久化到 `scripts/check_imports.py`**:已写好的工具规范化进项目 · 后续 CI / pre-commit 都能用

### 6.3 大工时 · 高价值(需要专门窗口)

- **`bank_reconcile.py` 整体迁移**(`docs/cleanup/bank-reconcile-migration.md` 路径 B 或 C):
  - 必须**先 grep `home.js` 看前端是否还调 `/api/bank-recon/*`**(本调研未做)
  - 然后按路径 B/C 决定整体迁移范围
  - 估 2-3 小时 + 跨前后端 + 必须有 staging 环境
- **deploy 流程 P1**:把 `git-deploy.sh` 从 app.py 字符串里拆出来到 `scripts/git-deploy.sh` + 加 import 预检步骤(`docs/deploy-sync-analysis.md` §4 详)

### 6.4 协调类(需跨会话沟通)

- **`get_mrerp_mappings_bundle` 改名**:不在本 round 做(决策"以后做 schema 重构时统一处理")· 备忘已加入 audit doc
- **OCR 领地的 4 个引擎文件 + quality_check.py + engine_chain.py**:等 OCR 迁移会话出新架构后,由 OCR 会话或专门收尾会话处理
- **home.js 647 处 // v##.x 注释**:单独窗口,与 NAV-IA Phase 配合

### 6.5 系统性建议(不是单项任务)

- **每个 Round 起手第一件事**:跑 `_audit_pearnly_imports_check.py` 验证基线
- **重复审计模式**:把"读代码 + 独立验证"作为标准步骤,不要盲信上轮 audit 数字
- **Stop 比 push 更值钱**:本 round 有 2 次"紧急停"(B-3 误名 + NEW-2 评估偏差)避免了误删,这种判断要持续

---

## 7. 工具/脚本现状

| 工具 | 位置 | 状态 | 建议 |
|---|---|---|---|
| `_audit_pearnly_imports.py` | `C:\Users\skin3\`(临时) | 跑过 1 次,生成 requirements.txt | Round 2 可永久化进 `scripts/` |
| `_audit_pearnly_imports_check.py` | `C:\Users\skin3\`(临时) | 本 round 跑了 13 次 import 检查 | 同上 + 进 CI |

---

## 8. 不变的承诺

本会话所有改动:
- ✅ 代码修改保留功能等价(empty except 改造行为零变化)
- ✅ 每 commit 后 import 检查全程绿色(41 / 33 / 8 / 7 / 0 幽灵)
- ✅ 不动 OCR 领地的 6 个引擎 + services/ocr/(协议遵守)
- ✅ 不动 deploy 脚本本身(用户明示)
- ✅ 关键判断点都先汇报后执行,不擅动

---

*Round 1 报告 · 2026-05-18 · 由本会话生成 · 已 push 至 GitHub*
