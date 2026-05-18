# Pearnly 审计 v2 · 激进重估(开发阶段无真用户场景)

> **生成日期**:2026-05-18
> **触发**:用户拍板「开发阶段无真实用户,strangler / 兼容老前端 / MR.ERP 残留可激进降级」
> **基础**:`docs/code-cleanup-audit.md` v1.2 的 19 项 🟡
> **不修改原审计**;本文档是叠加在原审计之上的重新分级。

---

## 降级 / 保级规则(用户给定)

**🟡 → 🟢(任一即降)**:
- 仅因"兼容老用户/老前端"标 🟡
- 仅因"可能有 DB 残留数据"标 🟡(开发阶段 DB 可清)
- 仅因"strangler 旧版可能有人用"标 🟡
- MR.ERP 相关残留(2026-05-14 全删)
- 墓碑注释

**保持 🟡**:
- 当前正在使用的核心逻辑(bank_recon_v2 主流程、auth/db 核心、PEARNLY_ADMIN_MODE)
- 涉及 deploy / git 流程(刚抢救完,别动)
- quality_check.py(OCR 领域)
- 需要业务判断的(两个 VAT 导出策略选哪个)
- 175+ 处空 except/catch(暴露错误需测试)

---

## 重估结果总览

| 原编号 | 题目 | 原级 | 新级 | 备注 |
|---|---|---|---|---|
| 🟡-0 | quality_check.py 整模块 | 🟡 | 🟡 | OCR 领域(保级) |
| 🟡-1 | engine_chain.py 整模块 | 🟡 | 🟡 | OCR 领域(保级) |
| 🟡-2 | erp_push.py:push_mr_erp stub | 🟡 | **🟢** | MR.ERP 全删 |
| 🟡-3 | bank_reconcile.py 旧版 905 行 | 🟡 | **🟢** | strangler 旧版 · ⚠ 触发 rule b stop |
| 🟡-4 | vat_excel_export vs exporter | 🟡 | 🟡 | 业务判断(保级) |
| 🟡-5 | pearnly_nav_prototype_final.html | 🟡 | 🔴 | CLAUDE.md 钦定基准(已在 🔴 区) |
| 🟡-6 | PEARNLY_ADMIN_MODE | 🟡 | 🟡 | 用户显式保级 |
| 🟡-7 | version-banner.js // v##.x 4 处 | 🟡 | **🟢** | 历史版本注释,墓碑类 |
| 🟡-8 | MODULE_EXPENSE_PRD_v2.md | 🟡 | OoS | 文档,非代码,出本审计范围 |
| 🟡-9 | app.py MR.ERP refs 8 处 | 🟡 | **🟢** | MR.ERP · ⚠ 触发 rule b stop |
| 🟡-10 | db.py MR.ERP 7 处 + 函数 | 🟡 | **🟢** | MR.ERP · 与 🟡-9 耦合,同 stop |
| 🟡-11 | bank_recon_v2:_parse_gl_mrerp_table | 🟡 | 🟡 | **活的** · Mr.erp PDF 解析(≠ MR.ERP 集成) |
| 🟡-12 | app.py 兼容旧前端注释 70+ 处 | 🟡 | **🟢** | 兼容老前端 · ⚠ 触发 rule b stop |
| 🟡-13 | auth_signup.py:1530 墓碑注释 | 🟡 | **🟢** | 墓碑注释 |
| 🟡-14 | 两个 HANDOVER_TO_NEXT_WINDOW.md | 🟡 | **🟢**(旧的) | 旧 HANDOVER 删,新的保 |
| 🟡-15 | mrerp_bridge/ 目录 | 🟡 | **🟢** | MR.ERP · 独立(无 Python import) |
| 🟡-15.5 | 4 个幽灵模块 | 🟡 | ✅ | 已解决(commit 90c1271) |
| 🟡-16 | Python 空 except: pass 57+ 处 | 🟡 | 🟡 | 用户显式保级 |
| 🟡-17 | 长函数未深扫 | 🟡 | DEF | 推迟到阶段 2 |
| 🟡-18 | home.js // v##.x 647 处 | 🟡 | 🟡 | 单文件 647 行 · 保级等专门窗口 |

**统计**:19 项 →
- 🟢 新增 **8 项**(其中 4 项触发 stop · 4 项可直接清)
- 🟡 保持 **8 项**(OCR / 核心 / 业务 / 测试敏感)
- 🔴 移入 **1 项**
- 其他 **2 项**(out of scope / deferred / resolved · 不计)

---

## 8 个新 🟢 详细评级 + 行动建议

### 🟢-NEW-1 erp_push.py:199 `push_mr_erp` stub
- **降级理由**:MR.ERP 残留(CLAUDE.md 钦定 2026-05-14 全删)
- **删除范围**:
  - `erp_push.py:199-205` def push_mr_erp(7 行)
  - `erp_push.py:223` `"mr_erp": push_mr_erp,`(1 行)
  - `erp_push.py:13` 注释"- mr_erp:Mr.ERP 预置(以后做)"(1 行 · 顺带)
- **副作用**:
  - `ADAPTER_REGISTRY` 不再含 `"mr_erp"` 键
  - `erp_push.py:245, 310` 的 `.get(adapter)` 仍正常工作(返回 None · adapter 校验拒绝)
  - `app.py:3126, 3185` 的 `adapter not in _erp.ADAPTER_REGISTRY` 校验自动拒绝 "mr_erp" adapter
  - 任何 DB 里 `erp_endpoints WHERE adapter='mr_erp'` 的记录会在添加 / 编辑时被拒
- **scope**:~9 行 in 1 file
- **rule b**:❌ 不触发(单文件小改)
- **执行**:直接清 ✅

### 🟢-NEW-2 静态版本注释(version-banner.js 4 处)
- **降级理由**:墓碑类注释 / 历史版本痕迹
- **删除范围**:`static/version-banner.js` 4 处 `^// v\d+\.` 行
- **scope**:4 行 in 1 file
- **rule b**:❌ 不触发
- **执行**:直接清 ✅

### 🟢-NEW-3 auth_signup.py:1530 墓碑注释
- **降级理由**:墓碑注释规则明示
- **删除范围**:`auth_signup.py:1530-1534` 5 行注释
  ```python
  # v118.12 · 旧版 admin_list_users / admin_user_detail 已删除
  # 原因:与 app.py:3741 路由冲突 · app.py 版数据更准(JOIN tenants)
  # 详情见 DIAGNOSTIC_v118_12.md 第一节
  # ============================================================
  ```
- **scope**:~5 行 in 1 file
- **rule b**:❌ 不触发
- **执行**:直接清 ✅

### 🟢-NEW-4 旧 HANDOVER_TO_NEXT_WINDOW.md(CLAUDE.md/ 内)
- **降级理由**:重复文档 · CLAUDE.md/HANDOVER 是 5/17 旧版 · 根目录 HANDOVER 是 5/18 新版
- **删除范围**:`CLAUDE.md/HANDOVER_TO_NEXT_WINDOW.md`(19515 字节)
- **scope**:1 文件
- **rule b**:❌ 不触发
- **执行**:直接清 ✅

### 🟢-NEW-5 mrerp_bridge/ 目录
- **降级理由**:MR.ERP 残留 · 目录独立无 Python import
- **删除范围**:`mrerp_bridge/`(目录 + INSTALL.txt + pearnly_bridge.php)
- **scope**:1 目录 / 2 文件
- **rule b**:❌ 不触发
- **执行**:直接清 ✅

---

### ⚠ 以下 3 项触发 rule b STOP(>50 行 + 跨多文件 · 我会执行到这里停下汇报)

### 🟢-NEW-6 bank_reconcile.py 整文件 905 行(strangler)
- **降级理由**:strangler 旧版 · `bank_recon_v2.py` 已替代
- **删除范围**:
  - `bank_reconcile.py`(905 行 · 整文件)
  - `app.py:3695` `import bank_reconcile as br`
  - `app.py:3821` `import bank_reconcile as br`
  - 这两处所在的路由 / 函数(需读懂上下文判断:是双轨制兜底?还是已经死路径?)
- **scope**:905 行 + 跨 2 文件 + 需理解路由逻辑
- **rule b**:✅ 触发(>50 行 + 跨多文件 + 涉及业务逻辑判断)
- **执行**:STOP 等用户审,提供详细影响范围

### 🟢-NEW-7 MR.ERP 大清理 bundle(🟡-9 + 🟡-10)
- **降级理由**:CLAUDE.md 钦定 MR.ERP 全删
- **删除范围**:
  - **app.py**:
    - 1606, 2106, 3328:注释行
    - 3067:Pydantic Field description 去 mr_erp
    - 3344:`mappings = db.get_mrerp_mappings_bundle(tid)` + 下游 mappings 使用
    - 7722, 7733, 8001:更多 MR.ERP 上下文(get_mrerp_mappings_bundle 调用)
  - **db.py**:
    - 6049:SQL 注释
    - 6506, 6528, 6554, 6581:`灌一份 mrerp 全量演示映射` 函数及内部 mrerp 引用
    - 6621-6635:`get_mrerp_mappings_bundle` 函数定义
- **scope**:跨 2 文件 · 估 50-150 行 · 涉及函数定义 + 调用方下游逻辑
- **rule b**:✅ 触发
- **执行**:STOP 等用户审,提供详细影响范围 + 建议拆解

### 🟢-NEW-8 app.py 兼容旧前端注释 + 代码 70+ 处
- **降级理由**:仅因"兼容老前端"
- **删除范围**:80+ 处 grep 命中,但每处性质不同:
  - 纯注释(墓碑式):可直接删
  - 实际兼容代码块(if 分支 / 备用字段 / fallback 路径):删了行为改变
- **scope**:难估 · 至少 70+ 处 · 跨 app.py 全文 8094 行
- **rule b**:✅ 触发(单文件但量大 + 行为风险)
- **执行**:STOP 等用户审,可能需分批

---

## 不动的 8 个 🟡(理由速记)

| 编号 | 题目 | 保级理由 |
|---|---|---|
| 🟡-0 | quality_check.py | OCR 领域 · 等 OCR 会话处理 |
| 🟡-1 | engine_chain.py | OCR 领域 |
| 🟡-4 | vat_excel_export vs exporter | 业务判断 · 哪个是 strangler 目标 |
| 🟡-6 | PEARNLY_ADMIN_MODE | NAV-IA admin SPA 仍设 flag |
| 🟡-11 | _parse_gl_mrerp_table | 活的 · Mr.erp PDF 格式解析器,不是 MR.ERP 集成 |
| 🟡-16 | Python 空 except 57+ 处 | 改完可能让原静默错暴露 · 需测试 |
| 🟡-17 | 长函数 | 推迟到阶段 2 用 radon / lizard |
| 🟡-18 | home.js 647 处 // v##.x | 单文件 647 行 mechanical 删除,建议专门窗口 |

---

## 执行顺序(任务 3 用)

按风险从低到高:

1. 🟢-NEW-3 auth_signup.py 墓碑(5 行)— **最安全 · 先做**
2. 🟢-NEW-4 删旧 HANDOVER(1 文件)
3. 🟢-NEW-2 version-banner.js 4 处版本注释
4. 🟢-NEW-5 mrerp_bridge/ 目录
5. 🟢-NEW-1 push_mr_erp stub
6. 🟢-NEW-6 / 7 / 8 → 触发 stop,只汇报不动手

每项执行后:跑 import 检查 + commit。

---

*v2 重估文档 · 2026-05-18 · 不修改原 audit*
