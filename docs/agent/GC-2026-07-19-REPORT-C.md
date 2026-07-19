# GC-2026-07-19 · REPORT-C 银行待定行批量分组推断

分支：`wip/gc0719-bc-bank`  
基线：`origin/master@1392f07e`  
代码提交：`121a22c1`、`11045313`  
生产状态：未合入 master、未改生产数据、未改线上闸值、未调用真实模型。

## 1. 改动清单

| 文件 | 改动 |
|---|---|
| `services/workorder/steps/bank_sales_suggest.py` | 增加票面明示 QR/EDC 销售规则、撤销/退款非销售规则、四组后端单一事实源；pending 行带 `group`，投影带 `pending_groups`。普通 `รับโอนเงิน` 仍为 pending。 |
| `services/workorder/steps/bank_sales_brain.py` | 40 行一批、单次最多 30 批；批量题面/解析硬闸；每批独立短事务；单批失败继续、连续 3 批熔断；内存进度与同工单运行互斥；task 仍为 `taxops.verdict`。 |
| `routes/workorder_bank_sales_routes.py` | run 秒回并起守护线程；新增 progress 与 decide-batch；批量裁定上限 800，同事务、任一野指纹整批回滚；既有单行 decide 不变。 |
| `static/ai/ai-api-bank-sales.js`、`ai-api.js` | 银行四端点抽成独立 API 薄层，主 API 文件降至 500 行内预算。 |
| `static/ai/ai-bank-sales-groups.js`、`ai-bank-sales-render.js` | 后端组键驱动待定区；≥฿10,000 单列，其余折叠；整组销售/非销售走站内确认框；倒推数为 0 时用中性态，不再显示 100% 超阈值。 |
| `static/ai/ai-intake-bank-sales.js`、`ai-intake.js` | run 后每 3 秒取进度，显示 done/total/失败批；409 接回既有后台任务；批量确认成功后重取 order 投影。银行动作委托回专属模块，主 intake 行数净减。 |
| `static/ai/ai-i18n-bank-sales.js` | GC-C 新文案四语独立分片，避免继续撑大既有 i18n 巨片。 |
| `static/ai/ai-bank-sales.css`、`ai.html`、`static/dist/ai.*` | 分组/小额折叠布局、资源版本 bump 与生产构建产物。 |
| `tests/unit/test_bank_sales_gc_c.py` 等 | 覆盖规则/四组、41→2 批、批异常/熔断/上限、短事务、进度互斥、批解析、路由/800 上限、API 与前端分组纯函数。 |
| `tests/e2e/gc0719_bank_sales_batch.spec.js` | 真 Chromium 以 120 条待定夹具验证后台进度、按钮 disabled、完成后分组、站内确认、批量写回、pending 清零及采用按钮解锁。 |

## 2. 自测证据

### 全量与定向测试

- 全量：`python -m unittest discover -s tests/unit` → `Ran 9715 tests in 100.4s`，`OK (skipped=109)`。
- GC-C 后端/前端定向：84 项通过；测试模型全部为注入假响应，零真实调用、零真实成本。
- 41 条待定行严格产生 2 次模型调用；异步测试记录游标模式为 `[read, commit, commit]`，证明两批各自提交。
- 个人转入、泰文退款、Thai QR 明示销售、四组 key、题面外指纹、缺行、非数组、连续三批失败与 1200 行上限均有机器断言。

### 工程硬门

- Black / Ruff：改动 Python 全绿。
- Prettier / ESLint / 全部改动 JS `node --check`：全绿。
- `npm run format:check`：全绿。
- `python scripts/check_imports.py --quiet`：通过。
- `python scripts/check_i18n.py --strict`：四语各 4904 keys，0 missing / 0 extra。
- `python scripts/check_file_size.py`：1212 文件，0 FAIL；`bank_sales_suggest.py` 正好 500 行，新模块均低于上限。
- 行数棘轮、缓存破、资产打包、新债、AI-smell：全部通过，0 新违规。
- UI 一致性/主题响应/UI design lint：均通过既有棘轮；未新增原生弹窗或黑色主按钮。
- `npm run build`：通过；`static/dist/ai.{css,html,js}` 已同步。

### 真浏览器

- `npx playwright test tests/e2e/gc0719_bank_recovery.spec.js tests/e2e/gc0719_bank_sales_batch.spec.js --reporter=line` → 3 passed。
- 进度按钮使用 `toBeDisabled()` 与可见文案断言；确认框同时检查 `toBeVisible()` 和 `getComputedStyle()`；批量请求逐条断言 6 个决策，刷新后 pending 组为 0、采用按钮 enabled。
- 截图：
  - `tests/e2e/_artifacts/gc0719_bc/03-gc-c-background-progress.png`
  - `tests/e2e/_artifacts/gc0719_bc/04-gc-c-group-confirm.png`

### CI

- 绿链：[CI run 29675558796](https://github.com/skin306152-star/pearnly-app/actions/runs/29675558796)。
- lint、lint-ui、lint-size、lint-agent、lint-debt、lint-routes、lint-model、全量 unit/coverage/build 与 182 条线上 Playwright smoke 全绿。

## 3. 验收标准逐条对照

1. **做到**：705 行按 `ceil(705/40)=18` 次模型调用，低于约 20 次；HTTP 只做鉴权、回放待定数和起线程后秒回；进度含 running/total/done/failed_batches/status。
2. **做到**：每批单独提交 append-only 事件；重启后内存互斥清空，但 `pending_rows` 跳过已有建议且事件 dedupe 锚行指纹，继续补剩余行、不重判已提交批次。
3. **做到**：待定行最多四组，每组“发起批量动作 + 确认”两击，典型分布最多 8 击；大额逐行可看，小额无 705 个单行按钮路径。
4. **做到**：普通 `รับโอนเงิน` 明确保持 pending；只有票面明示销售渠道或 EDC 强互证才自动 sales，代码走查与单测双证。
5. **做到**：本地全量、构建、全部工程闸、真 Chromium 与分支 CI 全绿，REPORT 附截图及绿链。

## 4. 待拍板

无。施工中未发现需要越过 GC-C 边界处理的新问题。

## 5. 回滚

按逆序 revert `11045313`、`121a22c1`。紧急止血可关闭 `pearnly_ai_bank_sales_suggest`；端点随闸 404，人工销项原路径不受影响，已落建议事件保留为审计证据且不会写申报数。
