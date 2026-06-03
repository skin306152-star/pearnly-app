-- scripts/sql/b7_error_events.sql · REFACTOR-WA-B7 · 错误事件聚合表
--
-- 自建简单版错误聚合(不上 Sentry):未捕获 500 异常持久化到本表 · 超管后台时间线读。
-- 表新建即空 · 用普通 CREATE(非 CONCURRENTLY)· 幂等 IF NOT EXISTS。
--      psql "$DATABASE_URL" -f scripts/sql/b7_error_events.sql
--
-- 写入点:services/observability/error_store.record_error(fail-open · 写不进不影响主流程)
-- 读取点:GET /api/admin/diagnostics/errors(超管)

CREATE TABLE IF NOT EXISTS error_events (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    level       TEXT NOT NULL DEFAULT 'ERROR',
    logger      TEXT,
    message     TEXT,
    request_id  TEXT,                  -- 关联 B6 全链路 request_id
    user_id     TEXT,
    tenant_id   TEXT,
    path        TEXT,
    method      TEXT,
    status_code INTEGER,
    exc_type    TEXT,
    traceback   TEXT
);

-- 时间线主查询:ORDER BY created_at DESC
CREATE INDEX IF NOT EXISTS idx_error_events_created ON error_events (created_at DESC);
