# -*- coding: utf-8 -*-
"""MR.ERP HTTP 直写 adapter · 公开接口与 Playwright 版 MRERPAdapter 一致。

`with MrErpHttpAdapter(...) as a: a.upload_invoice_batch(histories, mappings)`
→ ImportResult(success[SuccessRow] / failed[FailedRow])。

导入 5 步(known-facts §5)全走 requests,importpc 后**强制拉 report.php 逐行判成败**
(不信 "2"),这是"像 Express 一样稳"的回读闸。老 PHP 单账号单会话 → 复用 session_lock 串行。

S1 仅接 sales_credit(赊销)· 主数据自动建/方向识别在 S2 · 现金/采购/库存在 S3/S4。
构造签名兼容 build_mrerp_adapter 传入的全部 kwargs(未用者先吞下,S2 起接线)。
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
from services.erp.mrerp_http.modules import MrErpModule, get_module
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

        valid, preflight_failed = self._preflight(histories, mappings)
        if not valid:
            return self._result(histories, [], preflight_failed, t0, 0)

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
            histories, success_rows, preflight_failed + failed_rows, t0, len(xlsx_bytes)
        )

    # ---- 5 步 --------------------------------------------------------

    def _upload_xlsx(self, xlsx_bytes: bytes) -> None:
        m = self.module
        r = self._sess.post(
            f"{m.path}/component/uploadexcel.php",
            files={
                "uploadfile": (
                    "import.xlsx",
                    xlsx_bytes,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={"idus": str(self._sess.idus), "selmenu": str(m.selmenu)},
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

    def _fetch_preview(self) -> Tuple[List[Tuple[str, str]], List[str], Optional[str]]:
        m = self.module
        r = self._sess.post(
            f"{m.path}/formrdpc.php",
            data={"idus": str(self._sess.idus), "selmenu": str(m.selmenu)},
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

    def _confirm_import(self, form_fields: List[Tuple[str, str]], row_ids: List[str]) -> str:
        """按浏览器 FormData(#frmimport1) 提交整表(全 hidden + 勾选 cbimport)· 比只发 cbimport 更忠实。"""
        m = self.module
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

    def _fetch_report(self, idus_form: Optional[str]) -> bytes:
        m = self.module
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
        failed = [
            FailedRow(
                invoice_no=row.invoice_no,
                reasons=list(row.reasons),
                reasons_friendly=translate_reasons(list(row.reasons)),
                original=by_inv.get(row.invoice_no, {}),
            )
            for row in report.failed
        ]
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
        for h in histories:
            ok, err_code, warnings = _gen.validate_history_for_sales_credit(h, mappings)
            if ok:
                valid.append(h)
                continue
            inv = (
                _gen.derive_mrerp_invoice_no(h)
                if h.get("invoice_date")
                else (h.get("invoice_number") or h.get("invoice_no") or "?")
            )
            reasons = [err_code or "ERR_UNKNOWN_PREFLIGHT"]
            failed.append(
                FailedRow(
                    invoice_no=inv,
                    reasons=reasons,
                    reasons_friendly=translate_reasons(reasons),
                    original=h,
                )
            )
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
