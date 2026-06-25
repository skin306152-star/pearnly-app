-- B8 多租户 RLS · 回滚脚本(REFACTOR-B8 · P0 设计 §6 承诺)
--
-- 何时用:prod 逐域开 RLS(P3)后出现「某域查询返空 / 写入被拒」,需立即恢复旧行为。
--
-- 回滚有两道,按生效快慢:
--   ① 主回滚(最快·无需本脚本):撤掉业务连接的角色切换 —— systemd 删 `RLS_ROLE` env 后
--      `systemctl restart mrpilot`。get_cursor_rls 不再 `SET LOCAL ROLE pearnly_app`,
--      连接退回 owner 角色(prod owner 带 BYPASSRLS)→ 所有 policy 立即被绕过 → 全站恢复旧行为。
--      DB 层不动一行。这是出事时的第一手。
--   ② 表级回滚(本脚本):把已 force 的表 `NO FORCE` + `DISABLE`,policy 留着不碍事。
--      只有当某表 `apply_*(force=True)` 后、且想在【不撤 env】的前提下单独放掉该表时才需要。
--
-- 幂等:对未开 RLS 的表无副作用。policy 保留(再次 `apply_*` 即 DROP+重建)。
-- 数据驱动:遍历所有带本项目 policy(名 `tenant_isolation`)的表,自动覆盖当前 enrolled 集合,
--           不维护硬编码表名(防与 services/*/schema.py 的 _RLS_TABLES 漂移)。
-- 执行身份:owner / 超管连接(需 ALTER TABLE 权限)。psql 或 Supabase SQL editor 直接跑。

\echo '== RLS 回滚:NO FORCE + DISABLE 所有带 tenant_isolation policy 的表 =='

DO $$
DECLARE
    r record;
    n int := 0;
BEGIN
    FOR r IN
        SELECT DISTINCT c.relname AS tbl
        FROM pg_policy p
        JOIN pg_class c ON c.oid = p.polrelid
        JOIN pg_namespace ns ON ns.oid = c.relnamespace
        WHERE p.polname = 'tenant_isolation'
          AND ns.nspname = 'public'
        ORDER BY c.relname
    LOOP
        EXECUTE format('ALTER TABLE public.%I NO FORCE ROW LEVEL SECURITY', r.tbl);
        EXECUTE format('ALTER TABLE public.%I DISABLE ROW LEVEL SECURITY', r.tbl);
        RAISE NOTICE 'rolled back: %', r.tbl;
        n := n + 1;
    END LOOP;
    RAISE NOTICE 'done: % 张表已 NO FORCE + DISABLE', n;
END $$;

-- 校验:跑完应 0 行(无表仍启用 RLS)。
\echo '== 校验:仍 ENABLE RLS 的表(应为空)=='
SELECT c.relname AS still_enabled
FROM pg_class c
JOIN pg_namespace ns ON ns.oid = c.relnamespace
WHERE ns.nspname = 'public'
  AND c.relkind = 'r'
  AND c.relrowsecurity
ORDER BY c.relname;
