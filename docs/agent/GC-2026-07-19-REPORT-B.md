# GC-2026-07-19 · REPORT-B 银行续页救回与完整性安全网

分支：`wip/gc0719-bc-bank`  
基线：`origin/master@1392f07e`  
代码提交：`f3dffeeb`、`18c14101`、`b32b58fb`  
生产状态：未合入 master、未改生产数据、未改任何线上闸值。

验收补记：已恢复建议引擎、分类步与收料编排的关键 why；排除件改判抽至独立 bundle 模块并补纯函数测试，未再以删注释换行数。

## 1. 改动清单

| 文件 | 改动 |
|---|---|
| `services/workorder/steps/sort.py` | 用 `category=bank + statement title` 双锁补回无银行名续页，付款截图仍不误吸。 |
| `services/workorder/steps/statement_regroup.py` | 锚区间两端扩 4 个文件号；扩展带必须额外命中对账单标题。 |
| `services/workorder/steps/classify.py` | `item_classified` 事件按需携带分类理由。 |
| `services/workorder/steps/reconcile_bank.py`、`reconcile.py` | 抽出双闸 `emit_stmt_totals`，缺销项 checkpoint-only 路径也执行；银行集合采用最新人工 `assign_kind`。 |
| `services/workorder/steps/stmt_totals.py` | 窄读异常留 warning；新增佛历账期转换、首尾日期覆盖和跨文件余额交接判据。 |
| `services/workorder/steps/bank_sales_suggest.py` | 增加日期缺口/跨段断链降级、≥5 行页计数，并向建议投影传递四语提示。 |
| `services/workorder/evidence.py`、`api.py` | 投影最多 200 个排除件；人工改判后按事件回放从排除堆消失；账期传入完整性判据。 |
| `services/workorder/decisions.py`、`routes/workorder_routes.py` | 既有 `assign_kind` 合法集加入 `bank_statement`，同步接口说明。 |
| `static/ai/ai-intake-render.js`、`ai-intake.js`、`ai-intake.css` | 收料页新增默认折叠排除堆，逐件显示原因并通过既有 decisions 端点改判；手机宽度自适应。 |
| `static/ai/ai-bank-sales-render.js` | 降级卡优先显示后端四语确定性缺口文案。 |
| `static/ai/ai-i18n-{zh,th,en,ja}-2.js` | 补齐排除堆、原因、改判和失败文案。 |
| `static/ai/ai.html`、`static/dist/ai.{html,css,js}` | bump 资源版本并提交生产构建产物。 |
| `tests/unit/test_workorder_sort.py`、`test_workorder_classify.py` | 锁定 IMG_2501 直接救回与序列锚扩尾两条独立路径，以及付款截图防误吸。 |
| `tests/unit/test_workorder_reconcile_bank.py`、`test_stmt_totals.py` | 锁定 checkpoint/full 路径 totals 调用、闸关行为、异常日志和人工银行改判。 |
| `tests/unit/test_bank_sales_suggest.py` | 锁定佛历转换、18 段日期缺口、单日不降级、单行片段排除和跨文件余额接续/断链。 |
| `tests/unit/test_workorder_evidence.py`、`test_workorder_api.py` | 锁定排除投影形状/截断/改判消失、合法 kind、order_detail 挂键和 period 透传。 |
| `tests/e2e/gc0719_bank_recovery.spec.js` | 真 Chromium 验证折叠/展开/改判请求体/刷新消失及日期缺口降级卡。 |

## 2. 自测证据

### 全量与定向测试

- 全量：`python -m unittest discover -s tests -q` → `Ran 9691 tests in 96.007s`，`OK (skipped=109)`。
- Windows 测试进程显式使用 Git Bash、UTF-8，并固定 `RATE_LIMIT_ENABLED=true`，避免 `tests/integration/_helpers.py` 的 `setdefault(false)` 污染后续限流单测；仓库与系统配置均未改。
- GC-B 三组定向命令分别 61 / 56 / 76 项通过；18 段真实形态加强后 `test_bank_sales_suggest` 27 项通过。

### 逐文件 lint

```powershell
python -m black --check routes/workorder_routes.py services/workorder/api.py services/workorder/decisions.py services/workorder/evidence.py services/workorder/steps/bank_sales_suggest.py services/workorder/steps/classify.py services/workorder/steps/reconcile.py services/workorder/steps/reconcile_bank.py services/workorder/steps/sort.py services/workorder/steps/statement_regroup.py services/workorder/steps/stmt_totals.py tests/unit/test_bank_sales_suggest.py tests/unit/test_stmt_totals.py tests/unit/test_workorder_api.py tests/unit/test_workorder_classify.py tests/unit/test_workorder_reconcile_bank.py tests/unit/test_workorder_sort.py tests/unit/test_workorder_evidence.py
python -m ruff check <同上 18 个文件>
```

结果：Black `18 files would be left unchanged`；Ruff `All checks passed`。

```powershell
npx prettier --check static/ai/ai-bank-sales-render.js static/ai/ai-i18n-en-2.js static/ai/ai-i18n-ja-2.js static/ai/ai-i18n-th-2.js static/ai/ai-i18n-zh-2.js static/ai/ai-intake-render.js static/ai/ai-intake.css static/ai/ai-intake.js static/ai/ai.html tests/e2e/gc0719_bank_recovery.spec.js
npx eslint static/ai/ai-bank-sales-render.js static/ai/ai-i18n-en-2.js static/ai/ai-i18n-ja-2.js static/ai/ai-i18n-th-2.js static/ai/ai-i18n-zh-2.js static/ai/ai-intake-render.js static/ai/ai-intake.js tests/e2e/gc0719_bank_recovery.spec.js
```

结果：Prettier 全匹配；ESLint 0 error；全部改动 JS `node --check` 通过。

### 工程硬门

- `python scripts/check_imports.py --quiet`：通过。
- `python scripts/check_i18n.py --strict`：四语各 4904 keys，0 missing / 0 extra。
- `python scripts/check_file_size.py`：1212 文件通过，0 FAIL。
- `python scripts/check_line_ratchet.py --base origin/master --head HEAD`：0 违规；3 个净减、8 个透明功能豁免。
- `python scripts/check_ui_consistency.py`、`python scripts/check_theme_responsive.py --gate`：通过棘轮。
- `node scripts/ui_design_lint.mjs --gate`：通过；小固定 max-width 保持基线 120。
- `python scripts/check_new_debt.py`、`python scripts/check_cachebust.py`、`python scripts/check_ai_smell.py`：通过。
- `npm run format:check`、`npm run build`：通过；最终 `static/dist/ai.*` 已同步。

### 真浏览器

- `npx playwright test tests/e2e/gc0719_bank_recovery.spec.js --project=chromium` → 2 passed。
- 断言同时使用 `toBeVisible()` 和 `getComputedStyle()`；改判 body 逐字段断言为 `assign_kind + bank_statement`，刷新后排除件数量为 0。
- 截图：
  - `tests/e2e/_artifacts/gc0719_bc/01-excluded-expanded.png`
  - `tests/e2e/_artifacts/gc0719_bc/02-date-gap-degrade.png`

### CI

- 绿链：[CI run 29672942775](https://github.com/skin306152-star/pearnly-app/actions/runs/29672942775)。
- lint、lint-ui、lint-size、lint-agent、lint-debt、lint-routes、lint-model、全量 unit/coverage/build/E2E 全绿。

## 3. 验收标准逐条对照

1. **做到**：IMG_2501 真实字段夹具在闸开时由 sort 直接归 `bank_statement`，闸关仍 `non_tax`；独立 Collector 场景证明锚 2484..2500 可扩尾救回 2501 并落 `item_regrouped`，2503 无标题付款件不救。
2. **做到**：18 个 `item_bank_parsed` 段、末段日期 2026-05-28、period=`2569-05` 的纯事件回放降级，并逐字列出 2026-05-29、30、31。
3. **做到**：缺 `sales_summary` 路径和完整 reconcile 路径均有 totals 正向调用测试；闸关不调用；窄读异常 warning 含工单号且不阻断。
4. **做到**：排除堆默认折叠、可见可展开、改判走既有 decisions 端点；成功后事件回放使该件从排除堆消失，既有 P-7 自动续跑不另开端点。
5. **做到**：本地全量 9690 项绿、所有硬门绿、wip 分支 CI 全绿、REPORT-B 逐条对照完成。

## 4. 待拍板

无。施工中未发现需要越过 GC-B 边界处理的新问题。

## 5. 回滚

按逆序 revert `b32b58fb`、`18c14101`、`f3dffeeb`；紧急止血可先关闭 `pearnly_ai_stmt_regroup` 与 `pearnly_ai_bank_sales_suggest`（stmt totals 与建议共用后者），无需改数据。
