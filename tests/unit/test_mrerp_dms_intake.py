# -*- coding: utf-8 -*-
"""DMSClientIntakeMixin 契约单测(假 transport · 不连真 DMS)。

锁:lookup_customer / save_customer(create+overwrite·空 select 兜底)/ list_geo /
list_prefixes 的表单字段映射与提交端点(new.php / edit.php)。
"""

import unittest
from unittest import mock

from services.erp.mrerp_dms_client import DMSClient
from services.erp.mrerp_dms_client_base import DMSClientError


class _Resp:
    def __init__(self, text="", status=200):
        self.status_code = status
        self.text = text
        self.content = text.encode()


_NEW_FORM = """
<form id="frm">
  <input type="hidden" name="stsel" value="n">
  <input type="hidden" name="idsel" value="">
  <input name="txtcuscode" value="">
  <select name="selprefix"><option value="">--</option><option value="17">นาย</option></select>
  <input name="txtcusname" value="">
  <input name="txtpeopleid" value="">
  <input name="txttaxid" value="">
  <input name="txttel" value="">
  <input name="txthousenum" value=""><input name="txthousenum_ct" value=""><input name="txthousenum_sd" value="">
  <select name="selprovinces"><option value="65" selected>กระบี่</option></select>
  <select name="seldistricts"><option value="804" selected>คลองท่อม</option></select>
  <select name="selsubdistricts"><option value="6472" selected>คลองท่อมเหนือ</option></select>
  <select name="selzipcodes"><option value="">--</option></select>
  <select name="selprovinces_ct"><option value="65" selected>กระบี่</option></select>
  <select name="seldistricts_ct"><option value="804" selected>x</option></select>
  <select name="selsubdistricts_ct"><option value="6472" selected>x</option></select>
  <select name="selzipcodes_ct"><option value="">--</option></select>
  <select name="selprovinces_sd"><option value="65" selected>กระบี่</option></select>
  <select name="seldistricts_sd"><option value="804" selected>x</option></select>
  <select name="selsubdistricts_sd"><option value="6472" selected>x</option></select>
  <select name="selzipcodes_sd"><option value="">--</option></select>
</form>
"""


def _edit_form(name="Old Name", tel="0811111111"):
    return (
        _NEW_FORM.replace('name="txtcusname" value=""', f'name="txtcusname" value="{name}"')
        .replace('name="txttel" value=""', f'name="txttel" value="{tel}"')
        .replace(
            'name="selzipcodes"><option value="">--</option>',
            'name="selzipcodes"><option value="6477" selected>81120</option>',
        )
    )


class FakeTransport:
    def __init__(self):
        self.posts = []
        self.search_hits = ["95"]
        self._created = False  # new.php 后变 True · 模拟"建后能搜到"

    def get(self, url, timeout_ms=None):
        return _Resp("")

    def post(self, url, data=None, files=None, timeout_ms=None):
        self.posts.append((url, dict(data or {})))
        if url.endswith("cus/form.php"):
            if (data or {}).get("status") == "e":
                return _Resp(_edit_form(name=self._edit_name))
            return _Resp(_NEW_FORM)
        if url.endswith("cus/new.php"):
            self._created = True
            return _Resp("")
        if url.endswith("cus/component/showdata.php"):
            hit = bool(self.search_hits) or self._created
            return _Resp('<a data-val="95">row</a>' if hit else "")
        if url.endswith("cus/component/listzipcodes.php"):
            return _Resp('<option value="6477">81120</option>')
        if url.endswith("listdistricts.php"):
            return _Resp('<option value="804">คลองท่อม</option>')
        if url.endswith("listsubdistricts.php"):
            return _Resp('<option value="6472">คลองท่อมเหนือ</option>')
        if url.endswith("cus/new.php") or url.endswith("cus/edit.php"):
            return _Resp("")  # no err:: → success
        return _Resp("")

    _edit_name = "Old Name"


class _DupCodeTransport(FakeTransport):
    """建档撞唯一键场景:幂等预查与复搜前几次都空返,new.php 恒报 ซ้ำ。
    research_hit_at=第几次 showdata 搜索起命中(默认第 3 次=复搜第 2 试)。"""

    def __init__(self, research_hit_at: int = 3):
        super().__init__()
        self.search_hits = []
        self._hit_at = research_hit_at
        self._searches = 0

    def post(self, url, data=None, files=None, timeout_ms=None):
        if url.endswith("cus/component/showdata.php"):
            self.posts.append((url, dict(data or {})))
            self._searches += 1
            return _Resp('<a data-val="95">row</a>' if self._searches >= self._hit_at else "")
        if url.endswith("cus/new.php"):
            self.posts.append((url, dict(data or {})))
            return _Resp('err::"รหัสลูกค้า" ซ้ำ')
        return super().post(url, data=data, files=files, timeout_ms=timeout_ms)


class IntakeContractTests(unittest.TestCase):
    def setUp(self):
        self.t = FakeTransport()
        self.c = DMSClient(self.t, "https://x/dms/")

    def test_list_prefixes_and_geo(self):
        self.assertEqual(self.c.list_prefixes(), [["17", "นาย"]])
        self.assertEqual(self.c.list_geo("provinces"), [["65", "กระบี่"]])
        self.assertEqual(self.c.list_geo("districts", "65"), [["804", "คลองท่อม"]])
        self.assertEqual(self.c.list_geo("zipcodes", "6472"), [["6477", "81120"]])

    def test_lookup_found(self):
        self.t._edit_name = "Somchai Jaidee"
        out = self.c.lookup_customer("1234567890123")
        self.assertTrue(out["found"])
        self.assertEqual(out["customer_id"], "95")
        self.assertEqual(out["fields"]["name"], "Somchai Jaidee")

    def test_lookup_not_found(self):
        self.t.search_hits = []
        out = self.c.lookup_customer("0000000000000")
        self.assertFalse(out["found"])
        self.assertIsNone(out["customer_id"])

    def test_save_create_posts_new_php_and_maps_fields(self):
        self.t.search_hits = []  # 不存在 → 真新建走 cus/new.php
        fields = {
            "prefix_id": "17",
            "name": "New Cust",
            "people_id": "1234567890123",
            "birthday_be": "01/01/2530",
            "phone": "0899999999",
            "province_id": "65",
            "district_id": "804",
            "subdistrict_id": "6472",
            "zipcode_id": "6477",
        }
        cid = self.c.save_customer(fields=fields, mode="create")
        self.assertEqual(cid, "95")  # search verify
        save = [p for p in self.t.posts if p[0].endswith("cus/new.php")][0][1]
        self.assertEqual(save["txtcusname"], "New Cust")
        self.assertEqual(save["txtpeopleid"], "1234567890123")
        self.assertEqual(save["txttaxid"], "1234567890123")  # 个人税号回落身份证号
        self.assertEqual(save["stsel"], "n")
        self.assertEqual(save["selprovinces"], "65")

    def test_save_overwrite_posts_edit_php_with_idsel(self):
        self.t._edit_name = "New Cust"  # 重读核对用
        fields = {
            "name": "New Cust",
            "people_id": "1234567890123",
            "province_id": "65",
            "district_id": "804",
            "subdistrict_id": "6472",
            "zipcode_id": "6477",
        }
        cid = self.c.save_customer(fields=fields, mode="overwrite", customer_id="95")
        self.assertEqual(cid, "95")
        save = [p for p in self.t.posts if p[0].endswith("cus/edit.php")][0][1]
        self.assertEqual(save["stsel"], "e")
        self.assertEqual(save["idsel"], "95")

    def test_save_create_idempotent_to_overwrite_when_exists(self):
        """create 前先查身份证号 · 已存在则转 overwrite 更新它(防撞客户编号重复)。"""
        self.t._edit_name = "Dup Person"  # 重读核对
        fields = {
            "name": "Dup Person",
            "people_id": "1234567890123",
            "province_id": "65",
            "district_id": "804",
            "subdistrict_id": "6472",
            "zipcode_id": "6477",
        }
        cid = self.c.save_customer(fields=fields, mode="create")  # 默认 search_hits=['95']
        self.assertEqual(cid, "95")
        self.assertTrue(self.c._create_converted)
        self.assertTrue([p for p in self.t.posts if p[0].endswith("cus/edit.php")], "应转 edit.php")
        self.assertFalse([p for p in self.t.posts if p[0].endswith("cus/new.php")], "不应建新")

    def test_create_duplicate_code_self_heals_to_overwrite(self):
        """撞「รหัสลูกค้า ซ้ำ」= 搜索漏检但记录其实已在(2026-07-19 演示实锤:建档后
        3 分钟同号搜不到 → 重复建档被拒)→ 复搜(带重试)命中即转覆盖,不报错给用户。"""
        t = _DupCodeTransport()
        t._edit_name = "Heal Person"
        c = DMSClient(t, "https://x/dms/")
        fields = {
            "name": "Heal Person",
            "people_id": "1234567890123",
            "province_id": "65",
            "district_id": "804",
            "subdistrict_id": "6472",
            "zipcode_id": "6477",
        }
        with mock.patch("services.erp.mrerp_dms_client_intake.time.sleep") as slept:
            cid = c.save_customer(fields=fields, mode="create")
        self.assertEqual(cid, "95")
        self.assertTrue([p for p in t.posts if p[0].endswith("cus/edit.php")], "应转 edit.php 覆盖")
        self.assertTrue(slept.called)  # 复搜带退避,真跑时给搜索端点喘息窗口
        self.assertTrue(c._create_converted)  # 回执侧据此如实说「อัปเดต」不谎称新建

    def test_create_duplicate_code_research_still_missing_raises(self):
        """复搜三次仍空 → 如实抛 ERR_DMS_CUSTOMER_SAVE(不吞错不假成功)。"""
        t = _DupCodeTransport(research_hit_at=99)
        c = DMSClient(t, "https://x/dms/")
        fields = {
            "name": "X",
            "people_id": "1234567890123",
            "province_id": "65",
            "district_id": "804",
            "subdistrict_id": "6472",
            "zipcode_id": "6477",
        }
        with mock.patch("services.erp.mrerp_dms_client_intake.time.sleep"):
            with self.assertRaises(DMSClientError):
                c.save_customer(fields=fields, mode="create")

    def test_save_fills_empty_prefix_and_zipcode(self):
        """空 selprefix/selzipcodes 触发 DMS 误导性 'already in use' → 提交前兜底补全。"""
        self.t.search_hits = []  # 真新建路径
        fields = {
            "name": "X",
            "people_id": "1234567890123",
            "province_id": "65",
            "district_id": "804",
            "subdistrict_id": "6472",
        }
        self.c.save_customer(fields=fields, mode="create")
        save = [p for p in self.t.posts if p[0].endswith("cus/new.php")][0][1]
        self.assertTrue(save["selprefix"])  # 不为空
        self.assertTrue(save["selzipcodes"])  # 从 subdistrict 兜底取到

    def test_save_overwrite_requires_customer_id(self):
        with self.assertRaises(DMSClientError):
            self.c.save_customer(fields={"name": "x"}, mode="overwrite", customer_id=None)


_SHOWDATA = (
    'dt::<div data-val="59" data-allo="" data-cf="" onclick="ctllistdata(this);">'
    '<div class="detaildata">'
    "<div><p>0000ทดสอบ</p><p>ลูกค้า ทดสอบ ราย 1</p></div>"
    "<div><p>1234567890123</p></div>"
    '</div><div class="statuscf"><p><span>ผู้จัดทำ</span></p></div></div>'
    '<div data-val="67" data-allo="" data-cf="" onclick="ctllistdata(this);">'
    '<div class="detaildata">'
    '<div><p class="colnodt">-</p><p>ทดสอบ เพียร์ลี่</p></div>'
    '<div><p class="colnodt">-</p></div>'
    '</div><div class="statuscf"><p><span>ผู้จัดทำ</span></p></div></div>'
)


class CustomerRowParseTests(unittest.TestCase):
    def setUp(self):
        self.c = DMSClient(FakeTransport(), "https://x/dms/")

    def test_parse_rows_columns_and_placeholder(self):
        rows = self.c._parse_customer_rows(_SHOWDATA)
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            rows[0],
            {
                "customer_id": "59",
                "cuscode": "0000ทดสอบ",
                "name": "ลูกค้า ทดสอบ ราย 1",
                "people_id": "1234567890123",
            },
        )
        # "-"/colnodt 占位归一为空
        self.assertEqual(rows[1]["customer_id"], "67")
        self.assertEqual(rows[1]["cuscode"], "")
        self.assertEqual(rows[1]["name"], "ทดสอบ เพียร์ลี่")
        self.assertEqual(rows[1]["people_id"], "")

    def test_parse_empty_body(self):
        self.assertEqual(self.c._parse_customer_rows("ndt::"), [])


class ScoreCandidatesTests(unittest.TestCase):
    def test_closer_name_ranks_first_and_exact_id_scores_100(self):
        from services.erp.erp_dms_intake import _score_candidates

        # 相似分支里身份证号通常都不同(完全一致会走 exact 路径)→ 姓名相似度主导排序
        rows = [
            {"customer_id": "1", "name": "อื่น คนละคน", "people_id": "9999999999999"},
            {"customer_id": "2", "name": "สมชาย ใจดี", "people_id": "1234567890124"},
        ]
        out = _score_candidates(rows, people_id="1234567890123", name="สมชาย ใจดี")
        self.assertEqual(out[0]["customer_id"], "2")
        self.assertGreater(out[0]["score"], out[1]["score"])

        # 边界:若候选身份证号恰好完全一致 → 100
        exact = _score_candidates(
            [{"customer_id": "9", "name": "x", "people_id": "1234567890123"}],
            people_id="1234567890123",
            name="สมชาย ใจดี",
        )
        self.assertEqual(exact[0]["score"], 100)


class SaveSemanticTests(unittest.TestCase):
    def setUp(self):
        self.t = FakeTransport()
        self.c = DMSClient(self.t, "https://x/dms/")

    def _posted(self, endpoint):
        return [p for p in self.t.posts if p[0].endswith(endpoint)][0][1]

    def test_present_empty_clears_absent_keeps(self):
        """所见即所存:键【存在】=空串 → 真清空(手动清除生效);键【缺省】→ 保留 DMS 原值。"""
        # phone 显式传空串(用户手动清空)→ 清空 DMS txttel
        self.t._edit_name = "Keep Name"
        self.c.save_customer(
            fields={"name": "Keep Name", "people_id": "1234567890123", "phone": ""},
            mode="overwrite",
            customer_id="95",
        )
        self.assertEqual(self._posted("cus/edit.php")["txttel"], "")
        # phone 键不传(用户没动)→ 保留 DMS 现有 txttel
        self.t.posts.clear()
        self.c.save_customer(
            fields={"name": "Keep Name", "people_id": "1234567890123"},
            mode="overwrite",
            customer_id="95",
        )
        self.assertEqual(self._posted("cus/edit.php")["txttel"], "0811111111")

    def test_three_address_blocks_written_separately(self):
        self.t._edit_name = "Addr Cust"
        self.c.save_customer(
            fields={"name": "Addr Cust", "people_id": "1234567890123"},
            mode="overwrite",
            customer_id="95",
            addresses={
                "": {"house_no": "1"},
                "_ct": {"house_no": "2"},
                "_sd": {"house_no": "3"},
            },
        )
        save = self._posted("cus/edit.php")
        self.assertEqual(save["txthousenum"], "1")
        self.assertEqual(save["txthousenum_ct"], "2")
        self.assertEqual(save["txthousenum_sd"], "3")


if __name__ == "__main__":
    unittest.main()
