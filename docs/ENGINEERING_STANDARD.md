# 🏛️ Pearnly 工程标准 · 大厂级 Definition of Done(全生命周期)

> **这份文档回答一个问题:Pearnly 怎样才算"拿得上台面"。** 从源码到验收每个环节的硬标准 + **靠什么机制保证**(不靠口号靠闸)。
> 定位:整顿期的"完成定义"权威详版(`REFACTOR_MASTER_PLAN.md` 完成定义段是浓缩版)。AGENTS.md 文档地图指向本文件。
> 目标基线:**以 Claude 辅助开发的角度,工程卫生(测试/CI/无屎山/可交接)完胜 90% 大厂**;规模/安全纵深等持续逼近。
> 最后更新:2026-05-29(初版 · 含「去 AI 味」标准)

> 状态图例:✅ 已达标 · 🟡 部分 · ⚪ 未开始 · 🔒 机械闸已落(CI/脚本强制)

---

## 0. 总原则:代码要像资深工程师写的,不像 AI 生成的

每一处源码(新写的 + 老的)都要过这条:**给一个大厂资深工程师 code review,他不会一眼看出"这是 AI 写的"**。这是"拿得上台面"的底线。

---

## 1. 源码标准(含「去 AI 味」· 新旧都要过)

### 1.1 去 AI 味 —— 必须消除的 13 种痕迹 🟡(随拆模块逐个清 + I6 收尾审计)

| # | AI 味 | 大厂写法 |
|---|---|---|
| 1 | **过度注释**:每行都注释 / 注释复述代码(`i += 1 # 加一`) | 注释只写 **WHY**(为啥这么做 / 坑在哪),不写 WHAT |
| 2 | **注释/代码里的 emoji 和叙事腔**(`# 🎉 这里我们处理一下...`) | 源码注释中性、简洁、英文或精炼中文术语 · 无表情 · 无"我们/接下来" |
| 3 | **防御性冗余**:到处 try/except 吞错 / 重复 null 检查 / 不可能分支 | 只在真会失败处兜底 · 错误该抛就抛 · 信任内部不变式 |
| 4 | **泛化命名**:`data` `result` `temp` `handleClick` `doStuff` `obj` | 名字说清意图:`unpaidInvoices` `recalcVatTotals` `pushResult` |
| 5 | **docstring 套话**:复述函数签名("This function takes x and returns y") | 没有就不写;要写就写约束/副作用/坑 |
| 6 | **解释性长名 + 注释双写**:`# 检查用户是否登录` + `is_user_currently_logged_in` | 二选一 · 自解释命名 > 注释 |
| 7 | **调试残留**:`console.log` / `print()` / `# debug` / 注释掉的代码块 | 0 残留 · 调试用 logger + 删干净 · 死代码 `git rm`(铁律#7) |
| 8 | **AI 自述痕迹**:`# as requested` `# TODO: implement later` `# Note: I added` | 0 残留 · TODO 要有 issue 编号或删 |
| 9 | **不一致模式**:同一项目混用 `==`/`===`、不同错误处理风格、命名风格漂移 | 一种模式贯穿 · lint 强制 |
| 10 | **过度抽象/空壳**:为拆而拆造 1 行函数、跳转地狱、过早泛化 | 抽象服务于可读性 · 不为凑行数(主计划已禁) |
| 11 | **复制粘贴重复**:同一段逻辑 3 处略改 | 抽公共函数 · DRY |
| 12 | **魔法数字/字符串**:散落的 `30` `"failed"` `0.07` | 具名常量 · 集中配置 |
| 13 | **样板膨胀**:AI 爱写的冗长 if-else 链 / 不用语言惯用法 | 用语言惯用法(Python comprehension / JS 解构 / 早返回) |

**执行**:① B/C 窗口**抽每个模块时顺手清**(纯结构搬完顺带去味,0 改逻辑边界要谨慎) ② I6 全量审计兜底(见主计划) ③ 长期靠 lint 规则 + PR review 卡。
**注意**:本条只管**源码**(.py/.js/.css/.html)。中文规划文档(铁律/STATE 等)的 emoji/叙事是内部文档,不在此列;用户可见文案(release_notes/UI)另有铁律#6 管。

### 1.2 结构 🟡🔒
- 单源文件 **< 500 行**(🔒 `check_file_size.py` + CI lint-size · Loop 1 完切 fail 模式)· 行数只降不升(🔒 棘轮)。
- 函数单一职责 · 圈复杂度可控 · 新功能进独立模块不进巨石(🔒 铁律#17/#27)。
- 类型安全:前端 TS 80%+(C5 ⚪)· 后端 type hints(渐进)。
- 0 静默吞错(✅ home.js silent=0 · 🔒 test_anti_bigfile)。

### 1.3 风格 ✅🔒
- 🔒 black + ruff(Python)· prettier + ESLint(JS)· CI 强制 0 error · 字节级 LF 无 BOM。

---

## 2. 产品标准 🟡
- i18n 4 语完整(🔒 `check_i18n.py --strict` 0 missing/extra)· 拆 .json(C6 ⚪)。
- 设计系统:通用组件库 ≥ 8(C4 ⚪)· 视觉回归防炸(✅ D5 baseline)。
- 可访问性 WCAG 2.1 AA(C7 ⚪)· 移动端真机适配(C8 ⚪)。
- **状态诚实**:rows=0 / failed / needs_mapping 绝不显示"成功"(🔒 红线 · ERROR_CODES_AND_STATES.md)。
- 错误/加载/空态都有 UI · 不静默 · 不卡死。

---

## 3. 流程标准 🟡
- 分支:在 master 干 / 从 master 开 feature(铁律#14)· 部署 = push master 触发 webhook。
- Commit:Conventional Commits + `· REFACTOR-<id>`(整顿期)+ Co-Authored-By Opus 4.8(🔒 铁律#20)。
- **Definition of Ready**(开干前):需求清楚 / 影响面已评估 / 高敏走流程(铁律#16)。
- **Definition of Done**(本文件全部 ✅ 才算真完成):代码过 §1 · 测试过 §5 · CI 过 §6 · 验收过 §8 · 文档更新 §9。
- 30+ 文件/schema/删字段/关键路径 → 停下报方案(🔒 铁律#16 红线)。

---

## 4. 审核标准 🟡
- 每次改动过 **6 道守门**(🔒 format/unit/imports/i18n/node/build)。
- 代码审查:用 `/code-review`(质量+bug)· 高敏/上线前用 `/security-review`(OWASP)。
- 高敏路径自动 @ Zihao(✅ 🔒 `.github/CODEOWNERS`)。
- 拆模块必带契约/单元测试(🔒 硬门槛#4)· 没测试不算拆完。

---

## 5. 测试标准 🟡
- 单元 500+(✅ 1629)· 集成 20+(✅ 42)· E2E 10+(✅ 17 · 但核心路径 D1 仅 1/10 真覆盖)。
- 覆盖率 ≥ 70%(🟡 21% · 🔒 A8 棘轮只升不降)。
- Golden fixtures:用户真实坏样本变回归资产(⚪ workbench §3.1 规划)。
- 死灰复燃守门:复活即 CI 红(⚪ D3 等清单)。
- 高敏改动:真账号 E2E 闸 + 失败自动 revert(🔒 铁律#26)· 绝不触发真扣钱。

---

## 6. CI/CD 标准 🟡🔒
- CI:lint + 安全扫描(bandit/pip-audit/npm audit ✅)+ 全量测试 + build + 覆盖率棘轮 + lint-size,全绿才能合(🔒)。
- 部署:push → webhook → git-deploy.sh pull+restart · 验证 `/api/version` 200 + 看新进程时间戳(铁律#25)。
- 健康检查:`/health` + `/ready` 能真实失败(⚪ B4 · 硬门槛#7)。
- 回滚:CI 红/E2E 红 → `git revert` + 单独 push · 绝不留红在 master(🔒 铁律#26)。
- 依赖:锁定(✅ requirements.lock + package-lock)+ Dependabot 周更(✅)。

---

## 7. 可观测性标准 ⚪
- 结构化日志 JSON + request_id/user_id/tenant_id 全链路 trace(B6)。
- 错误聚合:写 errors 表 + admin 时间线(B7)。
- 性能基线:每 API 响应时间 → p50/p95/p99(E1)· OCR/AI/ERP 每次 trace id + 成本/耗时/状态(workbench §3.2)。

---

## 8. 验收标准 🟡
- 固定验收剧本:改完银行对账/收入对账/ERP/充值各跑对应剧本(🟡 `docs/agent/ACCEPTANCE_PLAYBOOKS.md`)。
- 真账号 E2E 通过才算受影响流程 OK · Zihao 像普通用户点验收。
- 改 UI 必写 4 语 release_notes 标准官方语言(🔒 铁律#6)。
- 上线后 cache_bust 翻新 + CI 真绿 + 用户能访问新版。

---

## 9. 安全 / 合规标准 🟡
- 密钥:Doppler 管(🟡 A4)· 绝不进 git(🔒 gitignore + 红线)· key 轮换流程(H6 ⚪)。
- OWASP Top 10 review:XSS/SQLi/CSRF/SSRF/auth bypass(H4 ⚪)。
- 多租户隔离:tenant 矩阵 + RLS 双保险(🟡 B8)· RLS 基础设施永不动。
- 反薅闸 5 道(✅ PLG)· 全局限流(B5 ⚪)。
- PDPA/GDPR:隐私/条款 4 语 + 数据导出 + 真删除(H1/H3/F3 ⚪)· TLS 自动续期(H5 ⚪)。

---

## 10. 文档 / 交接标准 ✅🟡
- 一页入口 AGENTS.md(✅)+ 状态卡(✅)+ 数字跑脚本(✅)+ SessionStart 自动注入(✅ hook)。
- 10+ ADR(✅ 11)· RUNBOOK(✅)· ONBOARDING(✅)· OpenAPI 公开(🟡 索引有 · /docs 未公开)。
- 业务词典 / 错误码状态机 / 验收剧本(✅ docs/agent/)。

---

## 11. 终极验收:第三方 AI 只读体检
整顿收官时,让另一个 AI 跑只读体检,报告显示 **"Google/Anthropic 级 90%+"** + 跟 2026-05-21 那次基线对比(⚪ I5)。这是"完胜 90% 大厂"的客观裁判,不是自说自话。

---

*配套:`REFACTOR_MASTER_PLAN.md`(9 阶段执行)· `AGENTS.md`(入口)· 铁律 #16/#17/#20/#26/#27 · 整顿搞完转为常态开发的 Definition of Done。*
