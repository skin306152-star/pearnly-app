-- scripts/sql/b9_perf_indexes.sql · REFACTOR-WA-B9 · 缺失索引补齐(热路径)
--
-- 审计见 docs/refactor/b9-index-audit.md。这 3 个索引补的是两张最热表的缺口:
-- 多数表(clients/exceptions/erp_*/gl_vat/cost/recon 系/users)tenant_id/user_id
-- 已有索引;ocr_history 仅 client_id、erp_push_logs 零索引,是仅存的热路径缺口。
--
-- ⚠️ 必须 CONCURRENTLY:ocr_history/erp_push_logs 在生产是大表 · 普通 CREATE INDEX
--    会锁表写(阻塞 OCR 落库/推送)· CONCURRENTLY 在线建不锁。
-- ⚠️ CONCURRENTLY 不能在事务块内 · 用 psql 默认 autocommit 逐条跑(勿包 BEGIN/COMMIT):
--      psql "$DATABASE_URL" -f scripts/sql/b9_perf_indexes.sql
--    幂等(IF NOT EXISTS)· 可重复执行。建一个失败不影响其余(逐条独立)。

-- 1) ocr_history 列表:list_ocr_history 按 user_id 过滤 + ORDER BY created_at DESC
--    + retention 的 created_at >= NOW()-INTERVAL。tenant 视图走 user_id IN(子查询)
--    同样命中 user_id 前缀。(services/ocr_history/queries.py)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ocr_history_user_created
    ON ocr_history (user_id, created_at DESC);

-- 2) erp_push_logs 推送去重:每次推送前查 (history_id, endpoint_id, user_id, status)
--    判断是否已 success 过。这是推送热路径的高频点查。(services/erp/push_store.py)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_erp_push_logs_dedup
    ON erp_push_logs (history_id, endpoint_id);

-- 3) erp_push_logs 列表:按 user_id 过滤 + 时间倒序(推送历史抽屉)。
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_erp_push_logs_user_created
    ON erp_push_logs (user_id, created_at DESC);
