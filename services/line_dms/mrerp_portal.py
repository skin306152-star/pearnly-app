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
        f"form-action {MRERP_ORIGIN}; "
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
    """Return an uncached top-level login handoff for MR.ERP.

    Optimised flow (replaces the legacy 1800 ms + 4000 ms relay):
    1. User clicks → open a named ``about:blank`` popup (instant, no network).
    2. Immediately submit the login form targeting that popup.
    3. Poll the popup: while it stays on same-origin ``about:blank`` the login
       POST is still in flight; once it lands on the cross-origin checklogin
       page (session cookie set) send it to the home page. A slow network thus
       never cancels the in-flight login.
    DNS-prefetch / preconnect hints warm the connection while the user reads
    the confirmation screen.
    """
    nonce = secrets.token_urlsafe(18)
    safe_user = html.escape(username, quote=True)
    safe_password = html.escape(password, quote=True)
    page = f"""<!doctype html>
<html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer"><title>DMS</title>
<link rel="dns-prefetch" href="{MRERP_ORIGIN}">
<link rel="preconnect" href="{MRERP_ORIGIN}" crossorigin>
<style nonce="{nonce}">html,body{{height:100%;margin:0}}body{{display:grid;place-items:center;font-family:system-ui,sans-serif;background:#f7f5ff;color:#30295f}}main{{width:min(420px,calc(100% - 40px));text-align:center;padding:32px 24px;border-radius:24px;background:#fff;box-shadow:0 18px 48px rgba(48,41,95,.12)}}h1{{margin:0 0 12px;font-size:30px}}p{{margin:0 0 24px;line-height:1.6;color:#615b80}}button{{width:100%;min-height:52px;border:0;border-radius:14px;background:#7357eb;color:#fff;font:700 18px system-ui,sans-serif}}button:disabled{{opacity:.65}}#status{{min-height:26px;margin:18px 0 0;color:#615b80}}</style></head>
<body><main id="dms-portal"><h1>เข้าสู่ระบบ DMS</h1><p>กดปุ่มด้านล่างเพื่อเปิดระบบ DMS ในเบราว์เซอร์</p><button id="open-dms" type="button">เข้าสู่ระบบ DMS</button><p id="status" role="status" aria-live="polite"></p></main>
<form id="mrerp-login" method="post" action="{MRERP_LOGIN_URL}" autocomplete="off" hidden>
<input type="hidden" name="txtusers" value="{safe_user}" autocomplete="off">
<input type="hidden" name="txtpasswords" value="{safe_password}" autocomplete="off">
<input type="hidden" name="btnsubmit" value="Submit">
</form>
<script nonce="{nonce}">(function(){{'use strict';var button=document.getElementById('open-dms');var status=document.getElementById('status');var form=document.getElementById('mrerp-login');var windowName='pearnly-mrerp-dms';var reset=function(message){{button.disabled=false;status.textContent=message;}};button.addEventListener('click',function(){{button.disabled=true;status.textContent='กำลังเปิดระบบ DMS กรุณารอสักครู่';var portal=window.open('about:blank',windowName);if(!portal){{reset('ไม่สามารถเปิดเบราว์เซอร์ได้ กรุณาอนุญาตหน้าต่างใหม่แล้วลองอีกครั้ง');return;}}try{{form.target=windowName;form.submit();form.querySelectorAll('input').forEach(function(input){{input.value='';}});form.remove();}}catch(error){{reset('ไม่สามารถเข้าสู่ระบบ DMS ได้ กรุณาลองอีกครั้ง');return;}}var settled=false;var goHome=function(){{if(settled)return;settled=true;clearInterval(timer);try{{portal.location='{MRERP_HOME_URL}';status.textContent='เปิดระบบ DMS แล้ว';}}catch(error){{reset('ไม่สามารถเปิดหน้าหลัก DMS ได้ กรุณาลองอีกครั้ง');}}}};var tries=0;var timer=setInterval(function(){{if(settled)return;var landed=false;try{{portal.location.href;}}catch(error){{landed=true;}}if(landed){{setTimeout(goHome,400);}}else if(++tries>30){{goHome();}}}},400);}});}})();</script></body></html>"""
    return page, nonce
