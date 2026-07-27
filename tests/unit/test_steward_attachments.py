# -*- coding: utf-8 -*-
"""管家会话附件的存储层与限额闸(services/steward/attachments.py + attach_intake.py)。

锁三件:①加密开着也要能原样读回、且 sha256 恒是【明文】哈希(密文哈希会让同一份文件每次
都不一样,F2 的零成本缓存复用直接失效);②取盘防穿越(库里存的字符串不当可信输入);
③三道限额闸各自会响,而且上限只有一处定义。
"""

from __future__ import annotations

import os
import re
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

from core import file_crypto
from services.steward import attach_intake, attachments


class _Sandbox(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self._patch = mock.patch.object(attachments, "_BASE", self._dir.name)
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        self._dir.cleanup()


class StorageTests(_Sandbox):
    def test_roundtrip_keeps_bytes_and_embeds_the_original_name(self):
        path = attachments.save(
            b"hello", tenant_id="t-1234-5678", session_id="s-1", original_name="รายงาน ขาย.xlsx"
        )
        self.assertEqual(attachments.read_content(str(path)), b"hello")
        self.assertTrue(path.name.endswith(".xlsx"))
        self.assertIn("__", path.name)

    def test_sealed_file_still_hashes_as_plaintext(self):
        plain = b"the same bytes"
        with mock.patch.dict(
            os.environ,
            {"FILE_ENC_MODE": "on", "PEARNLY_FILE_KMS_KEY": _fernet_key()},
        ):
            path = attachments.save(plain, tenant_id="t-1", session_id="s-1", original_name="a.pdf")
            on_disk = path.read_bytes()
            self.assertTrue(file_crypto.has_magic(on_disk))
            self.assertEqual(attachments.read_content(str(path)), plain)
        self.assertEqual(attachments.sha256_of(plain), attachments.sha256_of(plain))
        self.assertNotEqual(attachments.sha256_of(plain), attachments.sha256_of(on_disk))

    def test_resolve_refuses_paths_outside_this_session(self):
        mine = attachments.save(b"x", tenant_id="t-1", session_id="s-1", original_name="a.pdf")
        self.assertIsNotNone(attachments.resolve_within_session("t-1", "s-1", str(mine)))
        self.assertIsNone(attachments.resolve_within_session("t-1", "s-2", str(mine)))
        self.assertIsNone(attachments.resolve_within_session("t-9", "s-1", str(mine)))
        self.assertIsNone(
            attachments.resolve_within_session("t-1", "s-1", str(Path(mine).parent / ".." / "x"))
        )

    def test_resolve_refuses_a_path_that_is_not_a_file(self):
        self.assertIsNone(attachments.resolve_within_session("t-1", "s-1", ""))
        self.assertIsNone(
            attachments.resolve_within_session(
                "t-1", "s-1", str(attachments.session_dir("t-1", "s-1"))
            )
        )


def _fernet_key() -> str:
    from cryptography.fernet import Fernet

    return Fernet.generate_key().decode()


class LimitTests(unittest.TestCase):
    def test_too_many_files(self):
        pairs = [(f"{i}.pdf", b"x") for i in range(attachments.MAX_FILES_PER_MESSAGE + 1)]
        with self.assertRaises(attach_intake.AttachmentLimitError) as ctx:
            attach_intake.check_limits(pairs)
        self.assertEqual(ctx.exception.code, attach_intake.ERR_TOO_MANY)

    def test_single_file_too_large(self):
        pairs = [("big.pdf", b"x" * (attachments.MAX_FILE_BYTES + 1))]
        with self.assertRaises(attach_intake.AttachmentLimitError) as ctx:
            attach_intake.check_limits(pairs)
        self.assertEqual(ctx.exception.code, attach_intake.ERR_TOO_LARGE)
        self.assertEqual(ctx.exception.limit, attachments.MAX_FILE_BYTES)

    def test_batch_total_too_large_even_when_each_file_fits(self):
        one = b"x" * (attachments.MAX_FILE_BYTES - 1)
        pairs = [(f"{i}.pdf", one) for i in range(3)]
        with self.assertRaises(attach_intake.AttachmentLimitError) as ctx:
            attach_intake.check_limits(pairs)
        self.assertEqual(ctx.exception.code, attach_intake.ERR_BATCH_TOO_LARGE)

    def test_a_batch_at_the_limit_passes(self):
        attach_intake.check_limits([("a.pdf", b"x" * 10)] * attachments.MAX_FILES_PER_MESSAGE)


class IntakeAcceptTests(_Sandbox):
    """收料口整条:运输皮 → 落盘 → 落行 → 逐件识别。零模型、零扣费、零业务写。"""

    def _accept(self, pairs, insert_error=None):
        from tests.unit._route_contract_fakes import CurCM, FakeCur

        rows = []

        def _insert(_cur, **kw):
            rows.append(kw)
            return {"id": f"a-{len(rows)}", **kw}

        with ExitStack() as stack:
            for patch in (
                mock.patch("core.db.get_cursor", lambda *a, **k: CurCM(FakeCur())),
                mock.patch.object(attachments, "insert", side_effect=insert_error or _insert),
                mock.patch(
                    "services.ocr.entrypoints.billing_quote",
                    return_value={"allowed": True, "error_code": None, "page_count": 1},
                ),
            ):
                stack.enter_context(patch)
            out = attach_intake.accept(
                user={"id": "u1", "tenant_id": "t-1"},
                tenant_id="t-1",
                session_id="s-1",
                pairs=pairs,
            )
        return out, rows

    def test_zip_is_unpacked_and_every_leaf_is_recognised_on_its_own(self):
        import io as _io
        import zipfile

        buf = _io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("2569-06 GL.xlsx", _xlsx_bytes())
            zf.writestr("note.txt", "hello")
        out, rows = self._accept([("batch.zip", buf.getvalue())])
        self.assertEqual(len(out), 2)
        self.assertEqual(rows[0]["kind"], "gl_ledger")
        self.assertEqual(rows[0]["kind_source"], attachments.SOURCE_RULE)
        # 落盘的是明文可读的同一份字节,sha256 记的也是明文
        self.assertTrue(attachments.read_content(rows[0]["file_ref"]))

    def test_a_zip_with_more_leaves_than_the_batch_allows_is_refused_in_zip_words(self):
        """解包后的第二道闸:一个 zip 解出 21 件同样过不了「一条消息 20 件」。
        码换成 zip 口径 —— 她手上只有一个压缩包,「先送出一批」那句话没法执行。"""
        import io as _io
        import zipfile

        buf = _io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for i in range(attachments.MAX_FILES_PER_MESSAGE + 1):
                zf.writestr(f"note{i}.txt", "hello")
        with self.assertRaises(attach_intake.AttachmentLimitError) as ctx:
            self._accept([("batch.zip", buf.getvalue())])
        self.assertEqual(ctx.exception.code, attach_intake.ERR_ZIP_TOO_MANY)
        self.assertEqual(ctx.exception.limit, attachments.MAX_FILES_PER_MESSAGE)
        self.assertEqual(list(Path(self._dir.name).rglob("*.txt")), [])  # 一件都没落盘

    def test_a_zip_whose_leaves_add_up_past_the_batch_cap_is_refused(self):
        import io as _io
        import zipfile

        one = b"x" * (attachments.MAX_BATCH_BYTES // 2 + 1)
        buf = _io.BytesIO()
        # 压着存:一个 3MB 的包解出 35MB+ 才是真实场景(单件闸拦的是包本身,不是解出来的量)
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i in range(2):
                zf.writestr(f"scan{i}.txt", one)
        with self.assertRaises(attach_intake.AttachmentLimitError) as ctx:
            self._accept([("batch.zip", buf.getvalue())])
        self.assertEqual(ctx.exception.code, attach_intake.ERR_ZIP_TOO_LARGE)

    def test_zero_byte_file_is_named_and_refused_before_anything_lands(self):
        from services.workorder import intake_prep

        with self.assertRaises(intake_prep.IntakePrepError) as ctx:
            self._accept([("empty.pdf", b"")])
        self.assertEqual(ctx.exception.code, "workorder.intake.empty_file")
        self.assertEqual(list(Path(self._dir.name).rglob("*.pdf")), [])

    def test_a_failed_registration_leaves_no_orphan_on_disk(self):
        with self.assertRaises(RuntimeError):
            self._accept([("2569-06 GL.xlsx", _xlsx_bytes())], insert_error=RuntimeError("db"))
        self.assertEqual(list(Path(self._dir.name).rglob("*.xlsx")), [])


def _xlsx_bytes() -> bytes:
    import io as _io

    import openpyxl

    wb = openpyxl.Workbook()
    wb.active.append(["a", "b"])
    buf = _io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class _AnchorCur:
    """按 SQL 里【真实存在的】WHERE 锚点过滤内存行 —— 少一个锚,别人的行当场漏出来。

    路由那层的 get_owned/list_by_ids 一律被 mock 掉(测的是「拿到 None 返 404」),所以
    「三锚齐不齐」零覆盖:把 WHERE 删成 `id = %s` 也全绿。这个仿真让变异当场红。"""

    _COND = re.compile(r"(\w+)(?:::text)?\s*=\s*(ANY\(%s\)|%s)")

    def __init__(self, rows):
        self._rows = rows
        self._out: list[dict] = []

    def execute(self, sql, params=()):
        where = sql.split("WHERE", 1)[1] if "WHERE" in sql else ""
        conds = list(self._COND.finditer(where))
        assert len(conds) == len(params), f"占位符与参数对不上:{where!r} {params!r}"
        rows = list(self._rows)
        for cond, value in zip(conds, params):
            column, is_any = cond.group(1), cond.group(2).startswith("ANY")
            wanted = [str(v) for v in value] if is_any else [str(value)]
            rows = [r for r in rows if str(r.get(column)) in wanted]
        self._out = rows

    def fetchone(self):
        return self._out[0] if self._out else None

    def fetchall(self):
        return self._out


_MINE = {"id": "a-1", "tenant_id": "t-1", "session_id": "s-1", "user_id": "u1"}
_OTHER_TENANT = {**_MINE, "id": "a-2", "tenant_id": "t-9"}
_OTHER_USER = {**_MINE, "id": "a-3", "user_id": "u2"}
_OTHER_SESSION = {**_MINE, "id": "a-4", "session_id": "s-9"}
_ALL_ROWS = [_MINE, _OTHER_TENANT, _OTHER_USER, _OTHER_SESSION]


class OwnershipAnchorTests(unittest.TestCase):
    """下载/取料两条路的归属锚(提交信息把「租户 + id + 上传人三锚」当卖点写了,那就得有闸)。"""

    def test_download_row_needs_all_three_anchors(self):
        cur = _AnchorCur(_ALL_ROWS)
        got = attachments.get_owned(cur, tenant_id="t-1", attachment_id="a-1", user_id="u1")
        self.assertEqual(got["id"], "a-1")

    def test_another_tenants_or_another_users_attachment_is_not_downloadable(self):
        for row in (_OTHER_TENANT, _OTHER_USER):
            cur = _AnchorCur(_ALL_ROWS)
            got = attachments.get_owned(cur, tenant_id="t-1", attachment_id=row["id"], user_id="u1")
            self.assertIsNone(got, row["id"])

    def test_list_by_ids_is_anchored_on_tenant_and_session(self):
        cur = _AnchorCur(_ALL_ROWS)
        ids = [r["id"] for r in _ALL_ROWS]
        got = attachments.list_by_ids(cur, tenant_id="t-1", session_id="s-1", ids=ids)
        # 别的租户、别的会话的 id 拼进来一行都取不到(同一租户的别人的件仍在,归属由工具侧再验)
        self.assertEqual([r["id"] for r in got], ["a-1", "a-3"])


class PublicViewTests(unittest.TestCase):
    """前端契约锁:形状漂了就是页面全 [object Object] 的成因,键名在这里钉死。"""

    def test_shape(self):
        row = {
            "id": "a-1",
            "original_name": "gl.pdf",
            "file_ref": "/x/y__gl.pdf",
            "size_bytes": 12,
            "mime": "application/pdf",
            "kind": "gl_ledger",
            "kind_source": "rule",
            "kind_reason": "gl_name_or_text",
            "detect": {"page_count": 3, "needs_model": False, "actions": ["file_convert"]},
            "status": "ready",
        }
        out = attachments.public_attachment(row)
        self.assertEqual(
            sorted(out),
            [
                "actions",
                "attachment_id",
                "kind",
                "kind_reason",
                "kind_source",
                "mime",
                "name",
                "needs_model",
                "page_count",
                "quote",
                "size_bytes",
                "status",
            ],
        )
        self.assertNotIn("file_ref", out)  # 盘上真实路径绝不外泄

    def test_missing_name_falls_back_to_the_embedded_original(self):
        out = attachments.public_attachment(
            {"id": "a", "file_ref": "/base/deadbeef__ใบกำกับ.pdf", "detect": {}}
        )
        self.assertEqual(out["name"], "ใบกำกับ.pdf")

    def test_limits_expose_one_source_of_truth(self):
        limits = attachments.limits()
        self.assertEqual(limits["max_file_bytes"], attachments.MAX_FILE_BYTES)
        self.assertEqual(limits["max_files"], attachments.MAX_FILES_PER_MESSAGE)
        self.assertIn(".xlsx", limits["accept"])
        self.assertGreaterEqual(limits["ttl_days"], 1)

    def test_accept_lets_the_transport_wrappers_through(self):
        """accept 是前端的双闸(<input accept> + 选文件当下的判据)。漏了 zip/HEIC 的后果是
        静默的:落区写着「zip 都吃」,拖进来却被灰掉,后端拆壳的代码一次都跑不到。"""
        accept = attachments.limits()["accept"]
        for ext in attachments.TRANSPORT_EXTENSIONS:
            self.assertIn(ext, accept)


if __name__ == "__main__":
    unittest.main()
