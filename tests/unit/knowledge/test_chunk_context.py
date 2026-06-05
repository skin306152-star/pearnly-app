"""Source-preview chunk fetch: returns the cited chunk + neighbours with the hit
flagged, or None when the chunk isn't visible. DB is faked at the cursor."""

from services.knowledge import search


class _FakeCursor:
    """Returns a canned target row for fetchone, canned neighbours for fetchall."""

    def __init__(self, target, neighbours):
        self._target = target
        self._neighbours = neighbours

    def execute(self, sql, params):
        self._sql = sql

    def fetchone(self):
        return self._target

    def fetchall(self):
        return self._neighbours


def test_returns_segments_with_hit_flagged():
    target = {
        "id": 42,
        "document_id": 7,
        "chunk_index": 3,
        "text": "hit",
        "filename": "policy.docx",
    }
    neighbours = [
        {"chunk_index": 2, "text": "before"},
        {"chunk_index": 3, "text": "hit"},
        {"chunk_index": 4, "text": "after"},
    ]
    cur = _FakeCursor(target, neighbours)
    ctx = search.get_chunk_context(cur, tenant_id="t1", accessible_ids=None, chunk_id=42)
    assert ctx["filename"] == "policy.docx"
    assert ctx["chunk_id"] == 42
    assert [s["chunk_index"] for s in ctx["segments"]] == [2, 3, 4]
    assert [s["matched"] for s in ctx["segments"]] == [False, True, False]


def test_returns_none_when_chunk_not_visible():
    cur = _FakeCursor(None, [])
    assert search.get_chunk_context(cur, tenant_id="t1", accessible_ids=[9], chunk_id=42) is None


from tests.unit.knowledge._pytest_adapter import build_case  # noqa: E402

TestChunkContext = build_case(globals(), "TestChunkContext")
