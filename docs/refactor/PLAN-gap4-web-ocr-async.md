# 方案 · 缺口④ Web 上传统一异步(待 Zihao 批 + OCR 窗口收工后实施)

> 状态:**方案待批**。OCR 窗口正在改 `ocr_recognize_routes.py`/pipeline,实施前必须等其收工或明确分工,避免热路径撞车。
> 高敏路径(铁律 #26:登录鉴权 + 计费扣费 + ERP 自动推送),先报方案后动手。
> 调研依据见本文件「附:落点 file:line」,全部落在现有代码上。

---

## 1. 目标 & 范围

把网页上传 `POST /api/ocr/recognize` 从**同步内联跑 OCR**(请求挂着等整条跑完)改为**异步入队**:上传即返回 `job_id`,后台 worker 跑 OCR,前端轮询拿进度+结果。让 LINE / 邮件 / 网页三条进件统一走异步队列。

**只做**:网页上传链路异步化 + 进度可见。
**不做**:⑤ 存储归档(Zihao 暂缓);不重写 pipeline 本身;不动 LINE/邮件已异步的链路。

**为什么做**:Zihao 确认上传**以多页/批量为主**——正是同步链路最痛的场景(干等、event loop 被阻塞、长任务超时、不能连传)。

---

## 2. 现状(同步)的问题

`routes/ocr_recognize_routes.py:38-484` 单路由内顺序跑完:校验 → 缓存 → 余额闸(402)→ **内联 sync 调 pipeline(186-195,阻塞 event loop)** → persist → 计费(persist.py:231-249,已是 fire-and-forget)→ 自动推送(361-365)→ 返回完整 JSON(442-484)。

痛点:① 多页 PDF 请求挂十几秒;② sync pipeline 阻塞 event loop(铁律 #10);③ 长任务前端 90s `AbortController` 超时(`dms-intake-invoice.ts:237`);④ 批量只能 6 路并发硬等。

---

## 3. 复用清单(不造轮子)

| 要素 | 直接复用 | 位置 |
|---|---|---|
| 异步任务表 + 状态机 + 租约 | `recon_jobs` 全套(enqueue/claim_next FOR UPDATE SKIP LOCKED/finish/fail/reclaim_stale/gc) | `services/recon_jobs/store.py` |
| 内嵌 worker(并发+poll) | `start_embedded()` + `register_handler` | `services/recon_jobs/worker.py:138,183` |
| 提交→轮询路由范式 | submit 预生成 job_id + `_credits_precheck`(同 402 语义)+ 即返;`GET /api/recon/jobs/{id}` 状态 | `routes/recon_jobs_routes.py:47,64,348` |
| OCR 专用队列(retry/backoff/幂等) | `line_ocr_jobs` 的 ON CONFLICT 幂等 + 退避 | `services/ocr/line_ocr_jobs.py` |
| **统一进件计费+持久+推送序列** | `_ingest_one_attachment`(邮件进件已把 pipeline→persist→push→charge 串好) | `services/email_ingest/email_ingest_pipeline.py:34-184` |
| 计费契约 | `charge_successful_ocr(user, quote, history_id, desc)` / `billing_quote` | `services/ocr/entrypoints.py:57,157` |
| 前端轮询器 | `window._reconPollJob(jobId, token, opts)`(1.5s 轮询、容错、onProgress) | `src/home/recon-job-poll.ts:61` |
| 结果渲染 | `ingestResult(d)` / `ocr-results.ts`(**保持 job.result 与今日 recognize JSON 同形即零改**) | `src/home/dms-intake-invoice.ts` |

---

## 4. 架构(before / after)

**现在**
```
浏览器 ──POST /api/ocr/recognize(挂住)──▶ [校验→缓存→闸→pipeline 内联→persist→charge→push] ──▶ 完整结果
```

**改后**
```
浏览器 ──POST /api/ocr/submit──▶ [校验→缓存命中即返/否则余额闸→enqueue ocr_jobs]──▶ {job_id}  (立即)
            │
            └─poll GET /api/ocr/jobs/{id}─▶ {status, progress, result?}  (1.5s)
后台 worker ──claim_next──▶ [pipeline→persist→push→charge(末步)]──▶ finish(result=同形 JSON)
```

缓存命中仍在 submit 即返(不入队、不计费),保留即时体验。

---

## 5. 新增/改动清单(逐文件 · 均 <500 行 · 各 ≥1 测试)

**新增**
- `services/ocr/jobs/store.py` — `ocr_jobs` 表 + store(克隆 `recon_jobs/store.py`,字段:id/tenant_id/user_id/workspace_client_id/status/progress/params/input_ref/result/error_code/attempts/lease_until/charged_at/时间戳)。建表内联 `apply_tenant_or_user_rls(cur,"ocr_jobs")`。
- `services/ocr/jobs/handler.py` — `job_type="web_ocr"` 处理器:复用 `_ingest_one_attachment` 那条 **pipeline→persist_invoices→dispatch_auto_push→charge** 序列;**charge 放最后一步**,成功后写 `charged_at` 再 `finish`。
- `services/ocr/jobs/worker.py` — 克隆 `start_embedded`(独立 `OCR_WORKER_CONCURRENCY`、快 poll ~1s,保证交互延迟)。
- `routes/ocr_jobs_routes.py` — `POST /api/ocr/submit`(暂存文件→`_credits_precheck`(402)→`store.enqueue`→`{ok,job_id}`)+ `GET /api/ocr/jobs/{id}`(状态/进度/result,RLS+归属校验)。
- `src/home/ocr-job-poll.ts` — 克隆 `recon-job-poll.ts`,打 `/api/ocr/jobs/{id}`。

**改动**
- `services/startup.py` — 加 `ocr_jobs_store.ensure_table()`(`startup_ddl_lock()` 内)+ `ocr_worker.start_embedded()`,**`OCR_ASYNC_WEB` flag 默认 off** 才启 worker。
- `src/home/dms-intake-invoice.ts` — `recognizeOne` 在 flag 开时改走 submit+poll;6 路并发 = 入队 N 个 job 各自轮询;`renderProcessing` 接 `progress` 显真实进度(排队/识别中/第 x/y 页)。
- 前端构建产物 `static/dist/*`(`npm run build` + 提交 dist + bump `?v=`)。

---

## 6. 计费安全(本方案最关键一节)

铁律:不重复扣、不在失败时扣、不被客户端控金额。

1. **闸在 submit**:`_credits_precheck`(= `db.get_billing_status_combined`,与现路由 131-161 同口径)→ 余额不足即 402,**不入队**。快反馈、不浪费 worker。
2. **扣费在 worker 末步**:成功 persist 拿到 primary `history_id` 后才 `charge_successful_ocr`(沿用 `charge_ocr` 语义:exempt 不扣、订阅优先抵扣、超额扣余额、可负;现 persist.py:231-249 同逻辑)。
3. **防重复扣(新增幂等)**:job 行加 `charged_at`;handler 扣费前 `if job.charged_at: skip`;扣成功立即写 `charged_at`。解决"扣费后、`finish` 前崩溃 → 重试重扣"的唯一窗口(现同步链路无此风险,异步引入,必须堵)。
4. **claim 串行**:`claim_next` 的 `FOR UPDATE SKIP LOCKED` + 租约保证一 job 同刻只一 worker;失败重试只发生在扣费前的步骤,或被 `charged_at` 挡住。
5. **金额仍服务端定**:units/kind 由 pipeline 结果算(page_count/char),客户端只传文件,延续现状。

---

## 7. ERP 自动推送

`dispatch_auto_push(history_ids, plan, user)` 从"请求内联"挪到 handler 内 persist 之后、charge 之前(顺序不变,只是搬到后台)。语义零改。

---

## 8. RLS

`ocr_jobs` 建表即 `apply_tenant_or_user_rls`(镜像 `recon_jobs/store.py:83` 与 feedback 表 `services/ocr/feedback/schema.py:49`)。worker claim 用 `get_cursor_rls(bypass=True)` 跨租户取;用户 enqueue/get 用 `get_cursor_rls(tenant_id, user_id, workspace_client_id)`。新表走启动内联 DDL,**不进 `rls_boot._ENROLLS`**(那是给无 CREATE 钩子的 legacy 表)。集成测试真表验隔离(超管聚合除外)。

---

## 9. 前端体验

上传 → 立即"已收到 · 排队中" → 真实进度(`progress` jsonb:queued→running→识别第 x/y 页→done)→ 结果就地冒出(`ingestResult` 同形,零改渲染)。批量:并发入队 + 各自轮询,可关页回来续看。失败:job.error_code → 复用现有 `f.errorKey` 人话映射。

---

## 10. 灰度 + 回退

- **flag `OCR_ASYNC_WEB`(默认 off)**:off = `/api/ocr/recognize` 同步老路**完全不变**(worker 不启、前端不走 submit);on = 走异步。
- 灰度:先内测租户开 → 观察 → 全量。
- 回退:flag 关 + 重启,秒回同步老路。新表/路由留着不碍事。
- 老 `/api/ocr/recognize` **保留**(v1 别名也依赖它),不删,做兜底。

---

## 11. 测试计划(每新文件 ≥1 测试 + 高敏真 E2E)

- `ocr_jobs` store 契约:enqueue/claim_next 租约/finish/fail/reclaim_stale。
- **计费防重扣**:模拟"扣费后 finish 前崩溃 → 重试" 断言只扣一次(`charged_at` 守门)。
- handler 序列:pipeline→persist→push→charge 顺序 + 失败不扣。
- RLS 真表:跨租户不可见、bypass claim 可取。
- 路由:submit 余额不足 402、submit 即返 job_id、get 归属校验、缓存命中 submit 即返不入队。
- E2E:真上传多页 PDF → 轮询 → 结果与同步老路逐字段一致(同形校验)。
- 全量回归 + 6 闸(black/ruff、unittest、imports、i18n、size、ratchet/new_debt)。

---

## 12. 风险 & 排期

- ⚠️ **与 OCR 窗口撞车**:④ 不改 `ocr_recognize_routes.py` 主体(submit 是新路由),但 handler 要复用 pipeline 调用 + persist/charge——这些正是 OCR 窗口在动的。**实施前必须等其收工**,然后基于其最新代码接线。
- 🔒 高敏:计费防重扣是新引入风险点(§6.3),测试必须覆盖到。
- 中风险:worker 崩溃/卡住 → 复用 `reclaim_stale` 租约回收;poll 超时 → 复用 `_reconPollJob` 20min 上限。

---

## 13. 工作量(等 OCR 窗口清场后)

复用度高,估 **1.5–2 人日**:store+worker 克隆(0.5d)、handler 接线+计费幂等(0.5d)、路由(0.25d)、前端 submit/poll/进度(0.5d)、测试+E2E+灰度(0.5d)。

---

## 14. 验收标准

- flag off:同步老路逐字段不变(回归绿)。
- flag on:多页 PDF 上传即返 job_id;前端显真实进度;结果与同步逐字段一致;**计费一票一扣(防重扣测试绿)**;ERP 自动推送照旧触发。
- 6 闸全绿;新文件均 <500 行 + 各带测试;RLS 真表隔离验过。

---

## 附:落点 file:line(实施时照此接线)

- 同步路由全序:`routes/ocr_recognize_routes.py` 校验59-101 / 缓存117-129 / 闸131-161 / pipeline186-195 / persist340-352 / push361-365 / 返回442-484。
- 扣费点:`services/ocr/recognize/persist.py:231-249`(`charge_ocr_async`,仅 primary、exempt 不扣)。
- 计费内核:`services/billing/charge.py:149`(`charge_ocr`:exempt159、订阅82、按量186-256、可负)、`:302`(`charge_ocr_async`)。
- 统一进件序列范本:`services/email_ingest/email_ingest_pipeline.py:34-184`。
- 任务框架:`services/recon_jobs/store.py`(表29-62)、`worker.py:138/183`、`routes/recon_jobs_routes.py:47/64/348`、`services/startup.py:449-465`。
- OCR 队列范本:`services/ocr/line_ocr_jobs.py`(表14-35、claim166、retry215)。
- RLS:`core.rls.apply_tenant_or_user_rls`(用例 `recon_jobs/store.py:83`、`ocr/feedback/schema.py:49`)。
- 前端:`src/home/dms-intake-invoice.ts:234-333`(recognizeOne/startRecognize)、`src/home/recon-job-poll.ts:61`(轮询器)、`ingestResult`/`ocr-results.ts`(渲染)。
