# -*- coding: utf-8 -*-
"""MR.ERP HTTP 直写 adapter · 公开接口与 Playwright 版 MRERPAdapter 一致。

`with MrErpHttpAdapter(...) as a: a.upload_invoice_batch(histories, mappings)`
→ ImportResult(success[SuccessRow] / failed[FailedRow])。

导入 5 步(known-facts §5)全走 requests,importpc 后**强制拉 report.php 逐行判成败**
(不信 "2"),这是"像 Express 一样稳"的回读闸。老 PHP 单账号单会话 → 复用 session_lock 串行。

已接:赊销/现金销售(S1/S3)· 方向识别(S2a)· 销项缺买方客户+商品自动建(S2b·autocreate)。
采购/库存/科目在 S3/S4。构造签名兼容 build_mrerp_adapter 传入的全部 kwargs(未用者吞下)。
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from services.erp import mrerp_xlsx_generator as _gen
from services.erp.exceptions import MRERPBusinessError
from services.erp.mrerp_adapter_models import FailedRow, ImportResult, SuccessRow
from services.erp.mrerp_business_friendly import translate_reasons
from services.erp.mrerp_http.account_valve import (
    ACCOUNT_REVIEW_CODE,
    account_gate,
    tag_account_review,
)
from services.erp.mrerp_http.modules import MrErpModule, get_module
from services.erp.mrerp_http.report_parse import parse_master_report
from services.erp.mrerp_http.session import MrErpSession
from services.erp.mrerp_report_parser import parse_import_report
from services.erp.session_lock import mrerp_session_lock

logger = logging.getLogger(__name__)

# 预览页解析(标准库正则 · 不引 bs4:bs4 非 prod 依赖,直写运行期不能靠它)。
_FORM_RE = re.compile(
    r'<form\b[^>]*\bid=["\'](frmimport\d+)["\'][^>]*>(.*?)</form>', re.IGNORECASE | re.DOTALL
)
_TAG_RE = re.compile(r"<(input|select|textarea)\b([^>]*?)/?>", re.IGNORECASE)
_ATTR_RE = re.compile(r'([\w-]+)\s*=\s*"([^"]*)"')
_TAGSTRIP_RE = re.compile(r"<[^>]+>")
_HINT_KEYWORDS = ("ไม่พบ", "ผิดพลาด", "ไม่ถูกต้อง", "ซ้ำ", "ไม่ครบ")


def _selmenu_param(m) -> str:
    """selmenu 表单参数 · 主数据导入(imparmas/impstkmas…)无 selmenu → 发空串,别发 'None'。"""
    return "" if m.selmenu is None else str(m.selmenu)


class MrErpHttpAdapter:
    def __init__(
        self,
        *,
        login_url: str,
        username: str,
        password: str,
        comidyear: str = "6",
        seldb: str = "1",
        doc_type: str = "sales_credit",
        timeout: int = 30,
        serialize_sessions: bool = True,
        **_ignored: Any,  # 吞下 Playwright 版特有 kwargs(headless/retry/master-data*)· S2 起接线
    ):
        if not login_url:
            raise ValueError("login_url required")
        if not username or not password:
            raise ValueError("username and password required")
        self.login_url = login_url.rstrip("/")
        self._username = username
        self._password = password
        self.comidyear = str(comidyear)
        self.seldb = str(seldb)
        self.module: MrErpModule = get_module(doc_type)
        self.timeout = timeout
        self.serialize_sessions = bool(serialize_sessions)
        self._sess: Optional[MrErpSession] = None
        self._lock_cm = None

    @classmethod
    def from_encrypted(
        cls, *, login_url: str, encrypted_username: str, encrypted_password: str, **kwargs
    ) -> "MrErpHttpAdapter":
        from core.kms_helper import decrypt_str

        return cls(
            login_url=login_url,
            username=decrypt_str(encrypted_username),
            password=decrypt_str(encrypted_password),
            **kwargs,
        )

    # ---- lifecycle (同 MRERPAdapter 契约) -----------------------------

    def __enter__(self) -> "MrErpHttpAdapter":
        if self.serialize_sessions:
            self._lock_cm = mrerp_session_lock(f"{self.login_url}|{self._username}")
            try:
                self._lock_cm.__enter__()
            except Exception:
                self._lock_cm = None
        self._sess = MrErpSession(
            login_url=self.login_url,
            username=self._username,
            password=self._password,
            comidyear=self.comidyear,
            seldb=self.seldb,
            timeout=self.timeout,
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._sess is not None:
            try:
                self._sess.session.close()
            except Exception:
                pass
        self._sess = None
        if self._lock_cm is not None:
            try:
                self._lock_cm.__exit__(exc_type, exc, tb)
            finally:
                self._lock_cm = None

    # ---- 主入口 -------------------------------------------------------

    def upload_routed_batch(
        self, histories: List[Dict[str, Any]], mappings: Dict[str, Any]
    ) -> ImportResult:
        """方向自动路由后推送(采购→采购模块 · 销项/ambiguous 保持默认)· 见 routing.route_and_upload。"""
        if self._sess is None:
            raise RuntimeError("MrErpHttpAdapter used outside `with` block")
        from services.erp.mrerp_http.routing import route_and_upload

        return route_and_upload(self, histories, mappings)

    def upload_invoice_batch(
        self, histories: List[Dict[str, Any]], mappings: Dict[str, Any]
    ) -> ImportResult:
        if not histories:
            return ImportResult(total=0)
        if self._sess is None:
            raise RuntimeError("MrErpHttpAdapter used outside `with` block")
        m = self.module
        if not m.verified or m.selmenu is None:
            raise MRERPBusinessError(f"doc_type={m.doc_type} 直写未就绪(selmenu/模板待补 · S3/S4)")
        t0 = time.time()
        original = histories

        # ★匹配闸:票面买卖方须符合套账主体(own_tax_id 由调用方从套账解析后放 mappings)。
        # MR.ERP 导入不带卖方身份(默认=登录公司)→ 防"推错套账"只能靠这里的税号锚点。
        # 提供了 own_tax_id 才启用(未提供=调用方未接,保持旧行为);不符/无法判 → 挡下不推、不自建。
        histories, mismatch_failed = self._filter_by_account_set(histories, mappings)
        if not histories:
            return self._result(original, [], mismatch_failed, t0, 0)

        # 科目安全阀(主动层):提供了该套账科目表且配置科目码不在表内 → 全挡下退回用户配置(不硬建)。
        review = account_gate(mappings)
        if review:
            reasons = [ACCOUNT_REVIEW_CODE, "科目码不在该套账科目表: " + ", ".join(review)]
            fr = [self._fail_row(h, reasons) for h in histories]
            return self._result(original, [], mismatch_failed + fr, t0, 0)

        # 缺对手方主数据则自建并注入码(须在 preflight 前)· 销项建买方客户 / 采购建卖方供应商。
        # 除套账主体外一切可自建 · 见 autocreate。
        if m.doc_type.startswith("sales"):
            from services.erp.mrerp_http.autocreate import provision_customers

            provision_customers(self, histories, mappings)
        elif m.doc_type == "purchase":
            from services.erp.mrerp_http.autocreate import provision_suppliers

            provision_suppliers(self, histories, mappings)

        valid, preflight_failed = self._preflight(histories, mappings)
        if not valid:
            return self._result(original, [], mismatch_failed + preflight_failed, t0, 0)

        # 销/采/库存:明细行对不上已有商品则自建并注入码(在生成 xlsx 前)· 见 autocreate
        if m.doc_type.startswith("sales") or m.doc_type in (
            "purchase",
            "stock_receive",
            "stock_issue",
        ):
            from services.erp.mrerp_http.autocreate import provision_products

            provision_products(self, valid, mappings)

        xlsx_bytes = _gen.generate_xlsx(valid, mappings, sheet_kind=m.sheet_kind)
        expected = [_gen.derive_mrerp_invoice_no(h) for h in valid]

        probe = f"{m.path}/formupload.php?idmenu={m.idmenu}"
        self._sess.prepare(probe)

        self._upload_xlsx(xlsx_bytes)
        form_fields, row_ids, idus_form = self._fetch_preview()
        if not row_ids:
            hints = self._preview_hints()
            msg = "preview has no importable rows (xlsx rejected server-side)"
            if hints:
                msg += ": " + " / ".join(hints[:3])
            raise MRERPBusinessError(msg)
        raw = self._confirm_import(form_fields, row_ids)

        success_rows, failed_rows = self._classify(valid, expected, raw, idus_form)
        return self._result(
            original,
            success_rows,
            mismatch_failed + preflight_failed + failed_rows,
            t0,
            len(xlsx_bytes),
        )

    def _fail_row(self, h: Dict[str, Any], reasons: List[str]) -> FailedRow:
        return FailedRow(
            invoice_no=_gen.derive_mrerp_invoice_no(h),
            reasons=reasons,
            reasons_friendly=translate_reasons(reasons),
            original=h,
        )

    def _filter_by_account_set(
        self, histories: List[Dict[str, Any]], mappings: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[FailedRow]]:
        """匹配闸:只挡能确认是别家的票(读不到税号→放行不误挡)· _own_tax_id 提供才启用(否则全放行)。"""
        own = mappings.get("_own_tax_id") if isinstance(mappings, dict) else None
        if not own:
            return histories, []
        from services.erp.mrerp_http.routing import confirmed_account_set_mismatch

        expected = "sales" if self.module.doc_type.startswith("sales") else "purchase"
        kept: List[Dict[str, Any]] = []
        failed: List[FailedRow] = []
        for h in histories:
            if confirmed_account_set_mismatch(h, h, own_tax_id=own, expected_direction=expected):
                reasons = ["票面买卖方与套账主体不符 · 未推送(防推错套账)"]
                failed.append(self._fail_row(h, reasons))
            else:
                kept.append(h)
        return kept, failed

    # ---- 自建主数据 --------------------------------------------------

    def create_customers(
        self, customers: List[Dict[str, Any]], mappings: Dict[str, Any]
    ) -> Dict[str, bool]:
        """自建客户(idempotent)· 导入 imparmas · 返回 {客户码: 成功}。已存在视为成功。"""
        return self._import_masters(get_module("master_customer"), customers, mappings, "A")

    def create_products(
        self, products: List[Dict[str, Any]], mappings: Dict[str, Any]
    ) -> Dict[str, bool]:
        """自建商品(idempotent)· 导入 impstkmas · 返回 {商品码: 成功}。已存在视为成功。"""
        return self._import_masters(get_module("master_product"), products, mappings, "C")

    def create_suppliers(
        self, suppliers: List[Dict[str, Any]], mappings: Dict[str, Any]
    ) -> Dict[str, bool]:
        """自建供应商(idempotent)· 导入 impapmas · 返回 {供应商码: 成功}。已存在视为成功。"""
        return self._import_masters(get_module("master_supplier"), suppliers, mappings, "A")

    def _import_masters(
        self, module, records: List[Dict[str, Any]], mappings: Dict[str, Any], code_col: str
    ) -> Dict[str, bool]:
        """自建主数据通用流:导入 → raw=1 全成功;否则读 report 判逐行(空备注/已存在=成功)。"""
        codes = [str(r.get("code") or "") for r in records if r.get("code")]
        if not codes:
            return {}
        if self._sess is None:
            raise RuntimeError("MrErpHttpAdapter used outside `with` block")
        xlsx = _gen.generate_xlsx(records, mappings, sheet_kind=module.sheet_kind)
        self._sess.prepare(f"{module.path}/formupload.php?idmenu={module.idmenu}")
        self._upload_xlsx(xlsx, module=module)
        form_fields, row_ids, idus_form = self._fetch_preview(module=module)
        if not row_ids:
            return {c: False for c in codes}
        raw = self._confirm_import(form_fields, row_ids, module=module)
        if raw == "1":
            return {c: True for c in codes}
        notes = parse_master_report(self._fetch_report(idus_form, module=module), code_col=code_col)
        # 空备注=新建成功;"มีอยู่ในระบบแล้ว"(该码已存在)=幂等重复,视为成功
        return {c: (not notes.get(c) or "มีอยู่ในระบบแล้ว" in notes.get(c, "")) for c in codes}

    # ---- 5 步 --------------------------------------------------------

    def _upload_xlsx(self, xlsx_bytes: bytes, module=None) -> None:
        m = module or self.module
        r = self._sess.post(
            f"{m.path}/component/uploadexcel.php",
            files={
                "uploadfile": (
                    "import.xlsx",
                    xlsx_bytes,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={"idus": str(self._sess.idus), "selmenu": _selmenu_param(m)},
            headers={
                "Referer": f"{self.login_url}/{m.path}/formupload.php?idmenu={m.idmenu}",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": self.login_url,
            },
        )
        body = (r.text or "").strip()
        if r.status_code >= 400:
            raise MRERPBusinessError(f"upload rejected {r.status_code}: {body[:200]}")
        # 成功 = 空 body;非空 = 错误描述(JS 会 alert)
        if body:
            raise MRERPBusinessError(f"upload rejected: {body[:300]}")

    def _fetch_preview(self, module=None) -> Tuple[List[Tuple[str, str]], List[str], Optional[str]]:
        m = module or self.module
        r = self._sess.post(
            f"{m.path}/formrdpc.php",
            data={"idus": str(self._sess.idus), "selmenu": _selmenu_param(m)},
            headers={
                "Referer": f"{self.login_url}/{m.path}/formupload.php?idmenu={m.idmenu}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": self.login_url,
            },
        )
        self._last_preview_html = r.text or ""
        if r.status_code >= 400:
            raise MRERPBusinessError(f"preview failed {r.status_code}")
        return self._parse_preview_form(self._last_preview_html)

    def _confirm_import(
        self, form_fields: List[Tuple[str, str]], row_ids: List[str], module=None
    ) -> str:
        """按浏览器 FormData(#frmimport1) 提交整表(全 hidden + 勾选 cbimport)· 比只发 cbimport 更忠实。"""
        m = module or self.module
        files: List[Tuple[str, Tuple[Optional[str], str]]] = [
            (name, (None, value)) for name, value in form_fields
        ]
        have = {n for n, _ in form_fields}
        if "cballfrmimport1" not in have:
            files.append(("cballfrmimport1", (None, "on")))
        for rid in row_ids:
            key = f"cbimport[{rid}]"
            if key not in have:
                files.append((key, (None, str(rid))))
        r = self._sess.post(
            f"{m.path}/component/importpc.php",
            files=files,
            headers={
                "Referer": f"{self.login_url}/{m.path}/formrdpc.php",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": self.login_url,
            },
        )
        raw = (r.text or "").strip()
        if r.status_code >= 400:
            raise MRERPBusinessError(f"importpc rejected {r.status_code}: {raw[:200]}")
        if not raw:
            raise MRERPBusinessError("importpc returned empty body (unknown state)")
        return raw

    def _fetch_report(self, idus_form: Optional[str], module=None) -> bytes:
        m = module or self.module
        r = self._sess.post(
            f"{m.path}/component/report.php",
            data={"numform": "1", "idus": str(idus_form or self._sess.idus)},
            headers={"Referer": f"{self.login_url}/{m.path}/formrdpc.php"},
        )
        if r.status_code >= 400 or not r.content:
            raise MRERPBusinessError(f"report.php failed {r.status_code} ({len(r.content)}B)")
        return r.content

    # ---- 分类:回读 report 判真成败 ----------------------------------

    def _classify(
        self, valid: List[Dict[str, Any]], expected: List[str], raw: str, idus_form: Optional[str]
    ) -> Tuple[List[SuccessRow], List[FailedRow]]:
        by_inv = {inv: h for inv, h in zip(expected, valid)}
        if raw == "1":
            # importpc "1" = 全部提交 · 不出报告
            return (
                [
                    SuccessRow(invoice_no=i, mrerp_bill_no=f"SI{i}", original=by_inv.get(i, {}))
                    for i in expected
                ],
                [],
            )
        # 任何其他情况(含 "2")→ 必拉 report 逐行判定,不臆断
        report = parse_import_report(self._fetch_report(idus_form))
        success = [
            SuccessRow(invoice_no=i, mrerp_bill_no=f"SI{i}", original=by_inv.get(i, {}))
            for i in report.success
        ]
        # 科目安全阀:report 报科目未匹配 → 归为 ERR_ACCOUNT_NEEDS_REVIEW(退回用户配置,不硬建)
        failed = []
        for row in report.failed:
            reasons = tag_account_review(list(row.reasons))
            failed.append(
                FailedRow(
                    invoice_no=row.invoice_no,
                    reasons=reasons,
                    reasons_friendly=translate_reasons(reasons),
                    original=by_inv.get(row.invoice_no, {}),
                )
            )
        seen = {s.invoice_no for s in success} | {f.invoice_no for f in failed}
        for inv in expected:
            if inv not in seen:
                reasons = ["report did not mention this invoice"]
                failed.append(
                    FailedRow(
                        invoice_no=inv,
                        reasons=reasons,
                        reasons_friendly=translate_reasons(reasons),
                        original=by_inv.get(inv, {}),
                    )
                )
        return success, failed

    # ---- helpers -----------------------------------------------------

    def _preflight(
        self, histories: List[Dict[str, Any]], mappings: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[FailedRow]]:
        valid: List[Dict[str, Any]] = []
        failed: List[FailedRow] = []
        doc = self.module.doc_type
        if doc == "purchase":
            from services.erp.mrerp_xlsx_purchase import validate_purchase_history as _validate
        elif doc in ("stock_receive", "stock_issue"):
            from services.erp.mrerp_xlsx_stock import validate_stock_history as _validate
        else:
            _validate = _gen.validate_history_for_sales_credit
        for h in histories:
            ok, err_code, warnings = _validate(h, mappings)
            if ok:
                valid.append(h)
            else:
                failed.append(self._fail_row(h, [err_code or "ERR_UNKNOWN_PREFLIGHT"]))
        return valid, failed

    def _result(
        self,
        histories: List[Dict[str, Any]],
        success: List[SuccessRow],
        failed: List[FailedRow],
        t0: float,
        xlsx_size: int,
    ) -> ImportResult:
        res = ImportResult(total=len(histories))
        res.success = success
        res.failed = failed
        res.elapsed_ms = int((time.time() - t0) * 1000)
        res.xlsx_size_bytes = xlsx_size
        return res

    def _preview_hints(self) -> List[str]:
        html = getattr(self, "_last_preview_html", "") or ""
        if not html:
            return []
        hints: List[str] = []
        for line in _TAGSTRIP_RE.sub("\n", html).split("\n"):
            line = line.strip()
            if not line or len(line) > 200 or line in hints:
                continue
            if any(k in line for k in _HINT_KEYWORDS):
                hints.append(line)
        return hints[:5]

    @staticmethod
    def _parse_preview_form(
        html: str,
    ) -> Tuple[List[Tuple[str, str]], List[str], Optional[str]]:
        """从预览 HTML 抽 form#frmimport1 的全部字段 + cbimport row_ids + 该 form 的 idus。

        标准库正则:确认表(sales_credit)只含 hidden input + cbimport 复选框,无 <select>。
        """
        mform = _FORM_RE.search(html)
        scope = mform.group(2) if mform else html
        fields: List[Tuple[str, str]] = []
        row_ids: List[str] = []
        idus_form: Optional[str] = None
        for _tag, attrs_str in _TAG_RE.findall(scope):
            attrs = {k.lower(): v for k, v in _ATTR_RE.findall(attrs_str)}
            name = attrs.get("name")
            if not name:
                continue
            if attrs.get("type", "").lower() == "checkbox":
                # 预览默认勾选的行才提交(cbimport[N])
                if "checked" in attrs_str.lower() or name.startswith("cbimport"):
                    fields.append((name, attrs.get("value", "on")))
                    key = name[len("cbimport") :].strip("[]")
                    if name.startswith("cbimport") and key.isdigit():
                        row_ids.append(key)
                continue
            val = attrs.get("value", "")
            fields.append((name, val))
            if name in ("idus", "idus1") and val.strip():
                idus_form = val.strip()
        return fields, row_ids, idus_form
