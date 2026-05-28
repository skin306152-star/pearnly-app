# ADR-011 · 3 窗口并行 loop 策略(Parallel Loop Strategy · Window A / B / C)

**状态**:Accepted(2026-05-28 · 窗口 C 拍 · REFACTOR-WC-P4)
**关联铁律**:#16(C 档位 push 授权)· #19(接力 protocol)· #21(整改不污染整顿)· #26(无人值守安全区 + 自主 loop 例外)· #27/#28(防屎山闸 + 4 问)
**关联文档**:`docs/refactor/AUTONOMOUS_LOOP.md` · `docs/refactor/BATCH_AGENT_DISPATCH_TEMPLATE.md` · `docs/refactor/BATCH_STRATEGY.md` · `STATE_PEARNLY.md`
**关联 ADR**:ADR-008(batch 并行重构)· ADR-009(自主重构 loop)· ADR-010(防屎山机制 · 由窗口 C 产出)

---

## 1. 背景(Context)

Pearnly 整顿期(2026-05-22 起约 5-8 个月)9 阶段 60+ task · 单窗口跑会严重 bottleneck:
- B 阶段:app.py / db.py / auth_signup.py / login.html 拆搬删 · 工程量大 · 高敏(Zihao 在场为佳)
- C 阶段:home.js / home.html / home.css 拆搬删 · 工程量大 · 跟 B 串行会拖长
- D 阶段:integration / E2E / visual 测试 · 跟 B/C 是辅助 · 不该排队
- F-I 阶段:工程化 / 监控 / 文档 / 收尾 · 大量纯文档活 · 0 风险

**问题**:单窗口串行会卡 5-8 个月 · Zihao 真实 deadline ~ 2026-12。

**Zihao 2026-05-28 拍板**:**3 窗口并行**(本 ADR · 窗口 C 写)
- 窗口 A:某轨(占位 · Zihao 可决定)
- 窗口 B:某轨(占位 · Zihao 可决定)
- 窗口 C(本文)· **防屎山闸 + 文档 + 测试** · 0 业务代码 · 不阻塞 A/B 工作

---

## 2. 决策(Decision)

把整顿 9 阶段 task 按"是否碰业务代码 + 风险等级"切 3 道工:**A / B / C**。

### 工 · 窗口 A(主拆主线 · Zihao 在场 / 高敏 OK)

**领域**:
- B1 / B2 / B3 巨石拆搬删主线(app.py / db.py / auth_signup.py)
- 含🔴高敏块(billing/charge_ocr / auth/verify_password / RLS 等)
- 走铁律 #26 自主 loop 例外(4 条安全替身 · 真账号 E2E 兜底)或 Zihao 在场两档

**特征**:
- 改业务代码(.py)
- 高敏区涉及钱 / 登录 / 数据完整性
- 每 commit 需 17/17 E2E 真账号兜底(铁律 #26 替身 B)
- 失败自动回滚(替身 C)

**当前进度**(2026-05-28):
- db.py 3356 → 819(-2537 · -76%)· billing/credits/auth/account_merge/usage 等 13 域抽出
- app.py 10060 → 3288(-6772 · -67%)· 30+ router 抽出
- home.html 6568 → 4410(-2158 · -33%)· C3 head 内联 style 抽出

### 工 · 窗口 B(前端 + Vite 拆主线 · 长跑)

**领域**:
- C1 / C2 / C3 home.js / home.html / home.css 拆搬删
- 走 Vite + ES modules · src/home/* 模块化
- 跟 A 平行(B 不动 .py · A 不动 .js / .html)· 互不冲突

**特征**:
- 改前端代码(.js / .html / .css)
- 改 home.js 顶层函数群需 window 桥接(routeTo 中枢)· 需细心
- E2E spec 03-08 兜底(home tabs)
- 视觉回归(本窗口 C 产出 D5)兜底

**当前进度**(2026-05-28):
- home.css 16124 → 0(-100% · C2 完结)
- home.js 33768 → 6190(-82%)· I1 silent error 清零 · 顶层函数群桥接待续
- home.html 6568 → 4410(-33%)· C3 内联 style 抽 · body section 抽待"运行期模板机制"

### 工 · 窗口 C(本文 · 防屎山 + 文档 + 测试 · 0 业务代码)

**领域**(本窗口实际产出):
- **第一块**:防屎山 4 件套(REFACTOR-WC-P1)
  - 铁律 #27 + #28 写入项目宪法
  - `scripts/check_file_size.py` + `scripts/check_line_ratchet.py` · 零依赖
  - CI `lint-size` job(warning 模式)
  - `tests/unit/test_anti_bigfile.py` 19 守门测试
- **第二块**:G 阶段文档 5 项(REFACTOR-WC-P2)
  - G3 `docs/ONBOARDING.md`(新协作者 + 新 AI 窗口)
  - G4 `docs/openapi.md`(36 router 索引)
  - G5 `.github/ISSUE_TEMPLATE/question.md`
  - G6 `docs/CHANGELOG.md`(git-cliff 配置方案 · 暂不上 CI)
  - G7 `.github/CODEOWNERS`(高敏路径标记)
- **第三块**:集成 + 视觉测试(REFACTOR-WC-P3)
  - D2 21 个集成测试(8 域 · env-gated)
  - D5 10 页视觉回归 + 独立 Playwright config + README
- **第四块**:ADR 2 个(REFACTOR-WC-P4 · 本文 + ADR-010)

**硬约束**(本窗口 C 启动时 Zihao 写)· 只 touch:
```
- CLAUDE.md/*.md(改铁律)
- .github/workflows/ci.yml + .github/*.md / PULL_REQUEST_TEMPLATE / ISSUE_TEMPLATE/
- scripts/*.py(改棘轮脚本)
- tests/integration/* / tests/visual/*(纯新增)
- docs/**/*.md(写文档/ADR)
- README.md / CONTRIBUTING.md
```

绝不改:
```
- 任何 .py 业务文件 / .js / .html / .css / vite.config.js / package.json
```

**违反 = 立刻停下不 push · 开 PR 等 Zihao**(防 C 跟 A/B 抢同文件 merge 冲突)。

---

## 3. 替选方案(Alternatives Considered)

### 替选 A · 单窗口串行(现状之前)
- ✅ 0 协调成本
- ❌ Zihao 在线时间是 bottleneck(他不在 = 整顿停)
- ❌ 5-8 个月 deadline 不达
- **拒绝**:整顿期需要持续推进 · 单窗口太慢

### 替选 B · 2 窗口(主线 A + 副线 C)
- ✅ A 推主线 · C 做辅助 · 不冲突
- ❌ A 窗口要同时管 B(前端)+ B(后端)· 注意力分散
- **拒绝**:3 窗口拆"前 / 后 / 辅助" 更清晰

### 替选 C · 5+ 窗口超并行
- ✅ 极快
- ❌ merge 冲突指数级增长(超过 3 窗口同时改 home.js / app.py 会大爆炸)
- ❌ 主控协调成本指数级
- **拒绝**:3 是经验值最优 · 再多 ROI 下降

### 替选 D · 接外部协作者(人类 + AI)
- ✅ 真正并行
- ❌ 整顿期 onboarding 成本高(必读 CLAUDE.md 28 铁律 + STATE + 主计划 + 当前 task)
- ❌ Pearnly 私库 · 协作者审查重
- **暂缓**:整顿后期可加 1-2 个外协 reviewer · 当前 Claude / Codex 已够

---

## 4. 协调机制(Coordination)

### 4.1 文件 ownership 分工(防 merge 冲突)

| 窗口 | 主要 touch | 绝不 touch |
|---|---|---|
| A | `app.py` / `db.py` / `auth_signup.py` / `*_routes.py` / `services/**/*.py` | `home.*` / `src/home/**` / `tests/visual/` |
| B | `home.js` / `home.html` / `home.css` / `src/home/**/*.{js,css}` / `vite.config.*` | `*.py` / `services/` |
| C | `CLAUDE.md/*.md` / `docs/**/*.md` / `.github/` / `scripts/*.py` / `tests/integration/*` / `tests/visual/*` | 所有业务代码 |

**唯一可能冲突的边界**:`tests/unit/test_*_contract.py`
- A 抽出 service 同时加 contract test → 跟 B / C 的契约测试 add 在同目录
- 解决:测试文件名不重复(`test_<feature>_contract.py` 唯一)+ pull rebase 不 merge

### 4.2 Push 同步(铁律 #16)

- 每个窗口独立 push:`git push origin master`
- Push 前必 rebase:`git pull --rebase origin master` 防别窗口 push 在前
- 红即 `git revert HEAD` + 单独 push · 绝不留红
- 独立 `gh run watch <id> --exit-status` 查 CI 真绿(铁律 #22)

### 4.3 STATE 接力(铁律 #19)

- 每个窗口收尾必更新 `STATE_PEARNLY.md` 头部:本窗口完成的 task + commit hash + 数字变化
- 主计划"当前进度看板"对应 task 状态:待 → 做中 → 已完成
- 写一句话给下个窗口/下个并行窗口:"我做完 X · 下一步建议做 Y"

### 4.4 真账号 env 共享

- env(`PEARNLY_E2E_USER` / `_PASS` / `_ADMIN_USER` / `_ADMIN_PASS`)走 HKCU `setx`(铁律见 STATE)
- 每个 claude-code 子进程不继承 → 每次跑 playwright 必先 PS 桥接
- **绝不**入 git / 日志 / 文件(本会话起明确硬线)
- E2E 跑完:`rm tests/e2e/.auth/state.json`(含 token)

### 4.5 高敏边界(铁律 #26)

- 🔴 高敏文件(`auth*.py` / `services/billing/charge.py` / `db.py` 钱写入 / RLS / `home.js` 高敏 4 块)
- 只允许窗口 A 在场或自主 loop 例外做(真账号 E2E 闸兜底)
- 窗口 B / C 永远不动这些

---

## 5. 风险 & 缓解(Risks & Mitigations)

| 风险 | 触发概率 | 缓解 |
|---|---|---|
| 3 窗口同时 push 致 CI cancelled(`concurrency` cancel-in-progress)| 高 | concurrency 是 feature 不是 bug · 只留最新一个跑;每 commit 单独 push + 独立查 CI 真绿;红就 revert |
| 窗口越界(C 改了业务代码)| 中 | 本 ADR §2 / §4.1 文件 ownership 写死;CODEOWNERS 自动 @ Zihao;每 commit message 必标 REFACTOR-W{A,B,C}-XX |
| Merge 冲突(A 拆 db.py 同时 B 改 home.js 引用)| 低-中 | A / B 文件区域不重叠;只在 contract test 边界可能冲突;`git pull --rebase` 解 |
| Zihao 不知道哪个窗口在做啥 | 中 | STATE_PEARNLY.md 头部明确标"窗口 A 当前 task / 窗口 B 当前 task / 窗口 C 当前 task";主计划进度看板对齐 |
| 接力 agent 误进错窗口范围 | 高 | 入窗口必读铁律 #19(必读 4 文档)+ 本 ADR + 当前窗口的 hard 约束(每次 prompt 顶部有写)|
| C 窗口纯文档 / 测试 commit 过多 · 占 git log 噪音 | 低 | git-cliff(ADR-010 提到)+ `docs(state):` skip 模式 · CHANGELOG 不显示 |

---

## 6. 验证(How we'll know it works)

**短期(每窗口几小时跑完一波)**:
- 3 窗口 commit hash 不冲突 · Git log 清晰可追溯(grep `REFACTOR-WA-` / `WB-` / `WC-`)
- Push 不 cancel · 都跑完 CI(单独 push 策略生效)
- STATE 头部跟得上 3 个窗口进度

**中期(1-2 个月)**:
- 整顿综合进度提升速度 ≈ 单窗口的 2.5x(不是 3x · 协调成本 ~17%)
- 没出现"3 窗口改同文件"merge 冲突(文件 ownership 生效)
- 防屎山闸数据(refactor_progress.py)显示 A / B 拆得动 · 窗口 C 的 ADR / 文档 / 测试也跟得上

**长期(5-8 个月 deadline)**:
- 整顿期按时 / 提前收官(2026-12 / 2027-02 之前 ≥ 90%)
- 收尾时 ADR-012 复盘:"3 窗口并行实际节约了 N 个月"

---

## 7. 退场策略(Exit)

整顿期收官后(综合进度 ≥ 90% + Zihao 拍板"切硬门")· 3 窗口并行机制**自然降级**:
- 窗口 A 主线完成 · 转 normal 开发(单窗口)
- 窗口 B 前端 + Vite 完成 · 转 normal 开发
- 窗口 C 防屎山闸 / 文档 / 测试 = 已上线运转 · 不再需要专属窗口

**进入"维护期"**:
- 单窗口接 issue / hotfix / 新功能(整顿期外允许 feat 了)
- 防屎山 4 件套切 fail 模式 · 任何 push 涨监控文件 = CI 红
- 不再需要"工 A / B / C" 划分

---

## 8. 后续相关 ADR

- ADR-012 · 防屎山闸切 fail 模式 retrospective(切完之后写)
- ADR-013 · 整顿期收官报告(综合 ≥ 90% 后)
- ADR-014 · 维护期开发流程(单窗口 + 必带测试)

---

## 9. 参考

- 本 ADR 实践数据来自:窗口 C(2026-05-28)实跑 · 见 `docs/refactor/WINDOW_C_COMPLETE.md` 总结
- 自主 loop 机制:`docs/refactor/AUTONOMOUS_LOOP.md` · ADR-009
- 防屎山闸机制:本窗口 C 产 · ADR-010
- batch 并行模式(旧版本):ADR-008
- 接力 protocol:CLAUDE.md 铁律 #19
- C 档位 push 授权:CLAUDE.md 铁律 #16
