# B9 · DB 索引审计(REFACTOR-WA-B9 · 2026-06-04)

## 结论

全表扫描审计后,**仅两张最热表存在热路径索引缺口**,补 3 个索引。其余表
(clients / exceptions / erp_* mappings / gl_vat / cost / recon 系 / users / billing /
notification / membership)的 tenant_id / user_id / status / 时间倒序均已建索引,无需新增。

补齐脚本:[`scripts/sql/b9_perf_indexes.sql`](../../scripts/sql/b9_perf_indexes.sql)(`CONCURRENTLY` 在线建 · 幂等)。

## 缺口与依据

| 表 | 现有索引 | 缺口(热查询) | 新增索引 |
|---|---|---|---|
| `ocr_history` | 仅 `client_id`(partial)、`workspace` | `list_ocr_history` 按 `user_id` 过滤 + `ORDER BY created_at DESC` + retention `created_at >=`(最热读路径 · services/ocr_history/queries.py)· tenant 视图走 `user_id IN(子查询)` 同样命中 user_id 前缀 | `idx_ocr_history_user_created (user_id, created_at DESC)` |
| `erp_push_logs` | **零索引** | ① 每次推送前去重点查 `(history_id, endpoint_id, user_id, status)`(推送热路径 · push_store.py)② 列表按 `user_id` + 时间倒序 | `idx_erp_push_logs_dedup (history_id, endpoint_id)`、`idx_erp_push_logs_user_created (user_id, created_at DESC)` |

## 为何 `CONCURRENTLY` 且带外执行(不进启动 ensure)

`ocr_history` / `erp_push_logs` 在生产是大表。普通 `CREATE INDEX` 持有表级写锁直到建完,
会阻塞 OCR 落库 / ERP 推送。`CREATE INDEX CONCURRENTLY` 在线建不锁写,是大厂对线上大表
加索引的标准做法。`CONCURRENTLY` 不能在事务块内运行,故不放进每次启动跑的 `ensure_*`
(那是事务 + 会在每次重启时对大表加锁),改为带外一次性执行 + 幂等 `IF NOT EXISTS`。

注:`ocr_history` / `erp_push_logs` 是核心遗留表,现有代码只 `ALTER`/查询、不 `CREATE`
(生产历史遗留)· 故索引以独立 SQL 脚本为权威来源(可重复执行)· 不依赖启动建表路径。

## 应用(一次性 · 生产)

```bash
# 在生产应用服务器上(DATABASE_URL 在 /opt/mrpilot/.env)
psql "$DATABASE_URL" -f scripts/sql/b9_perf_indexes.sql
# 验证:
psql "$DATABASE_URL" -c "\d+ ocr_history" | grep idx_ocr_history_user_created
psql "$DATABASE_URL" -c "\d+ erp_push_logs"
```

幂等 · 可重复跑。建一个失败不影响其余(逐条独立 autocommit)。
