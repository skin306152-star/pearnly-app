# 代码质量 Canon(全项目约束 · 2026-07-08 拍板)

> 分法(项目铁律哲学):**能机械化的质量 → 做成 CI 闸(红=停);机械不了的 → 写成铁律(评审/设计纪律)。**
> 本文件只补 `CLAUDE.md/CLAUDE.md` 28 铁律与现有 12 道闸**未覆盖**的代码质量项,不重复。行业名对照见文末。

---

## A. 已有闸 → 覆盖到的原则(确认,不重做)

| 原则 | 行业名 | 现有闸 |
|---|---|---|
| 单文件 <500 行 | — | `check_file_size.py` |
| 行数只降不升 | 防技术债累积 | `check_line_ratchet.py` |
| 去 AI 味 / 无调试残留 | Clean Code | `check_ai_smell.py` |
| 无坏/循环 import | 低耦合 | `check_imports.py` · `check_tracked_imports.py` |
| 新增技术债拦截 | Technical Debt | `check_new_debt.py` |
| 授权覆盖 | — | `check_authz_coverage.py` |
| 状态单一事实源 | SSOT | 铁律 #12 |
| 响应码 ≠ 业务成功 | Fail Fast / 状态诚实 | 铁律 #9 |

**这些已在,新代码继续吃。下面只加缺的。**

---

## B. 新增闸(可机械化 · 按 warn→fail 落地)

> 落地方式照 `lint-ui`/`lint-size` 先例:**先 warn 模式挂 CI 跑一轮 → 清完存量 → 切 fail 硬门**。不一上来 fail 炸存量。

### 闸-Q1 · 圈复杂度上限(Cyclomatic Complexity)
- 工具:`ruff` 规则 `C901`,`max-complexity = 12`(Python);JS 用 `eslint complexity`。
- 拦:单函数分支过多(if/for/while 嵌套爆炸)= 该拆。

### 闸-Q2 · 函数体量 / 参数数上限
- 工具:`ruff` `PLR0913`(参数 >5 拦)+ 函数行数上限(`PLR0915` 语句数 / 自写 `check_func_size`)。
- 拦:巨函数、参数一长串(SRP 破坏信号)。

### 闸-Q3 · 重复代码(DRY)
- 工具:`jscpd`(JS/TS)+ `pylint duplicate-code`(Python),阈值 = 连续 ≥8 行重复。
- 拦:复制粘贴。**注意 Rule of Three:重复 2 次放行,第 3 次拦**(防过早/错误抽象)。

### 闸-Q4 · 换大脑不写死(依赖倒置的机械部分)✅ 已上线(WARN)
- 脚本 `scripts/check_no_hardcoded_model.py`(2026-07-08 建)· 挂 CI `lint-model`(WARN · continue-on-error)。
- 白名单(模型名合法归属地):`services/ai_gateway/**`、`services/ocr/gemini_models.py`、`cost.py`、`engine_policy.py`、`scripts/agent_brain_ab.py`;测试(`tests/**`)不扫。
- 业务逻辑(`services`/`routes`/`core`)里出现具体模型名 = 违规。
- **存量 4 处(待清完切 `--fail` 硬门)**:
  - `services/importer/ai_mapping.py:25`(`RECON_AI_MAPPING_MODEL` 默认 `gemini-2.5-flash-lite`)
  - `services/knowledge/generation.py:15`(`MODEL = "gemini-2.5-flash"` 参考默认)
  - `services/ocr/shadow_money.py:146,163`(影子读写死 `gemini-3.5-flash`)
  - 修法:改从 `gemini_models` 取 tier,别写死。**均在 OCR/recon 路径,按"改主路径先报方案"另起,不夹带。**

### 闸-Q5 · 未用 import / 未用变量
- 工具:`ruff` `F401`/`F841`(多半已在 ruff 配置,确认开 fail)。

---

## C. 代码质量铁律(机械不了 · 评审/设计纪律 · CQ 命名空间,不占用现有 #编号)

> 每条 = 一句约束 + 为什么。PR 评审对照。命中 = 打回。

### CQ-1 · 依赖倒置:换供应商走接口,不写死
核心逻辑只依赖抽象接口(`Brain`/`Provider`),不依赖具体 Claude/Gemini/OpenAI。换大脑 = 改一行注入/配置,业务零改动。**why**:供应商会换、会涨价、会下线;写死 = 绑架。闸-Q4 兜机械部分,接口设计靠评审。

### CQ-2 · 幂等:写操作 / 推送 / 扣费必须幂等 ⭐钱命门
同一操作重复执行,结果不变(靠幂等键 / 去重台账)。**why**:网络重试、用户重复点、worker 重跑——不幂等 = 重复推 ERP、重复扣钱。高敏路径必须带幂等键 + 守门测试证"重复调用只生效一次"。

### CQ-3 · Fail Fast + 状态诚实:不吞错、不假成功 ⭐钱命门
错误当场大声报,绝不静默吞掉或吞成默认值;`rows=0`/`failed`/`ERR_*` 绝不显示"成功"(扩展铁律 #9)。**why**:钱软件里"悄悄错"比"明着崩"危险十倍——今天 2647 就是闸报警才被抓到。宁可举手交人,不许假绿。

### CQ-4 · 高内聚低耦合 + 单一职责
一个文件/函数/模块只干一件事,块与块之间尽量少牵扯。**why**:这是 <500 行闸背后的"魂";行数达标但一个函数干五件事,照样是屎山。

### CQ-5 · KISS / YAGNI:最小实现,用不到的现在别写
只写"当前需求跑通所需"的最小代码,不预建抽象、不留"以后可能用得上"的死代码。**why**:未来的需求多半和你猜的不一样;预写 = 屎山 + 错误抽象。

### CQ-6 · 让非法状态无法表示
用类型/结构从根上让错误的数据组合拼不出来(如:互斥字段建成 union 而非并列可空)。**why**:防御式 if 检查是补漏;结构上不可能才是根治。

### CQ-7 · 童子军法则:越改越干净
每次改一块,顺手清掉碰到的坏味道(死代码、烂命名、重复),让它比来时更干净。**why**:屎山是一次次"先不管"攒出来的;反向攒才治本。

### CQ-8 · 顺序:先跑通 → 再写对 → 再写快
先让它 work,再重构 right,最后才 optimize。**why**:过早优化是万恶之源(Knuth);没跑通就调性能 = 优化了错的东西。

---

## D. 钱软件四条命门(建 Pearnly AI / 任何涉钱路径盯死)

> 从上面挑出**对"管钱"最要命**的四条,单列以防漏:

1. **CQ-1 依赖倒置** —— 换大脑不改逻辑
2. **CQ-2 幂等** —— 推 ERP / 扣费不重复
3. **CQ-3 Fail Fast + 状态诚实** —— 不假成功
4. **CQ-4 高内聚低耦合 + <500** —— 不堆屎山

---

## 行业名对照(速查)

Clean Code · SOLID(SRP/OCP/LSP/ISP/DIP)· KISS · YAGNI · DRY · Rule of Three · High Cohesion / Low Coupling · Law of Demeter · Fail Fast · Idempotency · Single Source of Truth · Make illegal states unrepresentable · Boy Scout Rule · Technical Debt · Cyclomatic Complexity · Premature Optimization · Software Craftsmanship。

---

## 落地状态

- [x] **闸-Q4**(换大脑不写死)· 脚本 + CI `lint-model`(WARN)· 2026-07-08 上线 · 存量 4 处已列
- [x] **CQ-1~CQ-8** 评审铁律 · 已成文(本文件)· 进 PR 评审清单
- [x] `CLAUDE.md/CLAUDE.md` 铁律区加指针 → 本文件
- [ ] 闸-Q1/Q2/Q3/Q5(圈复杂度/函数体量/重复码/未用符号)· 写脚本 + CI **warn** 跑一轮量存量 → 清完切 **fail**
- [ ] 闸-Q4 存量 4 处清理(OCR/recon 路径 · 按"改主路径先报方案"另起)→ 脚本挂 `--fail` 切硬门
