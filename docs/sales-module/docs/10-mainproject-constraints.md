# 10 · 主项目约束 + 守门闸(迁回不脱轨的权威清单)

> 实扫主项目得出(2026-06-04)。迁回写代码前**逐条对照**。源头:`CLAUDE.md/CLAUDE.md`(28+ 铁律)、
> `docs/ENGINEERING_STANDARD.md`(Definition of Done)、`scripts/git-hooks/pre-push`、`.github/workflows/ci.yml`。

## 一、守门闸真相(不是 3-4 道 · 是两个执行点 + 9 脚本)

### A. pre-push 本地硬闸(`scripts/git-hooks/pre-push` · 任一红 → exit 1 → push 中止 → 不上线)

按本次改动文件范围跑:

- **改了 .py** → ruff(F821/F822)· black --check · `import app` 冒烟 · check_imports · check_i18n --strict · **全量 unittest** · check_new_debt
- **改了前端(js/mjs/ts/css/html/json)** → prettier --check(按提交内容)· eslint(`npm run lint`)· **check_ai_smell**(注释 emoji/console.log)· tsc --noEmit(若 .ts)· `vite build` · **dist 一致性**(改源必 build+提交 dist)· check_asset_bundling
- **任何改动** → check_file_size(>500 拦)· check_line_ratchet(监控文件净增 → 拦,除非 commit 写 `RATCHET-EXEMPT: <file> +<N> · <理由>`)

### B. CI(`.github/workflows/ci.yml` · 6 个 job)

1. **lint**:black + ruff + bandit(HIGH)+ pip-audit + prettier + eslint + npm audit(high)
2. **lint-size**:check_file_size + check_line_ratchet — **FAIL 模式**(整顿收官已切硬门)
3. **lint-ui**:check_ui_consistency — WARNING 模式
4. **lint-debt**:check_new_debt(禁新增 `ensure_*` / `app.py` 巨石路由)— **FAIL 模式**
5. **lint-routes**:check_new_routes_contract(新 `*_routes.py` 必带契约测试)— WARNING 模式
6. **test**:check_imports + check_i18n + unittest+coverage(`--fail-under=40` 棘轮)+ vite build + asset bundling + Playwright E2E smoke

### C. 9 个 checker 脚本(`scripts/`)

`check_ai_smell` · `check_asset_bundling` · `check_file_size` · `check_i18n` · `check_imports` ·
`check_line_ratchet` · `check_new_debt` · `check_new_routes_contract` · `check_ui_consistency`

> ⚠️ **监控清单含**所有 `*_routes.py` / `services/**/*.py` / `src/home/**`——本模块新文件**一律被这些闸管**:
> 必须 <500 行、新增即触发 ratchet(用 RATCHET-EXEMPT 透明豁免)、新路由必带契约测试。

## 二、写新功能前必答「4 问」(铁律 #28 · 拿键盘前 30 秒)

1. **领域**?(本模块 = sales)→ 进 `services/sales/` 或 `sales_routes.py`
2. **新建什么文件**?(确切路径 · 不许塞 app.py/home.js/db.py)
3. **测试在哪**?(确切路径 + ≥1 用例名 · 新文件必带测试)
4. **删什么旧文件**?(替换旧实现的同 PR 删 · 全新功能写 N/A)

答不全 → 不许开写。

## 三、技术约束(数据/schema/部署)

| 约束 | 规定 | 铁律 |
|---|---|---|
| schema 迁移 | **走 Alembic**(`alembic/versions/NNNN_*.py` · 见既有 0001-0005)· **禁新增 `ensure_*`** | #5 #21.5 #23.2 |
| 多租户键 | `tenant_id` **UUID** + RLS(`SET LOCAL app.current_tenant_id` / policy `tenant_id::text = current_setting(...)`) | #23 ENG§9 |
| FK 类型 | `client_id` 必须匹配 **`clients.id` 实际类型**(既有 PRD 为 INTEGER/BIGSERIAL · **迁回前核实** · 别照搬 UUID) | — |
| 钱 | `NUMERIC` 不用 float/REAL | ENG |
| 时间 | `TIMESTAMPTZ` 存 UTC | ENG |
| ALTER/DDL | `with db.get_cursor(commit=True)` 否则回滚 | #2 |
| 删后端字段 | 同步改 Pydantic `response_model` · 先 Optional 一版再删 | #15 |
| 状态字段 | 单一 source of truth · 多处 UI 同读一个后端字段 · 前端只读 `body.ok` | #12 |
| 部署 | push master → webhook 自动部署 · 部署前看磁盘 `df -h /` · 后清 `/tmp/pip-*` | #24 |
| 改前端源 | 必 `npm run build` + `git add static/dist` + bump `home.html ?v=` | #27 ENG |

## 四、产品/UI 约束

| 约束 | 规定 |
|---|---|
| **i18n 4 语** | **zh/en/th/ja 全齐**(对外功能)· `check_i18n --strict` 0 缺失 · 默认 th · 见 `docs/07` |
| **UI 先设计后做** | 所有界面先出稿 + Zihao 定稿才实现(死规则 · 见 README/`docs/06`) |
| 设计系统 | 遵 `CLAUDE.md/DESIGN_SYSTEM.md`(20 节视觉契约)· 对照清单见 `docs/06` §设计系统对照 |
| 主按钮 | `.btn-primary` = **品牌蓝 `#2563EB`**(走 `static/home-38-buttons.css` · 权威)· DESIGN_SYSTEM §2.1 `#1a365d` 是旧值 |
| token | 直接用 `home.css :root`(`--accent/--bg/--card/--line/--ink*/--success/--warn/--danger`)· 钱/票号套 `--font-mono` |
| 梯度 | 字号 13/12/11/14px · 圆角 input6-8/card10-12/modal12/pill999 · 按钮 min-height 40px |
| 复用组件 | `pearnlyConfirm()`(禁原生 confirm)/ **`.modal`(单据编辑/详情 · Zihao 拍板用弹窗不用抽屉)** / `.erp-subtab` / `.stat-card`(铁律 47/48 不许重造) |
| 图标 | 只用 Lucide 风 inline SVG(viewBox 16/20/24 · stroke 1.8 · currentColor)· **禁 emoji 当图标** |
| 手机端 | 必适配(@media ≤800px · 触控 ≥44px · 真机视口验) |
| 四态 UI | 加载/空/错误/有数据 都有 · 不静默吞错 |
| 状态诚实 | rows=0/failed 绝不显"成功" |
| 产品标尺 | 每个功能必须帮会计师**省 ≥1 个手动步骤** |

## 五、高敏 + 流程(本模块尤其要注意)

- **开票属高敏**(钱/合规):取连号、开出不可改、生成税务凭证 = 类计费/关键路径 →
  **先报方案再动 · Zihao 在场 · 真账号 E2E 验**(铁律 #16/#26)· **不走无人值守自动合并**。
- 开工前 `git branch --show-current` 确认在 **master**(铁律 #14)。
- commit:**Conventional Commits + `Co-Authored-By: Claude Opus 4.8`**(整顿期才加 `· REFACTOR-<id>`;
  本模块是新功能 · 整顿收官后做 · 用普通 Conventional Commits + 模块 task id)。
- 每次部署写 **4 语 release_notes**(标准官方语言 · 无技术词 · 完全覆盖不 prepend)(铁律 #6)。
- 验收:真浏览器 isVisible+getComputedStyle+截图(grep 类名不算)· 跑对应验收剧本。

## 六、与既有 PRD 的边界(防重造/防冲突)

| 既有 PRD | 覆盖什么 | 与本沙盒关系 |
|---|---|---|
| `CLAUDE.md/MODULE_EXPENSE_PRD_v2.md` | **进项/凭证中心**(Expense Center)· 明确"Paypers 一比一+超越"· LINE/OCR/代收据/PV/4语/多客户 | 客户的 Paypers 截图(รายจ่าย=支出)**归这份**·本沙盒不重做进项 |
| `CLAUDE.md/MODULE_SALE_VAT_RECON_PRD.md` | **销项税对账**(把客户 VAT 报告 ↔ 已归档发票逐行核对)· 进 `reconcile/sale-vat` | 是"对账"·**不是开票**·本沙盒补的是"开票" |
| **本沙盒** | **销项开票**(自己给客户开 ใบกำกับภาษี/ใบเสร็จ · POS 4 种选品)· 填 `sales-invoices` 空壳 | 两份既有 PRD **都没覆盖**·属真空白·复用它们的 intake/PDF/对账底座 |

> 结论:"统一智能录入引擎"愿景里,**进项侧已被 Expense PRD 规划**;本沙盒聚焦**销项开票**,
> 复用同款 intake(LINE/OCR)与 PDF 生成,不另起炉灶。迁回前再与这两份 PRD 的属主对一次口径。
