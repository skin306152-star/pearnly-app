# -*- coding: utf-8 -*-
"""
scripts/probe/probe-dms.py · MR.ERP DMS 汽车销售 身份证→订车单 端到端探测

设计原则(CLAUDE.md 铁律 §7):
    - 仅走 Playwright 浏览器 UI · endpoint 仅作"跳到这就对了"的锚点
    - 凭据从 env 读 · 绝不打印明文 · 绝不写进脚本

入口:
    $env:DMS_LOGIN_URL="https://www.mrerp4sme.com/dms/index.php"
    $env:DMS_USERNAME="..."; $env:DMS_PASSWORD="..."
    python scripts/probe/probe-dms.py

副产物(本地 scratch · 不 commit):
    _dms_probe/NN-step.png / *.html
"""

import os
import sys
import json
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout  # noqa: E402
from services.erp._browser import SDPT_INIT_SCRIPT  # noqa: E402

RAW_URL = (os.environ.get("DMS_LOGIN_URL") or "").rstrip("/")
# base = everything up to and including /dms/
BASE = RAW_URL.rsplit("/", 1)[0] + "/" if RAW_URL.endswith(".php") else RAW_URL + "/"
USERNAME = os.environ.get("DMS_USERNAME") or ""
PASSWORD = os.environ.get("DMS_PASSWORD") or ""

OUT = PROJECT_ROOT / "_dms_probe"
OUT.mkdir(parents=True, exist_ok=True)


class CredStrip(logging.Filter):
    def filter(self, record):
        if isinstance(record.msg, str):
            for s in (PASSWORD, USERNAME):
                if s and s in record.msg:
                    record.msg = record.msg.replace(s, "***")
                    record.args = None
        return True


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("probe-dms")
log.addFilter(CredStrip())

_n = [0]


def snap(page, name):
    _n[0] += 1
    p = OUT / f"{_n[0]:02d}-{name}.png"
    try:
        page.screenshot(path=str(p), full_page=True)
        log.info("shot %s", p.name)
    except Exception as e:
        log.warning("snap %s failed: %s", name, e)


def dump_html(page, name):
    p = OUT / f"{_n[0]:02d}-{name}.html"
    try:
        p.write_text(page.content(), encoding="utf-8")
        log.info("html %s (%d bytes)", p.name, p.stat().st_size)
    except Exception as e:
        log.warning("dump %s failed: %s", name, e)


def list_inputs(page):
    """Return [(tag, name, type, id)] for every form control on the page."""
    return page.evaluate(
        """() => Array.from(document.querySelectorAll('input,select,textarea')).map(el => ({
            tag: el.tagName.toLowerCase(),
            name: el.getAttribute('name') || '',
            type: el.getAttribute('type') || '',
            id: el.id || '',
            placeholder: el.getAttribute('placeholder') || ''
        }))"""
    )


def main():
    if not (RAW_URL and USERNAME and PASSWORD):
        log.error("set DMS_LOGIN_URL / DMS_USERNAME / DMS_PASSWORD env first")
        return 2
    log.info("RAW_URL=%s  BASE=%s", RAW_URL, BASE)
    report = {"base": BASE, "raw_url": RAW_URL}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        ctx = browser.new_context(locale="th-TH", viewport={"width": 1440, "height": 900}, accept_downloads=True)
        ctx.add_init_script(SDPT_INIT_SCRIPT)  # make sdpt(_blank) navigations same-tab + observable
        page = ctx.new_page()
        page.on("dialog", lambda d: (log.info("dialog[%s]: %s", d.type, (d.message or "")[:200]), d.accept()))

        # 1. login page
        page.goto(RAW_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(1500)
        snap(page, "login")
        dump_html(page, "login")
        login_inputs = list_inputs(page)
        report["login_inputs"] = login_inputs
        log.info("login inputs: %s", json.dumps(login_inputs, ensure_ascii=False))

        # 2. attempt login — fill the lab-known field names, fall back to first text/password input
        filled = {"user": False, "pass": False}
        for sel in ['input[name="txtusers"]', 'input[name="username"]', 'input[type="text"]']:
            try:
                if page.query_selector(sel):
                    page.fill(sel, USERNAME)
                    filled["user"] = True
                    log.info("filled user via %s", sel)
                    break
            except Exception:
                pass
        for sel in ['input[name="txtpasswords"]', 'input[name="password"]', 'input[type="password"]']:
            try:
                if page.query_selector(sel):
                    page.fill(sel, PASSWORD)
                    filled["pass"] = True
                    log.info("filled pass via %s", sel)
                    break
            except Exception:
                pass
        report["login_filled"] = filled

        # submit: the login button is <input type="button" id="btnlogin"> whose
        # JS handler does formAjax(login/checklogin.php) then sdpt(...) to navigate.
        submitted = False
        for sel in ['#btnlogin', 'input[name="btnlogin"]', 'button']:
            try:
                el = page.query_selector(sel)
                if el:
                    el.click()
                    submitted = True
                    log.info("clicked login via %s", sel)
                    break
            except Exception:
                pass
        report["login_submitted"] = submitted
        # wait for the post-login navigation (home/home.php or login/selcomdb.php)
        try:
            page.wait_for_url(lambda u: "index.php" not in u, timeout=15000)
        except Exception:
            log.warning("no nav away from index.php within 15s")
        page.wait_for_timeout(2500)
        snap(page, "after-login")
        dump_html(page, "after-login")
        report["after_login_url"] = page.url
        log.info("after login url=%s", page.url)

        # 3. probe key pages by direct GET (PHP apps usually allow it once authed)
        for path, name in [
            ("cus/form.php?status=n", "cus-form-new"),
            ("impcarbookcon/formupload.php", "imp-formupload"),
            ("drfcbc/form.php?status=n", "drfcbc-form-new"),
            ("drfcbc/component/showdata.php", "drfcbc-showdata"),
        ]:
            try:
                page.goto(BASE + path, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1200)
                snap(page, name)
                dump_html(page, name)
                report[f"{name}_url"] = page.url
                report[f"{name}_inputs"] = list_inputs(page)
                log.info("%s url=%s inputs=%d", name, page.url, len(report[f"{name}_inputs"]))
            except Exception as e:
                log.warning("probe %s failed: %s", name, e)
                report[f"{name}_error"] = str(e)[:300]

        # 4. download official booking template
        try:
            tpl = ctx.request.get(BASE + "impcarbookcon/example.xlsx")
            body = tpl.body()
            if body[:2] == b"PK":
                (OUT / "booking-template.xlsx").write_bytes(body)
                report["template_bytes"] = len(body)
                log.info("template ok %d bytes", len(body))
            else:
                report["template_head"] = body[:80].decode("latin1", "replace")
                log.warning("template not a zip: %s", report["template_head"])
        except Exception as e:
            log.warning("template dl failed: %s", e)
            report["template_error"] = str(e)[:300]

        # 5. master data lists (authenticated ctx.request shares cookies)
        masters = {}
        for elem in ("txtusers", "txtcar", "txtcarpaint", "txtplacebook", "txttermsale",
                     "txtbranch_book", "txtteam_book", "txtregisbehalf", "selprefix"):
            try:
                r = ctx.request.post(
                    BASE + "drfcbc/component/bshsd.php",
                    form={"bshsdamt": "10", "bshsdcurrpage": "1", "elemname": elem, "sdt": ""},
                )
                txt = r.text()
                masters[elem] = txt[:600]
                log.info("master %s -> %s", elem, txt[:120].replace("\n", " "))
            except Exception as e:
                masters[elem] = f"ERR {str(e)[:120]}"
        report["masters"] = masters

        ctx.close()
        browser.close()

    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("wrote %s", OUT / "report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
