# -*- coding: utf-8 -*-
"""MR.ERP HTTP 直写 · 会话层(登录 / 选公司 / 抓 idus + 带鉴权判定的 get/post)。

老 PHP 站点约束(known-facts §2-§3 · 2026-07-01 test01 复测有效):
  - 必须先 GET 一次登录页才建 PHPSESSID,否则后续 POST 被丢。
  - checklogin.php 失败也返 200 + 登录表单 HTML,不 redirect → 靠"选公司后是否被踢回登录页"判成败。
  - idus(内部用户 id)在每个业务页以 <input hidden name=idus value=N> 出现,登录后 scrape 一次。
"""

from __future__ import annotations

import logging
import re
from typing import Optional

import requests

from services.erp.exceptions import MRERPAuthError, MRERPTechnicalError

logger = logging.getLogger(__name__)

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
)
_LOGIN_BOUNCE = ("checklogin", "/login/index", "/login/?", "/login.php", "/index.php")


class MrErpSession:
    """一次 MR.ERP 登录会话。持有 requests.Session(PHPSESSID cookie)+ idus。"""

    def __init__(
        self,
        *,
        login_url: str,
        username: str,
        password: str,
        comidyear: str = "6",
        seldb: str = "1",
        timeout: int = 30,
    ):
        self.base = login_url.rstrip("/")
        self._username = username
        self._password = password
        self.comidyear = str(comidyear)
        self.seldb = str(seldb)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": _UA})
        self.idus: Optional[str] = None
        self._logged_in = False
        self._company_selected = False

    # ---- lifecycle ---------------------------------------------------

    def login(self) -> None:
        """建 session + POST 凭据。真假留给 select_company 验(老 PHP 失败也返 200)。"""
        try:
            self.session.get(f"{self.base}/", timeout=self.timeout)
            self.session.get(f"{self.base}/login/login.php", timeout=self.timeout)
            r = self.session.post(
                f"{self.base}/login/checklogin.php",
                data={
                    "txtusers": self._username,
                    "txtpasswords": self._password,
                    "btnsubmit": "Submit",
                },
                headers={"Referer": f"{self.base}/", "Origin": self.base},
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise MRERPTechnicalError(f"login network error: {e}") from e
        if r.status_code >= 500:
            raise MRERPTechnicalError(f"login server error {r.status_code}")
        if not self.session.cookies.get("PHPSESSID"):
            raise MRERPAuthError("no PHPSESSID after checklogin (session not established)")
        self._logged_in = True

    def select_company(self, idus_probe_path: str = "impartran/formupload.php?idmenu=370") -> str:
        """选公司 + 抓 idus。被踢回登录页 = 凭据错。返回 idus。"""
        if not self._logged_in:
            raise MRERPAuthError("select_company before login")
        try:
            self.session.get(f"{self.base}/login/selectdb.php", timeout=self.timeout)
            r = self.session.get(
                f"{self.base}/login/mainmenu.php",
                params={"comidyear": self.comidyear, "seldb": self.seldb},
                headers={"Referer": f"{self.base}/login/selectdb.php"},
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise MRERPTechnicalError(f"select_company network error: {e}") from e
        if r.status_code != 200:
            raise MRERPTechnicalError(f"select_company status {r.status_code}")
        if self._is_login_bounced(r):
            raise MRERPAuthError("credentials rejected (bounced to login on select_company)")

        try:
            r2 = self.session.get(
                f"{self.base}/{idus_probe_path}",
                headers={"Referer": f"{self.base}/login/mainmenu.php"},
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise MRERPTechnicalError(f"idus probe network error: {e}") from e
        idus = self._scrape_idus(r2.text) or self._scrape_idus(r.text)
        if not idus:
            raise MRERPAuthError("cannot scrape idus (server returned login page?)")
        self.idus = idus
        self._company_selected = True
        return idus

    def prepare(self, idus_probe_path: str = "impartran/formupload.php?idmenu=370") -> None:
        """登录 + 选公司(幂等)· 让会话就绪可发业务请求。"""
        if not self._logged_in:
            self.login()
        if not self._company_selected:
            self.select_company(idus_probe_path)

    # ---- request helpers --------------------------------------------

    def get(self, path: str, **kw) -> requests.Response:
        return self._request("GET", path, **kw)

    def post(self, path: str, **kw) -> requests.Response:
        return self._request("POST", path, **kw)

    def _request(self, method: str, path: str, **kw) -> requests.Response:
        url = path if path.startswith("http") else f"{self.base}/{path.lstrip('/')}"
        kw.setdefault("timeout", self.timeout)
        try:
            r = self.session.request(method, url, **kw)
        except requests.RequestException as e:
            raise MRERPTechnicalError(f"{method} {path} network error: {e}") from e
        if r.status_code in (401, 403):
            self._logged_in = self._company_selected = False
            raise MRERPAuthError(f"session expired ({r.status_code}) on {path}")
        return r

    # ---- internals ---------------------------------------------------

    @staticmethod
    def _is_login_bounced(r: requests.Response) -> bool:
        if any(x in r.url.lower() for x in _LOGIN_BOUNCE):
            return True
        body = (r.text or "")[:6000].lower()
        return "txtpasswords" in body or "txtusers" in body

    @staticmethod
    def _scrape_idus(html: str) -> Optional[str]:
        if not html:
            return None
        for pat in (
            r'<input[^>]*\bname=["\']idus["\'][^>]*\bvalue=["\'](\d+)["\']',
            r'<input[^>]*\bvalue=["\'](\d+)["\'][^>]*\bname=["\']idus["\']',
        ):
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                return m.group(1)
        return None
