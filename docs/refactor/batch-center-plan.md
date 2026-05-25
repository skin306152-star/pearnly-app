# 批次中心(Batch Center)· B5 最小方案(设计 · 暂不上线)

> 2026-05-26 · 纯本地设计。**不改上传/推送主路径行为、不改 push log 状态机、不动 schema**(除非 Zihao 确认 batch_id)。
> 已落地的本地件:`services/erp/batch_view.py`(纯派生聚合器·非接入)+ 契约测试。

## 1. 现有状态流(只读梳理)

`erp_push_logs` 现有列:`id / user_id / endpoint_id / history_id / invoice_no / seller_name / total_amount / status / http_status / request_body / response_body / error_msg / attempt / elapsed_ms / trigger / created_at / retry_count / max_retries / next_retry_at`。

**status 白名单(CHECK)**:`success / failed / skipped_dup / pending / retrying`(实际主路径只产生前三个;pending/retrying 保留未用)。

**三条产生路径**(均在**推送完成后**才插一条终态 log → 这就是"日志先空白"的来源):
- **auto_push**(`_auto_push_history`·OCR 完成 hook):去重(`has_recent_successful_push`→`skipped_dup`)→ 推 → 插 log(`success`/`failed`,trigger=`auto`)。技术错且非用户数据错 → `schedule_log_retry` 设 `next_retry_at`(status 仍 `failed`)。
- **manual push**(`/api/erp/push`):同上,trigger=`manual`。
- **retry loop**(`_erp_retry_loop` 每 30s):`list_logs_due_for_retry`(`status='failed' AND next_retry_at<=NOW AND retry_count<max`)→ 重推 → 更新同一条 log。
- **用户数据错**(`is_user_data_error`:ERR_NO_CUSTOMER_MAPPING 等)→ **不**排重试,status 留 `failed`,等用户处理。

## 2. 展示态:从现有字段**派生**,不新增状态源

批次中心要的 4+ 个展示态,全部由 `batch_view.classify_push_log(row)` 纯派生(不改状态机):

| 展示态 | 派生条件(只读现有列) |
|---|---|
| ✅ 已推送 success | `status='success'` |
| ⏭ 已推过 skipped | `status='skipped_dup'` |
| 🔄 重试中 retrying | `status='failed'` + `next_retry_at` 有 + `retry_count<max_retries` |
| ⚠️ 需处理 needs_action | `status='failed'` + `is_user_data_error(error_msg)`(如缺映射) |
| ❌ 失败 failed | `status='failed'` 其余(技术终态/到上限) |
| (queued/running) | 预留 · 当前主路径不产生(若未来入队即写 log 才有·属状态机改动·本期不做) |

→ **零 DB 写、零状态机改动**。`summarize_logs(rows)` 一次 O(N) 出各态计数(100/1000 张同样)。

## 3. 唯一需要的 schema 改动:batch_id(⚠️ 待确认)

一次上传 N 张发票要聚合成"一个批次",需要 `erp_push_logs` 加一列:

```
batch_id TEXT NULL        -- 同一次上传共享一个 id(uuid4)· 加索引 (batch_id)
```

- **这是 schema 改动 → 按你的规矩,先停下来等确认,不实现。**
- 写入点(待确认后):上传/推送时生成一个 batch_id 透传到 insert_push_log。**这会碰推送主路径的 insert 调用 → 也需你确认**。
- 过渡(无 batch_id 时):`group_into_batches` 已能把无 batch_id 的行归入单一隐式批次,schema 落地后零改动复用。

## 4. 最小 API(待确认后做 · 新 `batch_routes.py`)

- `GET /api/erp/batches?limit=N` → 最近 N 个批次,每个返 `batch_view.summarize_logs` 的聚合(total/success/needs_action/retrying/failed/skipped)+ 批次名/时间/endpoint。
- `GET /api/erp/batches/{batch_id}` → 该批明细行(可按展示态过滤)+ 每行 reason/友好文案。
- 复用现有 `list_push_logs`(只读)+ `batch_view`,**不碰推送主路径**。

## 5. UI 与"只弹一次 toast"(待确认后做 · src/home 模块·非接入)

- 上传后**不再每张弹 toast**;前端拿该 batch 的聚合,弹**一个**:
  『已上传 100 张 · 成功 92 · 需处理 6 · 重试中 2』。
- 点进批次 → 四个分组列表(成功/需处理/重试中/失败)+ 每条友好原因(复用 `mrerp_business_friendly`)+ 需处理项给"一键修(绑客户/补字段)+重推"。
- 1000 张:后端聚合(GROUP BY batch_id)· 前端只渲染计数 + 分页明细 · 不一次性拉 1000 行。

## 6. 本期边界(严格)
- ✅ 只做:本设计文档 + `batch_view.py` 纯派生聚合器(非接入)+ 契约测试。
- ⛔ 不做(需确认):batch_id schema、batch_routes 接入、上传/推送 insert 加 batch_id、前端接入、单 toast 上线、queued/running 状态机扩展。
- 遇到上述任一,先停下来给方案。
