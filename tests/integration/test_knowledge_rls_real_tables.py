# -*- coding: utf-8 -*-
"""B8 RLS · knowledge RAG 6 表端到端隔离(REFACTOR-B8)。

6 表全部 tenant_id NOT NULL、无 user_id、workspace_client_id 可空 → 纯 tenant 模板。在真 postgres
上验:租户 A 的知识库/文档/分块/向量/答案/作业租户 B 一概读不到、塞不进(WITH CHECK);workspace_client_id
IS NULL 的 firm-wide 行在 tenant 上下文下仍可见(纯 tenant 不隐藏 NULL·回归守门·同 client_rules/risk_check)。
仓库无真 DDL(legacy 孤儿表·DDL 只在 alembic),测试自带最小建表(列对齐 prod \\d)。CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_knowledge_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
FAKE = "00000000-0000-0000-0000-0000000000ff"

# 列对齐 prod \d(只保留隔离/约束相关列;子表自带 tenant_id 不靠 fk 隔离)。
_DDL = {
    "knowledge_bases": (
        "id BIGSERIAL PRIMARY KEY, tenant_id UUID NOT NULL, workspace_client_id BIGINT, "
        "scope TEXT NOT NULL, name TEXT NOT NULL, status TEXT NOT NULL"
    ),
    "knowledge_documents": (
        "id BIGSERIAL PRIMARY KEY, tenant_id UUID NOT NULL, workspace_client_id BIGINT, "
        "knowledge_base_id BIGINT NOT NULL, source_type TEXT NOT NULL, filename TEXT NOT NULL, "
        "checksum TEXT NOT NULL, status TEXT NOT NULL"
    ),
    "knowledge_ingest_jobs": (
        "id BIGSERIAL PRIMARY KEY, tenant_id UUID NOT NULL, workspace_client_id BIGINT, "
        "document_id BIGINT NOT NULL, status TEXT NOT NULL, progress INTEGER NOT NULL DEFAULT 0, "
        "retry_count INTEGER NOT NULL DEFAULT 0, max_retries INTEGER NOT NULL DEFAULT 3"
    ),
    "knowledge_chunks": (
        "id BIGSERIAL PRIMARY KEY, tenant_id UUID NOT NULL, workspace_client_id BIGINT, "
        "document_id BIGINT NOT NULL, chunk_index INTEGER NOT NULL, text TEXT NOT NULL, "
        "char_count INTEGER NOT NULL, metadata JSONB NOT NULL DEFAULT '{}'::jsonb"
    ),
    "knowledge_embeddings": (
        "id BIGSERIAL PRIMARY KEY, tenant_id UUID NOT NULL, workspace_client_id BIGINT, "
        "chunk_id BIGINT NOT NULL, model TEXT NOT NULL"
    ),
    "knowledge_answers": (
        "id BIGSERIAL PRIMARY KEY, tenant_id UUID NOT NULL, workspace_client_id BIGINT, "
        "question TEXT NOT NULL, answer TEXT NOT NULL, citations JSONB NOT NULL, "
        "no_answer BOOLEAN NOT NULL DEFAULT false"
    ),
}

# (table, 额外列清单, 额外值清单)— 用于构造合法 INSERT。
_SEED = {
    "knowledge_bases": ("scope, name, status", "'firm','kb','ready'"),
    "knowledge_documents": (
        "knowledge_base_id, source_type, filename, checksum, status",
        "1,'file','a.pdf','c1','ready'",
    ),
    "knowledge_ingest_jobs": ("document_id, status", "1,'success'"),
    "knowledge_chunks": ("document_id, chunk_index, text, char_count", "1,0,'t',1"),
    "knowledge_embeddings": ("chunk_id, model", "1,'m'"),
    "knowledge_answers": ("question, answer, citations", "'q','a','[]'::jsonb"),
}


class KnowledgeRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.knowledge import rls as knowledge_rls

        cls.db = db
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            for table, cols in _DDL.items():
                cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                cur.execute(f"CREATE TABLE {table} ({cols})")

        knowledge_rls.ensure_knowledge_rls()  # 6 表 apply_tenant_rls

        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            for table in _DDL:
                cur.execute(f"GRANT SELECT,INSERT,UPDATE,DELETE ON {table} TO pearnly_app")
                cur.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
            cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                for table in _DDL:
                    cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            for table in _DDL:
                cur.execute(f"TRUNCATE {table} RESTART IDENTITY CASCADE")

    def _seed(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            for table, (cols, vals) in _SEED.items():
                for tid in (A, B):
                    cur.execute(f"INSERT INTO {table} (tenant_id, {cols}) VALUES ('{tid}', {vals})")

    def test_tenant_scoped(self):
        self._seed()
        for table in _DDL:
            with self.db.get_cursor_rls(tenant_id=A) as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 1, f"{table}: A 应只见自己租户 1 行")
            with self.db.get_cursor_rls(tenant_id=FAKE) as cur:
                cur.execute(f"SELECT count(*) n FROM {table}")
                self.assertEqual(cur.fetchone()["n"], 0, f"{table}: 陌生租户应见 0 行")

    def test_firm_wide_null_workspace_visible(self):
        # 纯 tenant 模板:workspace_client_id IS NULL 的 firm-wide 行在 tenant 上下文下仍可见
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO knowledge_bases (tenant_id, workspace_client_id, scope, name, status) "
                "VALUES (%s, NULL, 'firm', 'firmwide', 'ready')",
                (A,),
            )
        with self.db.get_cursor_rls(tenant_id=A) as cur:
            cur.execute("SELECT count(*) n FROM knowledge_bases")
            self.assertEqual(
                cur.fetchone()["n"], 1, "firm-wide NULL 账套行应可见(纯 tenant 不隐藏)"
            )

    def test_with_check_blocks_cross_tenant_insert(self):
        import psycopg2

        with self.db.get_cursor_rls(tenant_id=A, commit=True) as cur:
            with self.assertRaises(psycopg2.errors.Error):
                cur.execute(
                    "INSERT INTO knowledge_bases (tenant_id, scope, name, status) "
                    "VALUES (%s, 'firm', 'x', 'ready')",
                    (B,),
                )

    def test_owner_bypass_sees_all(self):
        self._seed()
        with self.db.get_cursor_rls(bypass=True) as cur:
            cur.execute("SELECT count(*) n FROM knowledge_embeddings")
            self.assertEqual(cur.fetchone()["n"], 2)


if __name__ == "__main__":
    unittest.main()
