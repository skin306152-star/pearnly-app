# -*- coding: utf-8 -*-
"""scripts/dump_prod_schema.py 产物的可重放性 · 正证 + 反证。

首版快照(2026-07-31)在空库上重放,176 张表只建出 122 张:53 个 serial 列的
DEFAULT nextval('x_id_seq') 引用的序列一个都没导出,psql 逐张 `ERROR: relation
"x_id_seq" does not exist`。而快照的头号用途就是"灾备/空库重建时有据可依" ——
建不出来就等于没有。这里把"引用了就必须先建"钉成断言。

只测 render():不连库、不读快照本体(那份得等下次拿只读串重新导才会包含序列)。
"""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import dump_prod_schema as dumper  # noqa: E402

_NEXTVAL = re.compile(r"nextval\('([a-zA-Z0-9_]+)'")
_CREATE_SEQ = re.compile(r'CREATE SEQUENCE IF NOT EXISTS "([a-zA-Z0-9_]+)"')

_COLS = {
    "widgets": ["  \"id\" bigint DEFAULT nextval('widgets_id_seq'::regclass) NOT NULL"],
    "gadgets": ["  \"id\" bigint DEFAULT nextval('gadgets_id_seq'::regclass) NOT NULL"],
}
_INLINE = {"widgets": ['  CONSTRAINT "widgets_pkey" PRIMARY KEY (id)']}
_SEQS = [
    'CREATE SEQUENCE IF NOT EXISTS "gadgets_id_seq";',
    'CREATE SEQUENCE IF NOT EXISTS "widgets_id_seq";',
]


def _unresolved(sql: str) -> list:
    """输出里被 nextval 引用、却没有(在引用之前)建出来的序列。"""
    created_at = {m.group(1): m.start() for m in _CREATE_SEQ.finditer(sql)}
    return sorted(
        {
            m.group(1)
            for m in _NEXTVAL.finditer(sql)
            if m.group(1) not in created_at or created_at[m.group(1)] > m.start()
        }
    )


class RenderedSnapshotIsReplayableTests(unittest.TestCase):
    def test_referenced_sequences_are_created_first(self):
        sql = dumper.render(_COLS, _INLINE, [], {}, _SEQS)
        self.assertEqual(_unresolved(sql), [], "有序列被 nextval 引用却没先建")

    def test_check_bites_when_sequences_are_dropped(self):
        # 反证:去掉序列段(= 修复前的产物形态),同一条检查必须报出两张表都建不了。
        sql = dumper.render(_COLS, _INLINE, [], {})
        self.assertEqual(_unresolved(sql), ["gadgets_id_seq", "widgets_id_seq"])


if __name__ == "__main__":
    unittest.main()
