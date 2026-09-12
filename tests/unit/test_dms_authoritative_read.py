# -*- coding: utf-8 -*-
"""销售视图 vs 管理员权威视图的行为契约(读借管理员 · 写留销售)。

覆盖:
  1. 销售主档不全/被裁空 → 开局主档快照与颜色仍拿到管理员完整结果;
  2. 销售搜不到/直读不到客户,管理员按身份证或客户号看得到 → 正确匹配;
  3. 未配独立管理员 → 照旧用销售会话;
  4. 配了管理员但管理员认证/读取失败 → 明确失败关闭(不静默降级,也不拿旧缓存冒充);
  5. 订车写只落销售 transport 且最多一次(管理员看得见的 ID 被 DMS 拒时如实报错,不重写);
  6. 同一份快照/预检不按字段重复解析管理员会话。
零网络:全部假 transport / 假 adapter,不碰真实 DMS。
"""

import contextlib
import dataclasses
import json
import os
import unittest
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-for-dms-authoritative-32bytes")

from services.erp import dms_masters_cache as mc  # noqa: E402
from services.erp import erp_dms_intake  # noqa: E402
from services.erp.mrerp_dms_adapter import MrerpDmsAdminAuthError  # noqa: E402
from services.erp.mrerp_dms_client import DMSClient  # noqa: E402
from services.erp.mrerp_dms_client_base import DMSClientError  # noqa: E402
from services.line_dms import booking_flow as bf  # noqa: E402

_EP = {"id": "E1", "config": {"admin_username": "dmsadmin", "admin_password": "pw"}}
_EP_SALES_ONLY = {"id": "E1", "config": {}}
# booking 走真 _run_logged_in(适配器已打桩),但端点配置仍要像生产那样带销售主凭据。
_EP_BOOKING = {
    "id": "E1",
    "config": {
        "username": "sale02",
        "password": "pw",
        "admin_username": "dmsadmin",
        "admin_password": "pw",
    },
}
_BASE = "https://x/dms/"
_CARS = [["c1", "DMX", "D-Max"]]
# 顾问行第 4 列是电话(txtuserstel):建单表单缺它会被判 ERR_DMS_ADVISOR_UNMATCHED。
_ADVISORS = [["335", "sale02", "sale02", "0811111111"]]
_PAINTS = [["p1", "WHITE", "ขาว"]]
_BANKS = [["1", "SCB", "SCB", "ระยอง", "1234567890123"]]


class _Resp:
    def __init__(self, text="", status=200):
        self.status_code = status
        self.text = text
        self.content = str(text).encode()


def _bshsd_body(rows):
    """bshsd.php 的响应体就是 JSON 数组(见 mrerp_dms_master_rows.parse_rows)。"""
    return json.dumps([list(r) for r in rows])


def _master_posts(rows_by_elem=None):
    """bshsd 取数:按登记的 elemname 回行列,未登记回空表(模拟被裁空的销售视图)。"""
    rows_by_elem = rows_by_elem or {}

    def _post(url, data):
        if "bshsd" in url:
            elem = (data or {}).get("elemname") or ""
            return _Resp(_bshsd_body(rows_by_elem.get(elem, [])))
        return _Resp("")

    return _post


def _full_masters(**over):
    masters = {
        "cars": [list(r) for r in _CARS],
        "advisors": [list(r) for r in _ADVISORS],
        "place_books": [["pl1", "PL", "สาขาบางนา"]],
        "term_sales": [["t1", "T", "เงินสด"]],
        "regis_behalfs": [["r1", "R", "บริษัท"]],
        "company_banks": [list(r) for r in _BANKS],
        "source_banks": [list(r) for r in _BANKS],
        "cheque_banks": [list(r) for r in _BANKS],
        "cashier_banks": [list(r) for r in _BANKS],
        "card_banks": [list(r) for r in _BANKS],
    }
    masters.update(over)
    return masters


class _Transport:
    """假 transport:记录调用,按 URL/data 造响应;deny=True 模拟销售账号权限不足。"""

    def __init__(self, name, posts=None, deny=False):
        self.name = name
        self.calls = []
        self.deny = deny
        self._posts = posts or (lambda url, data: _Resp(""))
        # 观察钩子:每次请求发生时读一次调用方 client 当前挂在哪个 transport(读写边界取证)。
        self.observer = None

    def get(self, url, timeout_ms=None):
        self.calls.append(("GET", url, None))
        if self.observer:
            self.observer("GET", url)
        return _Resp("")

    def post(self, url, data=None, files=None, timeout_ms=None):
        self.calls.append(("POST", url, dict(data or {})))
        if self.observer:
            self.observer("POST", url)
        if self.deny:
            return _Resp("forbidden", 403)
        return self._posts(url, data or {})

    def paths(self):
        return [url for _m, url, _d in self.calls]

    def paths_matching(self, needle):
        return [url for url in self.paths() if needle in url]

    def bshsd_elems(self):
        return [d.get("elemname") for _m, url, d in self.calls if url.endswith("bshsd.php")]


class _AdminFactory:
    """管理员 transport 工厂(计数 = 一次管理员登录/会话解析)。"""

    def __init__(self, transport=None, error=None):
        self.calls = 0
        self._transport = transport
        self._error = error

    def __call__(self):
        self.calls += 1
        if self._error:
            raise self._error
        return self._transport


class _Adapter:
    """假适配器:_client() 每次构造 DMSClient,凭据组与生产同源(admin=None 即未配)。

    同时实现 with/login 与并发登录判据 —— 这样测试走的是真 _run_logged_in(连
    authoritative_read=True 的接线一起验),而不是把 runner 打桩掉。"""

    def __init__(self, sales, admin=None, admin_factory=None):
        self.sales = sales
        self._admin = admin
        self.admin_factory = admin_factory
        self.concurrent_login_detected = False
        self.last_dialog = ""
        self._client_instance = None

    def _client(self):
        """每次 _client() 都回同一个 client(生产是每次新建,这里要让测试能盯住同一个实例:
        预检借管理员读、建单写回销售,都得发生在这一份 transport 状态上)。"""
        if self._client_instance is None:
            admin_transport = self.admin_factory if self.admin_factory is not None else self._admin
            self._client_instance = DMSClient(self.sales, _BASE, admin_transport=admin_transport)
        return self._client_instance

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def login(self):
        return None


@contextlib.contextmanager
def _runner(adapter):
    """保留真 _run_logged_in(含 authoritative_read 接线),只替掉适配器构造与绑定校验。"""
    with (
        mock.patch.object(
            erp_dms_intake,
            "_build_mrerp_dms_adapter",
            return_value=(adapter, None),
        ),
        mock.patch("services.line_dms.binding_guard.require_current", lambda: None),
    ):
        yield


class _Mem:
    def __init__(self):
        self.rows = {}

    def read(self, eid):
        row = self.rows.get(eid)
        return {"masters": row, "age_seconds": 0.0} if row is not None else None

    def write(self, eid, masters):
        self.rows[eid] = masters


class MasterSnapshotUsesAdminTests(unittest.TestCase):
    """1/3/4/6:主档与颜色读管理员；未配管理员用销售；认证失败 fail closed；不重复登录。"""

    def setUp(self):
        self.mem = _Mem()
        self.es = contextlib.ExitStack()
        self.es.enter_context(mock.patch.object(mc, "_read", side_effect=self.mem.read))
        self.es.enter_context(mock.patch.object(mc, "_write", side_effect=self.mem.write))
        self.addCleanup(self.es.close)

    def _patch_runner(self, adapter):
        self.es.enter_context(_runner(adapter))

    def test_roles_cut_sales_master_is_replaced_by_the_admin_snapshot(self):
        """销售主档被裁空(车型全无)→ 权威快照仍是管理员那份,且只解析一次管理员会话。"""
        sales = _Transport("sales", posts=_master_posts({}))
        admin = _Transport(
            "admin",
            posts=_master_posts(
                {
                    "txtcar": _CARS,
                    "txtusers": _ADVISORS,
                    "txtbanknametfmon": _BANKS,
                    "txtbanknametffrom": _BANKS,
                    "txtbanknamecheque": _BANKS,
                    "txtbanknamecashiercq": _BANKS,
                    "txtbanknamecddbc": _BANKS,
                }
            ),
        )
        factory = _AdminFactory(admin)
        self._patch_runner(_Adapter(sales, admin_factory=factory))

        masters = mc.get_masters(_EP, force_refresh=True, require_complete=True)

        self.assertEqual(masters["cars"], _CARS)
        self.assertEqual(masters["company_banks"][0][0], "1")
        self.assertEqual(factory.calls, 1)
        self.assertEqual(sales.calls, [])  # 权威快照一次都不碰销售会话

    def test_paints_fall_back_to_the_admin_session(self):
        """销售颜色表为空 → 颜色仍按管理员会话取到(空表会被误判成「这车没颜色」)。"""
        sales = _Transport("sales", posts=_master_posts({}))
        admin = _Transport("admin", posts=_master_posts({"txtcarpaint": _PAINTS}))
        factory = _AdminFactory(admin)
        self._patch_runner(_Adapter(sales, admin_factory=factory))

        self.assertEqual(mc.get_paints(_EP, "c1", force_refresh=True), _PAINTS)
        self.assertEqual(factory.calls, 1)
        self.assertEqual(sales.calls, [])

    def test_without_admin_credentials_reads_stay_on_the_sales_session(self):
        sales = _Transport("sales", posts=_master_posts({"txtcar": _CARS}))
        self._patch_runner(_Adapter(sales, admin=None))

        masters = mc.get_masters(_EP_SALES_ONLY, force_refresh=True, require_complete=True)

        self.assertEqual(masters["cars"], _CARS)
        self.assertTrue(any(p.endswith("bshsd.php") for p in sales.paths()))

    def test_configured_admin_auth_failure_fails_closed_instead_of_sales_or_stale(self):
        """配了管理员但管理员登录失败 → 空 dict:不拿销售视图顶,也不拿旧主档冒充。"""
        sales = _Transport("sales", posts=_master_posts({"txtcar": _CARS}))
        factory = _AdminFactory(error=MrerpDmsAdminAuthError("admin creds bounced"))
        self._patch_runner(_Adapter(sales, admin_factory=factory))
        self.mem.rows["E1"] = {"cars": [["old", "OLD", "Stale"]]}

        out = mc.get_masters(_EP, force_refresh=True, require_complete=True)

        self.assertEqual(out, {})
        self.assertEqual(sales.calls, [])
        # 非强制刷新的普通读也 fail closed:陈旧回退只对「未配管理员」的登录失败开放。
        self.mem.rows["E1"] = {"cars": [["old", "OLD", "Stale"]]}
        out2 = mc.get_masters(_EP, force_refresh=True)
        self.assertEqual(out2, {})

    def test_one_snapshot_block_resolves_the_admin_session_once(self):
        """一次权威主档快照 = 一次管理员会话:11 处 elemname 取数不按字段重复登录。"""
        elems = _admin_master_elems()
        admin = _Transport("admin", posts=_master_posts(elems))
        factory = _AdminFactory(admin)
        self._patch_runner(_Adapter(_Transport("sales", deny=True), admin_factory=factory))

        masters = mc.get_masters(_EP, force_refresh=True, require_complete=True)

        self.assertEqual(masters["cars"], _CARS)
        self.assertEqual(factory.calls, 1)  # 主档 11 处取数共用同一次管理员解析
        expected = set(elems) - {"txtcarpaint"}  # 快照阶段不读颜色(颜色按车型惰性读)
        self.assertEqual(sorted(set(admin.bshsd_elems())), sorted(expected))


class CustomerMatchUsesAdminTests(unittest.TestCase):
    """2:销售搜不到/读不到客户,管理员看得到 → 正确匹配(按身份证或客户号)。"""

    _PEOPLE_ID = "3319900165090"
    _CUSTOMER_ID = "95"

    def _detail(self, name="สมชาย ใจดี", people_id=None):
        return (
            f'<form><input name="txtcusname" value="{name}">'
            f'<input name="txtpeopleid" value="{people_id or self._PEOPLE_ID}">'
            '<select name="selprovinces"><option value="65" selected>กระบี่</option></select>'
            "</form>"
        )

    def _search_hit(self):
        return (
            f'<div data-val="{self._CUSTOMER_ID}" onclick="ctllistdata();">'
            '<div class="detaildata"><div><p>95</p><p>สมชาย ใจดี</p></div>'
            f"<div><p>{self._PEOPLE_ID}</p></div></div>"
            '<div class="statuscf"></div></div>'
        )

    def _lookup(self, adapter):
        with _runner(adapter):
            return erp_dms_intake.recognize_lookup_mrerp_dms(
                _EP,
                people_id=self._PEOPLE_ID,
                name="สมชาย ใจดี",
                ocr_address={"province": "กระบี่"},
            )

    def _admin_posts(self, url, data):
        if url.endswith("showdata.php"):
            return _Resp(self._search_hit())
        if url.endswith("cus/form.php"):
            return _Resp(self._detail())
        return _Resp("")

    def test_search_invisible_to_sales_is_matched_on_the_admin_session(self):
        sales = _Transport("sales", deny=True)
        factory = _AdminFactory(_Transport("admin", posts=self._admin_posts))

        out = self._lookup(_Adapter(sales, admin_factory=factory))

        self.assertTrue(out["ok"])
        self.assertEqual(out["scenario"], "exact")
        self.assertEqual(out["match"]["customer_id"], self._CUSTOMER_ID)
        self.assertEqual(factory.calls, 1)
        self.assertEqual(sales.calls, [])  # 销售看不到这个客户也不影响匹配

    def test_direct_customer_read_for_the_panel_uses_admin(self):
        """面板载入指定客户号全字段同属权威读(销售读不到 ≠ 这个客户没资料)。"""
        sales = _Transport("sales", deny=True)
        factory = _AdminFactory(
            _Transport(
                "admin",
                posts=lambda url, data: (
                    _Resp(self._detail() + "<form></form>")
                    if url.endswith("cus/form.php")
                    else _Resp("")
                ),
            )
        )
        adapter = _Adapter(sales, admin_factory=factory)

        with _runner(adapter):
            out = erp_dms_intake.customer_fields_mrerp_dms(_EP, customer_id=self._CUSTOMER_ID)

        self.assertTrue(out["ok"])
        self.assertEqual(out["current_fields"]["name"], "สมชาย ใจดี")
        self.assertEqual(factory.calls, 1)
        self.assertEqual(sales.calls, [])

    def test_without_admin_credentials_the_sales_view_is_used(self):
        """未配独立管理员 → 照旧销售读(逐字节兼容),不额外开管理员会话。"""

        def _sales_posts(url, data):
            if url.endswith("showdata.php"):
                return _Resp(self._search_hit())
            if url.endswith("cus/form.php"):
                return _Resp(self._detail())
            return _Resp("")

        sales = _Transport(
            "sales",
            posts=_sales_posts,
        )
        out = self._lookup(_Adapter(sales, admin=None))
        self.assertTrue(out["ok"])
        self.assertEqual(out["scenario"], "exact")
        self.assertEqual(out["match"]["customer_id"], self._CUSTOMER_ID)
        self.assertTrue(any(p.endswith("showdata.php") for p in sales.paths()))


# ── 订车提交链的假 DMS 服务端:主档(管理员工厂) + 建单/回读(销售) ────────────
_PEOPLE_ID = "3319900165090"
_CUSTOMER_ID = "95"

# 客户档直读表单:身份证/称谓/电话/户籍地址四级 ID 都要齐,否则建单卡被判资料不全。
_CUSTOMER_HTML = (
    "<form>"
    '<input name="txtcusname" value="สมชาย ใจดี">'
    f'<input name="txtpeopleid" value="{_PEOPLE_ID}">'
    '<input name="txtbirthday" value="01/01/2530">'
    '<select name="selprefix"><option value="17" selected>นาย</option></select>'
    '<input name="txttel" value="0812345678">'
    '<input name="txthousenum" value="123">'
    '<select name="selprovinces"><option value="65" selected>กระบี่</option></select>'
    '<select name="seldistricts"><option value="6501" selected>เมืองกระบี่</option></select>'
    '<select name="selsubdistricts"><option value="650101" selected>กระบี่ใหญ่</option></select>'
    '<select name="selzipcodes"><option value="81000" selected>81000</option></select>'
    "</form>"
)
# 顾问组织(detailbooksell 原生 12 列)与上面的地址级联子项。
_ORG_JSON = json.dumps(
    ["1", "Rayong", "30", "Sales team", "289", "Manager", None, None, None, None, None, None]
)
_GEO_CHILDREN = {
    "listdistricts.php": '<option value="6501">เมืองกระบี่</option>',
    "listsubdistricts.php": '<option value="650101">กระบี่ใหญ่</option>',
    "listzipcodes.php": '<option value="81000">81000</option>',
}

# 销售会话在订车链上允许出现的路径(创建单据所必需):建单表单/取号/提交/有限回读。
# bshsd.php(主档)、cus/form.php(客户档)、detailbooksell.php(顾问组织)都不在其中。
_SALES_ALLOWED_PATHS = (
    "drfcbc/form.php",
    "component/php/autonum.php",
    "component/php/autonumdetail.php",
    "drfcbc/component/showdata.php",
    "drfcbc/new.php",
    "drfcbc/view.php",
)


def _admin_booking_posts(elems):
    """管理员工厂服务端:全量主档 + 客户档直读 + 顾问组织 + 地址级联。"""
    masters = _master_posts(elems)

    def _post(url, data):
        if url.endswith("cus/form.php"):
            return _Resp(_CUSTOMER_HTML)
        if url.endswith("detailbooksell.php"):
            return _Resp(_ORG_JSON)
        for name, body in _GEO_CHILDREN.items():
            if url.endswith(name):
                return _Resp(body)
        return masters(url, data)

    return _post


class _BookingSite:
    """销售会话的假 DMS 服务端:取号 → new.php 建单一次 → 回读原样回显已存表单。"""

    BID = "BID100"
    DOCNO = "BK2606000001"

    def __init__(self):
        self.stored = {}
        self.reject = ""

    def posts(self, url, data):
        data = data or {}
        if url.endswith("component/php/autonum.php"):
            return _Resp(json.dumps(["7", "1", "BK2606", 6, self.DOCNO]))
        if url.endswith("component/php/autonumdetail.php"):
            return _Resp(json.dumps(["0", "0", self.DOCNO, "0"]))
        if url.endswith("drfcbc/new.php"):
            self.stored = dict(data)
            return _Resp(self.reject)
        if url.endswith("drfcbc/component/showdata.php"):
            if str(data.get("selcolsorttype")) == "2":
                return _Resp("dt::")  # 取号扫描:号段未被占用
            return _Resp(f'dt::<div data-val="{self.BID}"><div><p>{self.DOCNO}</p></div></div>')
        if url.endswith("drfcbc/form.php"):
            if data.get("status") == "e" and str(data.get("id")) == self.BID:
                return _Resp(self._candidate_form())
            return _Resp("")  # 新建表单(status=n):字段由调用方填
        return _Resp("")

    def _candidate_form(self):
        fields = {**self.stored, "idsel": self.BID}
        return (
            "<form>"
            + "".join(f'<input name="{key}" value="{value}">' for key, value in fields.items())
            + "</form>"
        )


class _Trace:
    """按请求发生时的 transport 记轨迹:证明读写落在哪条会话上,而不是看谁被调用。"""

    def __init__(self, sales, admin):
        self.sales, self.admin = sales, admin
        self.client = None
        self.entries = []  # [(transport, method, url)]

    def bind(self, client):
        self.client = client
        self.sales.observer = self._observe
        if self.admin is not None:
            self.admin.observer = self._observe

    def _observe(self, method, url):
        self.entries.append((self.label(getattr(self.client, "transport", None)), method, url))

    def label(self, transport):
        if transport is self.sales:
            return "sales"
        if self.admin is not None and transport is self.admin:
            return "admin(writer)"
        if self.admin is not None and getattr(transport, "_transport", None) is self.admin:
            return "admin(readonly)"
        return "unknown"

    def urls(self, label=None):
        return [url for where, _m, url in self.entries if label is None or where == label]

    def first_index(self, suffix, *, after=-1, label=None):
        for index, (where, _m, url) in enumerate(self.entries):
            if index <= after or not url.endswith(suffix):
                continue
            if label is not None and where != label:
                continue
            return index
        raise AssertionError(f"trace 里没有 {suffix!r}(label={label!r}, after={after})")


def _admin_master_elems(**over):
    """权威主档取数:与 fetch_masters + 5 类银行 + 颜色一致的 elemname 表。"""
    elems = {
        "txtcar": _CARS,
        "txtplacebook": [["pl1", "PL", "สาขาบางนา"]],
        "txttermsale": [["t1", "T", "เงินสด"]],
        "txtbranch_book": [["br1", "BR", "สำนักงานใหญ่"]],
        "txtregisbehalf": [["r1", "R", "บริษัท"]],
        "txtusers": _ADVISORS,
        "txtcarpaint": _PAINTS,
        "txtbanknametfmon": _BANKS,
        "txtbanknametffrom": _BANKS,
        "txtbanknamecheque": _BANKS,
        "txtbanknamecashiercq": _BANKS,
        "txtbanknamecddbc": _BANKS,
    }
    elems.update(over)
    return elems


class BookingAuthoritativeChainTests(unittest.TestCase):
    """订车提交链(真载荷解析,不 mock resolve_booking_payload):

    读走管理员权威会话(一次全主档 + 一次选中车颜色 + 一次顾问组织 + 客户档直读),
    写只落销售 transport 且 drfcbc/new.php 正好一次;成功后缓存吃同一份权威快照。
    """

    def setUp(self):
        self.mem = _Mem()
        self.es = contextlib.ExitStack()
        self.es.enter_context(mock.patch.object(mc, "_read", side_effect=self.mem.read))
        self.es.enter_context(mock.patch.object(mc, "_write", side_effect=self.mem.write))
        self.addCleanup(self.es.close)

    def _qa(self):
        qa = {
            "step": "pay_more",
            "endpoint_id": "E1",
            "customer": {"id": _CUSTOMER_ID, "name": "สมชาย ใจดี"},
            "advisor": {"id": "335", "name": "sale02"},
            "draft": {"people_id": _PEOPLE_ID, "name": "สมชาย ใจดี", "phone": "0899999999"},
            "files": {"id_card_mid": "mid-card", "slip_mid": None},
            "answers": {
                "place": {"id": "pl1", "name": "สาขาบางนา"},
                "car": {"id": "c1", "label": "DMX D-Max"},
                "paint": {"id": "p1", "name": "ขาว"},
                "delivery_date_be": "01/01/2570",
                "term": {"id": "t1", "name": "เงินสด"},
                "regis": {"id": "r1", "name": "บริษัท"},
                "regis_name": "บริษัท สมชาย จำกัด",
            },
            "payments": [
                {
                    "channel": "transfer",
                    "amount": "5000.00",
                    "extra": {
                        "src": "SCB",
                        "src_bank_id": "1",
                        "src_bank_name": "SCB",
                        "src_account_name": "Customer",
                        "src_account_no": "1111111111",
                        "src_branch_name": "Rayong",
                        "src_time": "14:00",
                        "dst_bank_id": "1",
                        "dst_bank_name": "SCB",
                        "dst_business_name": "Company",
                        "dst_account_no": "1234567890123",
                        "dst_branch_name": "ระยอง",
                        "dst_id": "1",
                        "dst": "SCB · 1234567890123 · ระยอง",
                    },
                }
            ],
            "pending_channel": {},
            "audit": [],
        }
        qa["master_snapshot"] = bf.master_contract.build_snapshot(_full_masters())
        return qa

    def _run(self, *, admin_posts=None, admin_factory=None, site=None, qa=None):
        """跑一次真建单链:返回 (result, sales, admin, factory, trace, site, adapter)。

        只用假 transport 与假适配器;载荷解析/建单/回读全走真代码(零网络)。
        """
        site = site or _BookingSite()
        sales = _Transport("sales", posts=site.posts)
        admin = _Transport(
            "admin", posts=admin_posts or _admin_booking_posts(_admin_master_elems())
        )
        factory = admin_factory if admin_factory is not None else _AdminFactory(admin)
        adapter = _Adapter(sales, admin_factory=factory)
        trace = _Trace(sales, admin)
        trace.bind(adapter._client())
        self.es.enter_context(_runner(adapter))
        self.es.enter_context(
            mock.patch("services.line_dms.booking_flow.mrerp_booking_lock", _lock_cm)
        )
        result = bf._book_in_session(_EP_BOOKING, {"qa": qa or self._qa()})
        return result, sales, admin, factory, trace, site, adapter

    def test_real_payload_resolution_runs_on_the_admin_snapshot(self):
        """预检 + 载荷解析成功;销售只见创建单据必需的请求,drfcbc/new.php 正好一次。"""
        result, sales, admin, _factory, trace, site, _adapter = self._run()

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["booking_id"], _BookingSite.BID)
        self.assertEqual(result["booking_no"], _BookingSite.DOCNO)
        # 载荷真解析过:顾问/车/颜色/店/条款/登记/客户都来自权威行,不是 mock 的占位值
        submitted = site.stored
        self.assertEqual(
            {
                key: submitted[key]
                for key in (
                    "usersval",
                    "carval",
                    "carpaintval",
                    "placebookval",
                    "termsaleval",
                    "regisbehalfval",
                    "cusval",
                    "txtpeopleid",
                )
            },
            {
                "usersval": "335",
                "carval": "c1",
                "carpaintval": "p1",
                "placebookval": "pl1",
                "termsaleval": "t1",
                "regisbehalfval": "r1",
                "cusval": _CUSTOMER_ID,
                "txtpeopleid": _PEOPLE_ID,
            },
        )
        self.assertEqual((submitted["branch_bookval"], submitted["team_bookval"]), ("1", "30"))
        self.assertEqual(submitted["txtuserstel"], "0811111111")  # 顾问电话来自权威名册行
        self.assertEqual(submitted["txtdocno"], _BookingSite.DOCNO)
        # 逐问值覆盖端点默认基线:交车日/登记人/订金渠道都进了提交表单
        self.assertEqual(submitted["txtcardeliverydate"], "01/01/2570")
        self.assertEqual(submitted["txtregisname"], "บริษัท สมชาย จำกัด")
        self.assertEqual(submitted["txtmoneytfmon"], "5000.00")
        self.assertEqual(submitted["txtaccountnumtfmon"], "1234567890123")
        # drfcbc/new.php 只在销售会话上、正好一次
        self.assertEqual(len(sales.paths_matching("new.php")), 1)
        self.assertEqual(admin.paths_matching("new.php"), [])
        # 销售会话只出现创建单据必需的请求:主档/客户档/顾问组织一个都没落到销售上
        self.assertEqual(sales.bshsd_elems(), [])
        self.assertEqual(sales.paths_matching("cus/"), [])
        self.assertEqual(sales.paths_matching("detailbooksell.php"), [])
        self.assertEqual(
            [url for url in sales.paths() if not url.endswith(_SALES_ALLOWED_PATHS)], []
        )
        # 每一次 DMS 请求都落在「权威只读闸」或「销售会话」上:没有裸管理员会话的读写
        self.assertEqual({where for where, _m, _url in trace.entries}, {"admin(readonly)", "sales"})

    def test_preflight_does_not_refetch_masters_per_field(self):
        """一次权威全主档快照:每个 elemname 正好一次;颜色一次;组织一次;单次管理员解析。"""
        _result, _sales, admin, factory, _trace, _site, _adapter = self._run()

        elems = admin.bshsd_elems()
        self.assertEqual(factory.calls, 1)  # 整块只解析一次管理员 transport
        self.assertEqual(len(elems), len(set(elems)), f"主档被按字段重复拉取: {sorted(elems)}")
        self.assertEqual(set(elems), set(_admin_master_elems().keys()))
        self.assertEqual(
            [
                d.get("idcar")
                for _m, url, d in admin.calls
                if url.endswith("bshsd.php") and d.get("elemname") == "txtcarpaint"
            ],
            ["c1"],
        )
        self.assertEqual(len(admin.paths_matching("detailbooksell.php")), 1)
        # 客户档按客户号直读正好一次(另一处 cus/form.php 是称谓名册取数,不是客户档)
        self.assertEqual(
            [
                d
                for _m, url, d in admin.calls
                if url.endswith("cus/form.php") and str(d.get("id") or "") == _CUSTOMER_ID
            ],
            [{"status": "e", "id": _CUSTOMER_ID}],
        )

    def test_cache_is_written_from_the_admin_snapshot_without_a_second_fetch(self):
        """成功后缓存吃 preflight 权威快照:完整银行 + 选中车颜色;销售裁剪视图不污染缓存。"""
        old_paints = [["p9", "BLACK", "ดำ"]]
        self.mem.rows["E1"] = {
            "cars": [["stale", "STALE", "Stale"]],
            "company_banks": [["9", "OLD", "OLD BANK", "", ""]],
            "paints_by_car": {"c9": old_paints},
        }

        result, sales, admin, _factory, _trace, _site, _adapter = self._run()

        self.assertTrue(result["ok"], result)
        written = self.mem.rows["E1"]
        self.assertEqual(written["cars"], _CARS)  # 管理员完整视图,不是销售的空表
        self.assertEqual(written["company_banks"], _BANKS)  # 新银行不被旧银行覆盖
        self.assertEqual(written["source_banks"], _BANKS)
        self.assertEqual(written["paints_by_car"]["c1"], _PAINTS)  # 选中车型颜色来自权威快照
        self.assertEqual(written["paints_by_car"]["c9"], old_paints)  # 未读车型旧色保留
        # 不再二次抓取:销售一条主档都没读,管理员每个 elemname 也只读一次
        self.assertEqual(sales.bshsd_elems(), [])
        elems = admin.bshsd_elems()
        self.assertEqual(len(elems), len(set(elems)))

    def test_admin_auth_failure_fails_closed_before_any_request(self):
        """配了管理员但认证失败 → 明确报错:销售会话一个请求都不发(更别说写)。"""
        factory = _AdminFactory(error=MrerpDmsAdminAuthError("admin creds bounced"))

        result, sales, admin, _factory, _trace, _site, _adapter = self._run(admin_factory=factory)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "ERR_DMS_ADMIN_AUTH")
        self.assertEqual(sales.calls, [])
        self.assertEqual(admin.calls, [])
        self.assertEqual(self.mem.rows, {})  # 没写缓存

    def test_dms_rejecting_the_booking_is_reported_without_admin_rewrite(self):
        """DMS 拒收 → 如实上报,只提交过一次,绝不改用管理员会话重写同一张单。"""
        site = _BookingSite()
        site.reject = "err::ไม่มีสิทธิ์"

        result, sales, admin, _factory, _trace, _site, _adapter = self._run(site=site)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "ERR_DMS_IMPORT")
        self.assertEqual(len(sales.paths_matching("new.php")), 1)
        self.assertEqual(admin.paths_matching("new.php"), [])
        self.assertEqual(self.mem.rows, {})  # 没成功就不刷缓存

    def test_without_admin_credentials_everything_stays_on_the_sales_session(self):
        """未配管理员 → 单凭据兼容路径:主档/客户档/组织/建单全在销售会话上,行为不变。"""
        site = _BookingSite()
        sales = _Transport("sales", posts=site.posts)
        elsewhere = _admin_booking_posts(_admin_master_elems())

        def _sales_posts(url, data):
            booking = site.posts(url, data)
            return booking if booking.text else elsewhere(url, data)

        sales._posts = _sales_posts
        adapter = _Adapter(sales, admin=None)
        trace = _Trace(sales, None)
        trace.bind(adapter._client())

        with (
            _runner(adapter),
            mock.patch("services.line_dms.booking_flow.mrerp_booking_lock", _lock_cm),
        ):
            result = bf._book_in_session(_EP_BOOKING, {"qa": self._qa()})

        self.assertTrue(result["ok"], result)
        self.assertEqual(len(sales.paths_matching("new.php")), 1)
        self.assertTrue(sales.bshsd_elems())  # 主档读销售会话(逐字节兼容)
        self.assertEqual(len(sales.paths_matching("detailbooksell.php")), 1)
        self.assertEqual({where for where, _m, _url in trace.entries}, {"sales"})

    def test_customer_dirty_nests_writer_session_and_restores_read_only_gate(self):
        """customer_dirty:真实 _writer_session 嵌套 —— 写切 raw admin、退出落回只读闸、
        整块退出回到销售;订车写仍是销售。"""
        qa = self._qa()
        qa["customer_dirty"] = True

        result, sales, admin, _factory, trace, _site, adapter = self._run(qa=qa)

        self.assertTrue(result["ok"], result)
        edit_index = trace.first_index("cus/edit.php", label="admin(writer)")
        # 客户改档的读写全部落在 raw admin writer 上(_ReadOnlyTransport 会拒写编辑表单)
        write_names = {url.rsplit("/", 1)[-1] for url in trace.urls("admin(writer)")}
        self.assertEqual(
            write_names,
            {
                "form.php",
                "listdistricts.php",
                "listsubdistricts.php",
                "listzipcodes.php",
                "edit.php",
            },
        )
        self.assertEqual(admin.paths_matching("cus/new.php"), [])
        # 退出 writer 会话落回本块的只读闸:紧接着的客户档直读走 admin(readonly)
        form_index = trace.first_index("cus/form.php", after=edit_index, label="admin(readonly)")
        self.assertLess(edit_index, form_index)
        # 订车写仍在销售会话上
        trace.first_index("drfcbc/new.php", label="sales")
        # 整块退出后 client 回到销售 transport(绝不留在管理员态)
        self.assertIs(adapter._client().transport, sales)


@contextlib.contextmanager
def _lock_cm(ep=None):
    yield


if __name__ == "__main__":
    unittest.main()
