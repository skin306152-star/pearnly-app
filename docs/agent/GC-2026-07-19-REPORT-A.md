# GC-2026-07-19 · GC-A 交付报告

分支：`wip/gc0719-a-entrance-token`

基线：`1392f07e`（`origin/master`）

源代码提交：`490966ac`、`bca21044`、`1f680ec8`

## 1. 改动清单

- AI 门户 token 单一事实源改为 `AI.token`，只使用 `localStorage['mrpilot_token_ai']`；AI 登录、API 请求、套餐、复核和收件箱统一通过 helper 读写。
- 没有采认或迁移旧 `mrpilot_token`。上线后现有 `/ai` 用户需要重新登录一次；`pearnly_entry='ai'` 保持原样。
- 新增零副作用 `GET /api/ai/session`：只执行 `tax.filing.view` 守卫，不读取工单或客户业务数据。
- `entrance_scope` 拒绝改为可机读 `403 detail=authz.entrance_scope`；`module_disabled` 与普通 forbidden 语义保持不变。
- 销项表单区分 401、入口 403、普通 403、断网和格式/校验错误；两类 403 锁定提交直到刷新，断网和格式错可重试，401 清 AI token 并回到登录卡。
- 四语新增 `intake_err_session`、`intake_err_entrance`、`intake_err_forbidden`、`intake_err_network`，同步 bump i18n 与 AI bundle 缓存版本。
- `npm run build` 后提交 `static/dist/ai.js`、`static/dist/ai.html`；未提交无关构建产物。
- 新增后端/纯函数契约测试及 `26-entrance-token-isolation.spec.js`。18 个既有 AI 本地-stub spec 同步改用新测试 token 槽；其中唯一对未知 API 返回 404 的 spec 明确 stub 新会话探针。

范围核对：相对基线的 diff 没有 `/pos`、`/home`、`src/home` 或 `/dms` 文件，也没有新增依赖、迁移或生产数据操作。

## 2. 自测证据

### 单测与构建

- 本地全量：`python -m unittest discover -s tests -q` → `Ran 9682 tests in 86.321s`，exit 0。
- GC-A 定向单测：入口权限、路由契约及错误映射合计 142 tests → `OK`。
- CI unit（coverage）：`Ran 9399 tests in 54.958s`；总覆盖率 69.8%，覆盖率棘轮通过。
- `npm run build` → 通过；CI 的 Vite 打包一致性闸与 view-source 资产闸均通过。

Windows 本地全量测试按仓库既有环境要求设置 `PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`、`RATE_LIMIT_ENABLED=true`，并把 Git Bash `bin` 加入 `PATH`；未因此改动业务代码。

### 逐文件 lint 与机械闸

- `python -m black --check routes/workorder_routes.py services/authz/deps.py tests/unit/test_entrance_scope.py tests/unit/test_workorder_routes_contract.py tests/unit/test_ai_intake_errors_pure.py` → 通过。
- `python -m ruff check`（同上 Python 文件）→ 通过。
- `npx prettier --check`（全部本单 JS、HTML、E2E 文件）→ 通过。
- `npx eslint`（全部本单前端 JS）→ 通过。
- `node --check`（全部本单 JS 与 E2E spec）→ 通过。
- `npm run format:check`、`python scripts/check_imports.py --quiet`、`python scripts/check_i18n.py --strict` → 通过；四语各 4904 keys，0 missing/extra。
- `python scripts/check_file_size.py` → 1212/1212，FAIL 0。
- `python scripts/check_line_ratchet.py --base origin/master --head HEAD` → 受监控后端文件净增 0，PASS。
- `python scripts/check_ui_consistency.py`、`python scripts/check_theme_responsive.py --gate`、`python scripts/check_new_debt.py`、`python scripts/check_cachebust.py`、`git diff --check` → 全部通过。

### 真浏览器 E2E

- `npx playwright test tests/e2e/26-entrance-token-isolation.spec.js --repeat-each=2` → 6 passed（9.1s）。
- 受新 token 槽直接影响的既有 AI 本地-stub 回归：156 passed；补齐会话探针 stub 后剩余 10/10 passed。
- 源代码批次 CI 全量 Playwright：183 passed（4.7m）。
- 双 tab 实际请求头断言：POS 登录后，销项提交仍为 `Authorization: Bearer ai-fake-token`；AI 槽保持 `ai-fake-token`，主槽为 `pos-fake-token`。
- 403/断网/401 均使用 `isVisible`、`getComputedStyle` 与真实截图；格式错另有页面断言。

截图：

- `tests/e2e/_artifacts/gc0719_a/01-token-isolation-entrance-403.png`
- `tests/e2e/_artifacts/gc0719_a/02-network-retryable.png`
- `tests/e2e/_artifacts/gc0719_a/03-session-expired-login.png`

CI 绿灯：[source batch · run 29673570515](https://github.com/skin306152-star/pearnly-app/actions/runs/29673570515)

## 3. 验收标准逐条对照

1. **做到：双入口同浏览器互不串权。** 同一 browser context 先登录 AI、再登录 POS，销项请求头仍使用 AI 假 token；截图与 localStorage 双槽断言齐全。
2. **做到：失败状态如实。** 入口 403、401、断网、格式错四种文案分别出现；普通 403 纯函数分支也有测试。`authz.entrance_scope` 已从后端 detail 贯通前端锁定态。
3. **做到：token 与范围收口。** `rg -n "mrpilot_token" static/ai` 仅 `static/ai/ai-api.js` 的 `mrpilot_token_ai` 定义命中；diff 无 pos/home/dms 文件。
4. **做到：产物、缓存与交付齐全。** bundle 与 `?v=` 同提交，源代码批次 CI 全绿，本报告明确 `/ai` 用户需重登一次。

## 4. 待拍板

- 项目总则记录的 GitHub CLI 路径 `C:\Program Files\GitHub CLI\gh.exe` 在本机不存在；实际安装在 WinGet package 路径。属 GC-A 单外文档维护项，本分支未修改，是否更新由验收窗口决定。

## 5. 回滚方式

按新到旧依次 revert `1f680ec8`、`bca21044`、`490966ac`，即可撤回测试适配、AI token/错误态前端和后端探针/403 细分；本单没有数据库迁移或 feature flag。

补记（2026-07-19 验收）：已在 `routes/workorder_routes.py` 顶部 docstring 补回四权分立与 `{id}` 路由 404 防枚举安全指针，文件保持 500 行。
