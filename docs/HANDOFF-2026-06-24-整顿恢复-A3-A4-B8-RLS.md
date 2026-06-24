# 交接 · 2026-06-24 · 整顿恢复:A3 完成 / A4 搁置 / B8 RLS 推进到 P2

> 给下一个窗口。本文只写事实 + 待办。prod = master `e8074817` · 全部已 push · prod 200 · RLS 默认关、生产零影响。

## 今天的任务来源(Owner 指令序列)
1. 「读文档,重回整顿,看还有哪些未做」→ 整顿现状评估(§一)
2. 「把整顿未完成的所有任务列出来」→ 未完成清单(§一)
3. 「把 A3A4 做了」→ A3 完成(§二)、A4 搁置(§三)
4. 「继续」→ B8 多租户 RLS,Owner 给了 7 点生产级要求 → P0-P2 完成(§四)
5. 「收尾,写详细交接」→ 本文 + `/simplify`(已跑,改动干净无需改)

---

## 一、整顿现状评估(已口头交付)
- **整顿"核心"早收官**:体积/结构/防屎山闸/目录重组(I7)/前端模块化全完成。**关键验证**:06-03 收官至今 **944 commit / 3 周 feature 开发,体积闸全守住**(`check_file_size` 858 文件全 <500,FAIL 0)——防屎山闸真扛住了。
- **C5 TypeScript 化实际已达标**:`src` 下 **215 个 .ts / 仅剩 3 个 .js**(`purchase-calc.js` 被 `test_purchase_calc.py` 用 node 直跑当可执行规格、`main.js` Vite 入口、`workspace-gate-boot.js` 启动门 —— **都是有意保留,别硬转**)。进度看板写的"59/151"严重 stale,应标 ✅。
- **真正未完成**(按价值):**B8 RLS**(本窗口推进中)、**lint-ui 视觉债**(220 UI 不一致 + 967 裸 hex + 29 i18n 漏翻 · Owner-gated 从未起 · 现靠棘轮被动压)、**E 性能**(0/6)、**F 存储**(0/3)、**H 合规安全**(0/6)、**D4 覆盖率**(22.5%→70%)、**C4/C6/C7/C8/C9**、**A4**。
- **lint-routes** 仍 warning 模式没切硬门。

---

## 二、A3 本地 Docker 环境分级 — ✅ 完成上线(commit `6ace4f9d`)
**做了什么**:本机 Docker 早装好(ADR-003 写的"未装"过时),逐项跑通 ADR-003 验证清单(build/up/api-version/api-ready/dev-reload 8 项全过)。
**修了 3 个前端 bundle 化后的回归**:
1. `Dockerfile` 删过时 `cp home.html home.js home.css static/`(home.js 物理文件已不存在 → build 失败;前端走 Vite `static/dist/`)。
2. `core/db.py` `sslmode="require"` → `sslmode=os.environ.get("PGSSLMODE","require")`(**prod 默认 require 不变**;本地容器 postgres 无 SSL,compose 设 `PGSSLMODE=disable`)。
3. 验证清单路径笔误:健康检查是 `/api/ready` 不是 `/ready`。
**ADR-003 已更新**(标完成 + 记录修复)。
**独立发现(未修·非 A3)**:`services/static_assets.py:read_frontend_version` 读 `static/home.html`(bundle 化后不再产出该文件)→ `/api/version` 前端版本号在本地/容器恒为 `0`(prod 因有老部署遗留文件暂正常)。应改读 `static/dist/home.html`。**小 bug,待办。**

---

## 三、A4 Doppler Secrets — ⏸️ 搁置(卡 Owner · CLI 已装 v3.76.0)
**为什么搁置**:剩 3 步本质要 Owner:① `doppler login`(浏览器认证绑账号,我登不了)② 生产改 systemd 用 Doppler = 碰红线 #16 ③ 删旧密钥要前两步通后。
**怎么继续**(Owner 敲):`doppler login` → `doppler setup`(选 pearnly/dev)→ `doppler run -- uvicorn app:app --port 7860`。
**我的建议**:单人项目密钥散放能跑,A4 是规范化非刚需,**先放**;等多人协作或做 H6 密钥轮换时再接。第 1 步(39 密钥导入)早完成。

---

## 四、B8 多租户 RLS — P0/P1/P2 ✅ 上线 · P3/P4 待做

### 已完成(全部上线 · prod 零影响)
| 阶段 | commit | 内容 |
|---|---|---|
| P0 设计 | `b3ee95e7` | `docs/refactor/b8-rls-production-design.md`:99 表隔离矩阵 + 7 点方案 + 分批 rollout + 回滚 + 6 裁决项 |
| P1 基建 | `1138b437` | `core/rls.py` 3 policy 模板 + `ensure_rls_app_role`;`core/db.py` `get_cursor_rls` 三维上下文 + 可选 `SET LOCAL ROLE`;+6 单测 |
| P2 测试矩阵 | `e8074817` | `tests/integration/test_rls_isolation_matrix.py`:3 模板 × CRUD × 5 场景,env-gated |

**验证**:POC 裸 SQL 7/7 + 集成(真 core 模块)8/8 + 单测 4761 全绿 + CI 绿 + prod `/api/ready` db ok。

### 核心机制(已验证可行)
- **缺陷根因**:prod 连接角色带 BYPASSRLS(超级角色)→ policy 形同虚设(`12-rls-isolation.spec.js` T1/T3/T5 失败根因)。
- **解法**:最小权限角色 `pearnly_app`(NOSUPERUSER NOBYPASSRLS)+ 表 `FORCE ROW LEVEL SECURITY` + 业务连接 `SET LOCAL ROLE`(Supabase pooler 不能改连接 role,故事务级切)。
- **三维 context**:`app.current_tenant_id` + `app.current_workspace_id` + `app.current_user_id`(SET LOCAL)。
- **3 模板**:`apply_tenant_rls`(纯租户)/ `apply_tenant_workspace_rls`(租户+账套强隔离)/ `apply_tenant_or_user_rls`(tenant 可空+user 兜底孤立行)。`force` 默认 False 向后兼容现有 POS 调用。
- **开关**:env `RLS_ROLE`(设了才切角色)+ 表 `apply_*(force=True)`。**默认全关,prod 行为不变**。

### 未完成:P3 逐域启用(详细 playbook · 这是唯一碰生产数据的阶段)
**前置审计**:实测 **457 处 `get_cursor()`(无上下文)/ 113 文件**(老模块),**220 处 `get_cursor_rls()`(已带上下文)/ 51 文件**(POS/会计/销售/采购/库存/知识/LINE 新模块)。开 RLS 前,该域所有读写必须走 `get_cursor_rls`(带上下文),否则切到 NOBYPASSRLS 角色后查空。
**分域顺序**(低风险→高):① POS/库存(已大量用 rls 游标)→ ② 采购/销售/会计 → ③ 对账/知识 → ④ 老模块(clients/exceptions/notification/billing · 457 处重灾)。
**每域 rollout cycle**:
1. 审计该域查询是否全走 `get_cursor_rls`(grep `get_cursor(` 该域文件,逐个评估/改)。
2. 本地恢复库:`ensure_rls_app_role` 建角色 → 该域表 `apply_*_rls(force=True)` → 跑穿透 smoke(扩 `run_rls_isolation_tests` 或仿 P2 矩阵)。
3. staging(可选)。
4. prod:建角色(SQL/ensure)→ 设 systemd `RLS_ROLE=pearnly_app`(**碰红线 #16**)→ 该域表 `apply_*_rls(force=True)` → 冒烟 → 异常立即跑回滚。
5. **回滚**(零数据风险·幂等):`ALTER TABLE <t> NO FORCE / DISABLE ROW LEVEL SECURITY` + 撤 `RLS_ROLE` env 重启。建议落地成 `scripts/rls_rollback.sql`(P0 设计承诺·未建)。
**★风险评估更新**:Owner 2026-06-24 明确"**没有真实用户**"→ prod 启用 RLS 影响面极小,**不必死等低峰窗口、可大胆逐域上**,出问题秒回滚。这降低了 P3 的执行门槛。

### 未完成:P4 收尾
- prod 真启用后,把 `tests/e2e/12-rls-isolation.spec.js` 断言从 `passed>=2` 收紧到 **`passed===5`**(spec 顶部 E 段有 TODO 标记)。
- 回滚脚本归档 + 设计文档 §7 rollout 状态更新。

### 裁决项(P0 §6 · 已按"RLS 匹配现有隔离粒度、不改变它"原则定默认,无需 Owner 业务输入)
`line_voice_quota`(LINE 身份全局唯一·不开租户 RLS)/ `products`(现状 tenant 级共享·RLS 判 tenant)/ 订阅·付款·改密日志(绑 user·归 admin 域不开)/ Supabase 根表 users·tenants·ocr_history(单列 Supabase 侧·本批不动)/ tenant 可空表(用 `apply_tenant_or_user_rls` 兜底模板)。

---

## 五、附带:Docker Desktop 坑(记忆已记 `docker-desktop-kill-trap`)
关 Docker 别用 `Stop-Process` 强杀所有 `*docker*` 进程(会带停 `com.docker.service` → 引擎 500、手动也起不来,我今天踩了)。正确关法 = GUI Quit 或只关 `Docker Desktop.exe`。修复 = `wsl --shutdown` + `Restart-Service com.docker.service` + 重开。**开机自启已关**(删了注册表 Run 项),Owner 要求"留着 Docker"。

---

## 六、本地环境 / 资源 / 坑
- Docker Desktop **留着**(开机自启关)· db 容器 **stopped**,起:`docker compose start db`。
- 本地跑 P2 矩阵:`PEARNLY_INTEGRATION_DB=1 DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly RLS_ROLE=pearnly_app PGSSLMODE=disable python -m unittest tests.integration.test_rls_isolation_matrix -v`。
- 临时脚本(可删):`scratchpad/rls_poc.py`(裸 SQL POC)、`scratchpad/rls_integration.py`(真模块验证)。
- 共享树:push 前 `git pull --rebase` · 只 `git add` 自己文件(工作区有大量别窗口未跟踪文件,**禁 `add -A`**)。
- `core/db.py` 等是 LF · 改后 git 会警告 LF→CRLF(autocrlf),提交内容仍 LF,无害。

## 七、状态总览
- **全部已 push**(HEAD `e8074817`)· 无未 push commit · prod `/api/version` 200 · `/api/ready` db ok。
- **prod 零影响**:RLS 默认关(`RLS_ROLE` 未设、表未 `force`),新 `apply_*` 函数 P3 才调用。
- 守门:全量单测 4761 OK · check_imports 0 · check_file_size FAIL 0 · CI 绿。
