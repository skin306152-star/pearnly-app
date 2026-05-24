# ADR-005 · 对账中心异步任务化(大文件不超时 + 多用户可扩展)

> 状态:**已拍板 · 实施中**(Zihao 2026-05-24 选"两步一次到位")
> 触发:付费用户 mrerp 跑 163 行密集银行账单对账 · 报 `Unexpected token '<', "<html>..."`
> 优先级:**BUG > 整顿**(核心功能 + 影响付费用户 · 铁律 #18 允许的紧急破例)· 整顿(REFACTOR B 阶段)暂停
> 单一权威源:本文档。跨窗口接力先读这里。

---

## 1. 问题(根因)

三个对账"run"接口**全是同步阻塞**——一口气把 OCR/解析/对账跑完才返回:

| 模块 | 接口 | 同步耗时 | 落库时机 |
|---|---|---|---|
| M4 银行对账 | `POST /api/recon/bank-v2/run` (`recon_routes.py:1667`) | 10s ~ 数分钟 | 处理后 (`bank_recon_v2_task`) |
| M3 收入对账 | `POST /api/recon/gl-vat/run` (`recon_routes.py:1144`) | 5~30s | 处理中 (`reconciliation_task`/gl_vat) |
| M2 销项税 | `POST /api/vat_excel/build` (`vat_excel_routes.py:86`) | 3s ~ 5-10 分钟(800 张) | 处理后 (`vat_recon_tasks`) |

生产 Nginx **未设 `proxy_read_timeout` = 默认 60s**(已 SSH 实证:`/etc/nginx` grep 为空)。
处理 > 60s → Nginx 504 → 返回 HTML 错误页 → 前端 `home.js:19496` 的 `res.json()` **唯独这行没 `.catch()` 兜底**(全项目其他 fetch 都有)→ 抛 `Unexpected token '<'` 原样弹给用户。

**两层**:① 真根因 = 慢任务用"HTTP 长连接干等"模式 · 撞网关超时;② 症状放大 = 前端缺兜底 · 报错丑。

**规模隐患**:同步处理占住 worker/连接数分钟。单 worker uvicorn + 10~100 用户同时跑大文件 = 连接池耗尽 = 全站卡死(不止大文件用户)。

---

## 2. 现有可复用资产(为什么"最兼容")

**批量上传识别(屏 B · `/api/recon/upload_invoices`)早就是"订单号 + 轮询"模式**,生产已跑通:
- 立即返回 `progress_id`;前端每 1-2s 轮询 `GET /api/recon/progress/{pid}`(`recon_routes.py:128`)
- 5 阶段进度 + ETA · 内存 `_progress_store`(60min TTL · `recon_routes.py:88-156`)
- 前端轮询 UI:`home.js` 屏 B 流程(~29617-30976)

**已有但未接线**:`services/task_queue.py`(`InMemoryQueue` 骨架 · 注释明写"接 OCR 时换这个")。

**结论**:不发明新架构 · 复用已验证的"进度轮询"体验 + 把任务状态搬到 DB(扛重启/扛规模)。

---

## 3. 目标(对齐 Zihao 4 条要求)

| 要求 | 设计满足点 |
|---|---|
| ① 少等 | 提交后 <1s 返回 `job_id` + 实时进度条 · 永不卡死/干等 |
| ② 不报错 | 连接秒回 · 不存在超时被掐;再补前端非-JSON 兜底 |
| ③ 快拿结果 | 保留现有多文件并行 + 批量识别 + 持久缓存升级;按 job 完成即出 |
| ④ 不动识别能力 | **只改"怎么调用"不改"怎么识别"** · 解析/Gemini/对账函数原样搬进后台 |
| 多用户扩展 | DB 队列 + 后台工人 + 并发闸门(同时只跑 N 单 · 其余排队)· 100 单不崩 |

---

## 4. 架构设计

### 4.1 统一"对账任务"层(三个对账共用)

新增轻量队列/状态表 `recon_jobs`(只管状态/进度/订单号)· **结果仍写入现有三张结果表**(`bank_recon_v2_task` / `vat_recon_tasks` / `reconciliation_task`)→ 历史/导出/KPI **全不改** = 最兼容。

```
recon_jobs
  id            UUID PK (gen_random_uuid)
  job_type      TEXT     -- 'bank' | 'glvat' | 'salesvat'
  user_id       UUID
  tenant_id     UUID NULL
  status        TEXT     -- queued | running | done | failed | canceled
  progress      JSONB    -- {stage, stage_done, stage_total, current_file, eta_sec, ...}
  params        JSONB    -- gl_account / lang / anchor overrides 等
  input_ref     JSONB    -- 暂存的上传文件路径列表(见 4.4)
  result_table  TEXT NULL-- 'bank_recon_v2_task' 等
  result_id     TEXT NULL-- 对应结果表主键(完成后回填 · 前端据此取结果)
  error_code    TEXT NULL-- 业务错误码(给前端 i18n · 非栈)
  attempts      INT default 0
  max_attempts  INT default 1   -- OCR 不幂等 · 默认不自动重试(用户手动重试)
  created_at, started_at, finished_at, updated_at TIMESTAMPTZ
  worker_id     TEXT NULL       -- 认领的工人标识
  lease_until   TIMESTAMPTZ NULL-- 租约 · 工人崩了租约过期可被回收
索引: (status, created_at) · (user_id, created_at DESC) · (tenant_id, created_at DESC)
```

新 schema **走 Alembic 003**(铁律 #5/#21 · 不再 `ensure_*` 偷渡)。

### 4.2 提交(submit)流程

三个 run 接口改造为(纯瘦身 · 重活移走):
1. 鉴权 + 校验 + credits 前置检查(保留现状)
2. **暂存上传文件**(见 4.4)
3. `INSERT recon_jobs (status=queued, params, input_ref)` → 拿 `job_id`
4. 唤醒/入队 → **<1s 返回 `{ok, job_id}`**

旧同步返回保留为**兼容兜底**(feature flag `RECON_ASYNC=1` 默认开 · 关掉回退老同步路径 · 出事可秒回滚)。

### 4.3 工人(worker)· 双模式(这就是"两步一次到位")

一份工人逻辑 `services/recon_jobs/worker.py` · 两种跑法:
- **embedded(默认 · 第 1 步)**:web 进程启动时跑一个后台 asyncio 任务轮询队列 · 单进程即可工作 · **不依赖服务器改动 · 翻 flag 即生效**。
- **standalone(第 2 步 · 冲量时)**:独立 systemd 服务 `mrpilot-worker`(`deploy/mrpilot-worker.service`)· 同一份代码 `python -m services.recon_jobs.worker` · web 进程关掉 embedded 工人。

认领用 Postgres `SELECT ... FOR UPDATE SKIP LOCKED`(DB 当队列 · **不引 Redis**)· 并发闸门 = 同时认领 N 单(初始 N=2 · 可调)· 租约 `lease_until` 防工人崩了任务卡死。

工人按 `job_type` 分发到**现有**重活函数(0 改识别逻辑):
- bank → 现 `bank_v2_run` 的解析+对账段(抽成可被工人调用的 `run_bank_recon(params, files, progress_cb)`)
- glvat → 现 `gl_vat_run` 段
- salesvat → 现 `build_excel` 段

进度通过 `progress_cb` 写回 `recon_jobs.progress`(复用现有 5 阶段语义)。

> ⚠️ 内存:standalone 工人也要加载 torch/OCR 栈 · 单 Vultr 上 web+worker 双份内存 · 初期 worker 并发=1~2 · 上线前确认服务器 RAM 够(否则 OOM)。

### 4.4 上传文件暂存(关键实现点)

现在文件在 POST 内存里处理。异步后 · HTTP 已返回 · 工人要能读到文件 → submit 时落盘:
- 暂存目录 `/opt/mrpilot/var/recon_jobs/<job_id>/`(本地 docker 用挂载卷)
- `input_ref` 记路径 + 原文件名 + 类型(stmt/gl/invoice/report)
- 工人完成/失败后**清理**暂存文件(成功留 N 天可重跑 · 失败留更久排查 · 后台 GC)

### 4.5 状态查询 + 前端

统一 `GET /api/recon/jobs/{job_id}` → `{status, progress, result_table, result_id, error_code}`。
前端三个 run 流程:阻塞 fetch → **submit→轮询→出结果**(复用屏 B 轮询代码)。
完成后用 `result_id` 调现有结果接口(`/api/recon/bank-v2/{id}` 等)渲染 → 渲染/导出代码不动。
顺手修 `home.js:19496` + 同类点:`.json().catch()` + 检测非-JSON 响应 → 友好 4 语提示。

可选(长任务)·完成推送 LINE/邮件(已有基建)· 用户可离开页面。

### 4.6 Nginx(纵深防御)

`proxy_read_timeout` 仍提到 300s(`_deploy_nginx/pearnly.com.new` 已写)+ 补 `client_max_body_size`。
异步后 run 是秒回 · 超时不再是 run 的事;但导出大文件/其他长 GET 仍受益。Zihao 部署。

---

## 5. 安全/兼容/回滚

- **加性改造**:新表 + 新代码 + 新接口 · 旧同步路径保留在 `RECON_ASYNC` flag 后 · 中间每个 commit 可安全部署不破生产。
- **不碰识别**:解析/Gemini/对账函数零改 · 只换调用位置 · 识别准确率 0 影响。
- **不碰结果表/导出/历史**:结果照写老表。
- **回滚**:`RECON_ASYNC=0` 立即回老同步行为。
- **schema**:Alembic 003 · 只 `CREATE TABLE`(可逆 downgrade DROP)。

---

## 6. 实施步骤(任务清单见 TaskList)

1. ADR(本文)+ 任务拆解 ✅
2. Alembic 003 建 `recon_jobs` 表 + db.py CRUD(enqueue/claim SKIP LOCKED/update_progress/finish/get/list/gc)
3. `services/recon_jobs/`:job 模型 + 文件暂存 + 工人(embedded+standalone 双模)+ 并发闸门 + 租约回收
4. 把三个重活段抽成 `run_bank_recon / run_glvat / run_salesvat(params, input_ref, progress_cb)`(纯搬 · 守门测试锁行为)
5. 三个 run 接口改 submit(flag 后)+ 统一 `GET /api/recon/jobs/{id}`
6. 前端三流程改 submit→轮询→渲染 + 修 `.json()` 兜底(4 语)
7. 测试:job 生命周期契约 / 工人分发 / SKIP LOCKED 并发 / 状态接口 / 至少 1 个端到端 integration
8. `deploy/mrpilot-worker.service` + 部署文档(Zihao 在场上 systemd · 碰部署红线)
9. Nginx 超时/体积(Zihao)
10. 灰度:先 flag 开 embedded 验 → 稳了上 standalone 工人

---

## 7. 明确不做(防范围蔓延)

- ❌ 不引 Redis/Celery/RQ(DB 队列够用到中等规模 · 真到瓶颈再议)
- ❌ 不改 OCR/Gemini 识别逻辑、prompt、解析算法
- ❌ 不改结果表 schema / 导出格式 / 历史展示
- ❌ 不做自训模型 / 用户自定义公式(Phase 4 永久锁死 · 见审计文档)
