# -*- coding: utf-8 -*-
"""DMS 订车单挂附件(attach_booking_files)。

契约来源:_dms_probe/fupload_probe/CONTRACT.md(测试站真传真删验证)。
要点:上传 = POST drfcbc/edit.php 提交完整编辑表单 FormData;HTTP 200 空白=成功,
err:: 开头=失败;回读校验(HTTP 200 不算数)。
"""

import unittest

from services.erp.mrerp_dms_client_base import DMSClientError
from services.erp.mrerp_dms_client_ops import DMSClientOpsMixin
from services.erp.mrerp_dms_client_forms import DMSClientFormsMixin

_EDIT_FORM = """
<form>
<input type="hidden" name="stsel" value="e">
<input type="hidden" name="idsel" value="5">
<input type="text" name="txtdocno" value="BK0002502000001">
<input type="text" name="txtcus" value="นาย ก">
<textarea name="fulcurrname[1]" maxlength="150">สำเนาบัตรประชาชน</textarea>
</form>
"""


def _verify_html(*names):
    """回读 HTML = 编辑表单 + 新增附件的 fulcurrname 区,可带超限显示名。"""
    rows = "".join(
        f'<textarea name="fulcurrname[{i}]" maxlength="150">{n}</textarea>'
        for i, n in enumerate(names, start=2)
    )
    return _EDIT_FORM.replace("</form>", rows + "</form>")


class _Resp:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text


class _FakeTransport:
    """form.php 第一次回编辑表单、之后回回读 HTML;edit.php 按队列回响应。"""

    def __init__(self, form_html=_EDIT_FORM, verify_html=None, edit_responses=None):
        self.form_html = form_html
        self.verify_html = verify_html if verify_html is not None else form_html
        self.edit_responses = list(edit_responses or [])
        self.posts = []
        self.form_calls = 0

    def post(self, url, data=None, files=None, timeout_ms=None):
        self.posts.append({"url": url, "data": data, "files": files, "timeout_ms": timeout_ms})
        if url.endswith("/form.php"):
            self.form_calls += 1
            return _Resp(200, self.verify_html if self.form_calls > 1 else self.form_html)
        if url.endswith("/edit.php"):
            return self.edit_responses.pop(0) if self.edit_responses else _Resp(200, " ")
        return _Resp(200, "ok")


class _FakeClient(DMSClientOpsMixin, DMSClientFormsMixin):
    def __init__(self, transport):
        self.transport = transport

    def _url(self, p):
        return "http://dms.test/" + p

    def _post_text(self, path, data=None):
        return self.transport.post(self._url(path), data=data).text


_FILE_A = {
    "display_name": "ใบขับขี่",
    "filename": "lic-a.jpg",
    "content_type": "image/jpeg",
    "content": b"\xff\xd8jpeg-a",
}
_FILE_B = {
    "display_name": "สำเนาบัตรประชาชนหน้า",
    "filename": "id-b.jpg",
    "content_type": "image/jpeg",
    "content": b"\xff\xd8jpeg-b",
}


class TestAttachBookingFiles(unittest.TestCase):
    def test_single_file_success(self):
        tr = _FakeTransport(
            verify_html=_verify_html(_FILE_A["display_name"]),
            edit_responses=[_Resp(200, " ")],
        )
        cl = _FakeClient(tr)
        res = cl.attach_booking_files(booking_id="5", files=[_FILE_A])

        self.assertTrue(res["ok"])
        self.assertEqual(res["attached"], 1)
        self.assertEqual(res["failed"], [])
        self.assertEqual(tr.form_calls, 2)  # 编辑表单 + 回读

        edit = tr.posts[1]
        self.assertTrue(edit["url"].endswith("/edit.php"))
        # 完整编辑表单现值 + 新文件名,不是独立小接口
        self.assertEqual(edit["data"]["stsel"], "e")
        self.assertEqual(edit["data"]["idsel"], "5")
        self.assertEqual(edit["data"]["txtdocno"], "BK0002502000001")
        self.assertEqual(edit["data"]["txtcus"], "นาย ก")
        self.assertEqual(edit["data"]["fulcurrname[1]"], "สำเนาบัตรประชาชน")
        self.assertEqual(edit["data"]["fulnewname[]"], "ใบขับขี่")
        self.assertEqual(
            edit["files"]["fulnew[]"],
            (_FILE_A["filename"], _FILE_A["content"], _FILE_A["content_type"]),
        )
        self.assertEqual(edit["timeout_ms"], 120000)

    def test_two_files_independent_posts_first_fails(self):
        tr = _FakeTransport(
            verify_html=_verify_html(_FILE_B["display_name"]),
            edit_responses=[_Resp(200, "err::disk full"), _Resp(200, " ")],
        )
        cl = _FakeClient(tr)
        res = cl.attach_booking_files(booking_id="5", files=[_FILE_A, _FILE_B])

        self.assertFalse(res["ok"])
        self.assertEqual(res["attached"], 1)
        self.assertEqual(len(res["failed"]), 1)
        self.assertEqual(res["failed"][0]["display_name"], "ใบขับขี่")
        self.assertIn("err::disk full", res["failed"][0]["error"])
        # 两件 = 两轮独立 edit.php POST
        edit_urls = [p["url"] for p in tr.posts if p["url"].endswith("/edit.php")]
        self.assertEqual(len(edit_urls), 2)

    def test_readback_missing_display_name_is_failure(self):
        # edit.php 全判绿,但回读 HTML 里没有该显示名 → 不算数
        tr = _FakeTransport(edit_responses=[_Resp(200, " ")])
        cl = _FakeClient(tr)
        res = cl.attach_booking_files(booking_id="5", files=[_FILE_A])

        self.assertFalse(res["ok"])
        self.assertEqual(res["attached"], 0)
        self.assertEqual(len(res["failed"]), 1)
        self.assertIn("readback", res["failed"][0]["error"])

    def test_idsel_mismatch_raises(self):
        tr = _FakeTransport(
            form_html=_EDIT_FORM.replace('value="5"', 'value="9"'),
            edit_responses=[_Resp(200, " ")],
        )
        cl = _FakeClient(tr)
        with self.assertRaises(DMSClientError) as ctx:
            cl.attach_booking_files(booking_id="5", files=[_FILE_A])
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_IMPORT")

    def test_display_name_truncated_to_150(self):
        long_name = "泰" * 200
        truncated = "泰" * 150
        tr = _FakeTransport(
            verify_html=_verify_html(truncated),
            edit_responses=[_Resp(200, " ")],
        )
        cl = _FakeClient(tr)
        res = cl.attach_booking_files(
            booking_id="5", files=[{**_FILE_A, "display_name": long_name}]
        )

        self.assertTrue(res["ok"])
        self.assertEqual(res["attached"], 1)
        edit = tr.posts[1]
        self.assertEqual(edit["data"]["fulnewname[]"], truncated)
        self.assertEqual(len(edit["data"]["fulnewname[]"]), 150)

    def test_readback_docno_changed_is_failure(self):
        # 回读时 txtdocno 变了 = 附件动作冲坏了单据 → 判失败
        verify = _verify_html(_FILE_A["display_name"]).replace("BK0002502000001", "BK0002502000999")
        tr = _FakeTransport(verify_html=verify, edit_responses=[_Resp(200, " ")])
        cl = _FakeClient(tr)
        res = cl.attach_booking_files(booking_id="5", files=[_FILE_A])

        self.assertFalse(res["ok"])
        self.assertEqual(res["attached"], 0)
        self.assertEqual(len(res["failed"]), 1)
        self.assertIn("docno", res["failed"][0]["error"])

    def test_empty_files_ok(self):
        cl = _FakeClient(_FakeTransport())
        res = cl.attach_booking_files(booking_id="5", files=[])
        self.assertTrue(res["ok"])
        self.assertEqual(res["attached"], 0)
        self.assertEqual(res["failed"], [])
        self.assertEqual(cl.transport.form_calls, 0)  # 空列表不碰网络


if __name__ == "__main__":
    unittest.main()
