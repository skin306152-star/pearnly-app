# T2 施工单 · 账套客户自选 + 锁定所选账套(去 DATAT 白名单 · 去 Owner 审批)

> 派自 `11-production-readiness-dispatch.md` T2。**Owner 2026-06-22 拍板(覆盖前稿)**:白名单**全部打开**·激进上生产给真实用户·**不要逐账套审批**。
> Owner 原话:"全部打开,不要一个一个搞,我要上生产给真实用户用,激进点。选错套账是他自己的事——我们只把他 ERP 的**真实账套映射出来给他自己选**,确保**我们的数据正确录入他选择的套账**就行。"
> 施工窗口:pearnly-app(去云端白名单)+ companion `D:\pearnly-companion`(锁定所选账套)。

---

## 1. 决策与边界(变了 · 以本节为准)

- **去掉 DATAT 硬白名单**(云端 + 端侧):不再"只允许 DATAT"。
- **去掉 Owner 逐账套审批机制**(前稿的 approve/revoke API 全部作废,不做)。
- **客户自选**:客户配对时从小助手探测出的**真实账套列表**里选自己那家(= **T5** 的下拉选)。这个选择就是授权。
- **职责切分(Owner 定)**:
  - **客户的事**:选哪个账套。选错 = 客户责任,我们不替他兜底、不拦。
  - **我们的事**:① 把他 ERP 的真实账套**准确映射出来**给他选(T5);② 确保数据**正确录入他选的那个账套**,不因我们的 bug 写到**别的**账套去。
- **保留的唯一闸 = 数据正确性闸(不是审批)**:写盘目标必须 == 客户所选账套(三重一致性:目录 / 公司名 / 账套名都对上所选)。这不是"批不批准",是"别写错地方"——正是 Owner 说的"确保数据正确录入他选择的套账"。**缺选择 → 拒写(fail-safe·没选不能瞎写)。**

## 2. 现状 4 写死点 → 怎么改(PM 已读真码)

| # | 位置 | 现状 | 改 |
|---|---|---|---|
| C1 | 云 `services/erp/express_push/__init__.py:19,27` | `ALLOWED_ACCOUNT_SETS=("DATAT",)` + `account_set_allowed(s)` | **去 DATAT 锁**。改 `account_set_allowed(s, endpoint)` = s 命中该端点配置的(客户所选)`account_set` 才放,否则拒(防我们映射 bug 串账套)。无 DATAT 限制。 |
| C2 | companion `dbf_schema.py:44` | `ALLOWED_DIR_TAIL=("70exp","test")` | 期望值改 = **客户所选账套目录**(配对锁进 config 的 `account_dir`)。`account_dir_allowed` = 写盘目标 == 所选目录(精确·归一)。去写死 `test`。 |
| C3 | companion `purchase_adapter.py:23` | `ALLOWED_ACCOUNT_SETS=("DATAT",)`(sales 复用) | 改读 config 的所选账套名,`payload.account_set == 所选` 才过;缺失 → 拒(fail-safe)。去写死 DATAT。 |
| C4 | companion PACK 闸 | 比 `cfg.account_company`(探测填) | 已 config 驱动·确认与所选账套同一来源·补一致性断言。 |

## 3. 施工(两段 · 比前稿少一段)

### T2-A · 云端:去 DATAT 锁,改"匹配所选账套"
- 删 `ALLOWED_ACCOUNT_SETS=("DATAT",)` 硬常量。
- `account_set_allowed(account_set, endpoint)`:取 `endpoint.config.account_set`(= 配对时客户所选,见 T5/§T2-B)→ 相等放行、不等拒(防串账套)。**无 DATAT 限制、无审批字段**。
- `enqueue.py` 两处调点(`:117`/`:166`)传 endpoint。
- **不做** approve/revoke 路由、不做审批审计字段(前稿作废)。

### T2-B · companion:锁定客户所选账套(与 T5 选择合流)
- 配对时(T5 客户从探测列表选一个)→ 把所选账套的 `account_dir`/`account_company`/`account_set` 名/`account_set_row` 锁进 config。**这就是写盘的唯一合法目标。**
- C2/C3:三重一致性闸的"期望值"全部来自这份所选 config(目录==所选目录 + 该目录 ISINFO 公司==`account_company` + payload 账套名==所选名)。任一不符 → 拒、不落盘(= 我们写错地方时的保险,非拦客户)。
- **去 DATAT 写死**:测试时客户(你)在列表里选 DATAT,就锁 DATAT;真客户选自家账套,就锁自家。同一套逻辑,无特例。
- **缺选择 fail-safe**:config 没有所选账套 → 拒写(没选不能瞎写)。

### T2-C · onboarding runbook(`14-onboarding-runbook.md`)
新事务所 0→上线:装小助手 → 本地配对窗输入配对码 + Express 登录(T1)→ 小助手探测真实账套 → **客户从列表选自家账套**(T5)→ `method=dbf` → 首张真票冒烟(直写 → PACK → 报表可见)→ 上线。含"选错账套是客户责任·请认准自家公司名"的提示文案 + 直录原理简述(给客户看)。

## 4. 测试
- 云端:① 去 DATAT 锁后,`account_set_allowed("58XXX", ep)` 在 ep 选了 58XXX 时放行、选了别的时拒。② 缺所选 → 拒。③ enqueue 两处按 endpoint 判。
- companion:① 所选=X → 只写 X、写 Y 目标被三重闸拒。② 缺所选 → fail-safe 拒。③ 三重闸算法不变(原 DATAT 用例:选 DATAT 后等价通过)。④ 既有 169 单测不破。

## 5. 验收(真机 · DATAT 当"客户选的账套"用)
1. 配对时从探测列表**选 DATAT**(显示真公司名)→ 锁定 → 写一张 → 只进 DATAT。
2. 伪造 payload 指向**别的**账套目录 → 三重闸拒、零落盘(证"我们写不错地方")。
3. config 清掉所选账套 → 拒写(fail-safe)。
4. 选真账套(部署时·你本人测)→ 数据正确落入所选账套·借贷平。
5. DATAT·写前 robocopy 备份·完事 `/MIR` 还原回 8 表基线。

## 6. 交付
- pearnly-app:去 DATAT 白名单 + `account_set_allowed` 改匹配所选 + 测试。**未验收不 push**。
- companion:C2/C3 锁所选账套 + C4 一致性 + 测试(与 T5 选择逻辑合流)。
- `14-onboarding-runbook.md`。
- 报告:5 项真机 + 云/端单测 + DATAT 还原核对。

> ⚠️ **诚实备案(Owner 已知并拍板)**:白名单全开 + 客户自选 = 上线快、客户自助。代价:客户**选错自家账套**时系统不拦(Owner 定:那是客户的责任)。我们守住的是"数据不写错地方 + 准确落入所选"。此为 Owner 明确决策,非疏漏。
