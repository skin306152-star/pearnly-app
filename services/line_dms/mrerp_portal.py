# -*- coding: utf-8 -*-
"""Build the short-lived MR.ERP login relay used by the DMS LINE OA."""

from __future__ import annotations

import html
import secrets
from typing import Dict, Tuple

MRERP_ORIGIN = "https://www.mrerp4sme.com"
MRERP_LOGIN_URL = f"{MRERP_ORIGIN}/dms/login/checklogin.php"
MRERP_HOME_URL = f"{MRERP_ORIGIN}/dms/home/home.php"
MRERP_ROOT_URL = f"{MRERP_ORIGIN}/dms"


class PortalCredentialsMissing(Exception):
    pass


class PortalUnavailable(Exception):
    pass


def load_credentials(user_id: str) -> Tuple[str, str]:
    """Resolve this employee's enabled endpoint and decrypt credentials in memory."""
    from services.erp.dms_id_ocr import resolve_dms_endpoint
    from services.erp.erp_dms_push import _dms_plain_creds

    endpoint = resolve_dms_endpoint(str(user_id), None)
    if not endpoint:
        raise PortalCredentialsMissing("endpoint_missing")
    try:
        username, password = _dms_plain_creds(endpoint.get("config") or {})
    except Exception as exc:
        raise PortalUnavailable("credential_unavailable") from exc
    if not username or not password:
        raise PortalCredentialsMissing("credentials_missing")
    return username, password


def security_headers(nonce: str) -> Dict[str, str]:
    csp = (
        "default-src 'none'; "
        f"script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'; "
        f"form-action {MRERP_ORIGIN}; frame-src {MRERP_ORIGIN}; "
        "base-uri 'none'; object-src 'none'; frame-ancestors 'self'"
    )
    return {
        "Cache-Control": "no-store, no-cache, max-age=0, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
        "Referrer-Policy": "no-referrer",
        "X-Robots-Tag": "noindex, nofollow",
        "Content-Security-Policy": csp,
    }


def render_login_relay(username: str, password: str) -> Tuple[str, str]:
    """Return an uncached relay page; credentials exist only in the transient form."""
    nonce = secrets.token_urlsafe(18)
    safe_user = html.escape(username, quote=True)
    safe_password = html.escape(password, quote=True)
    page = f"""<!doctype html>
<html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer"><title>DMS</title>
<style nonce="{nonce}">html,body{{height:100%;margin:0}}body{{display:grid;place-items:center;font-family:system-ui,sans-serif;background:#f7f5ff;color:#30295f}}main{{text-align:center;padding:28px}}.spin{{width:34px;height:34px;margin:0 auto 18px;border:4px solid #ddd5ff;border-top-color:#7357eb;border-radius:50%;animation:r .8s linear infinite}}@keyframes r{{to{{transform:rotate(360deg)}}}}</style></head>
<body><main><div class="spin"></div><h1>กำลังเข้าสู่ระบบ DMS</h1><p>กรุณารอสักครู่</p></main>
<iframe id="mrerp-login-frame" name="mrerp-login-frame" hidden></iframe>
<form id="mrerp-login" method="post" action="{MRERP_LOGIN_URL}" target="mrerp-login-frame" autocomplete="off">
<input type="hidden" name="txtusers" value="{safe_user}" autocomplete="off">
<input type="hidden" name="txtpasswords" value="{safe_password}" autocomplete="off">
</form>
<script nonce="{nonce}">(function(){{'use strict';var form=document.getElementById('mrerp-login');var frame=document.getElementById('mrerp-login-frame');var sent=false;var openHome=function(){{location.replace('{MRERP_HOME_URL}');}};frame.addEventListener('load',function(){{if(sent)openHome();}});sent=true;form.submit();setTimeout(function(){{form.querySelectorAll('input').forEach(function(input){{input.value='';}});form.remove();}},0);setTimeout(openHome,5000);}})();</script></body></html>"""
    return page, nonce
