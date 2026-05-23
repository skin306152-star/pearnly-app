# -*- coding: utf-8 -*-
"""
scripts/probe/probe-mrerp.py · MR.ERP 销项发票批量导入端到端探测

设计原则(CLAUDE.md 铁律 §7):
    - 仅走 Playwright 浏览器 UI · 严禁直接 POST endpoint
    - known-facts.md 的 URL 仅作"如果跳转到这就对了"的验证锚点
    - 凭据从 .env.local 读 · 不打印明文

入口:
    python scripts/probe/probe-mrerp.py            # headed 默认
    MRERP_HEADED=0 python scripts/probe/probe-mrerp.py  # headless

副产物:
    docs/integrations/screenshots/NN-step-name.png
    docs/integrations/templates/*.html / *.xlsx
"""

import os
import sys
import time
import logging
import re
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env.local")

from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout

# ============================================================
# 配置
# ============================================================
LOGIN_URL = (os.environ.get("MRERP_LOGIN_URL") or "").rstrip("/")
USERNAME = os.environ.get("MRERP_USERNAME") or ""
PASSWORD = os.environ.get("MRERP_PASSWORD") or ""
COMIDYEAR = os.environ.get("MRERP_COMIDYEAR") or "6"
SELDB = os.environ.get("MRERP_SELDB") or "1"
IDMENU_SC = os.environ.get("MRERP_IDMENU_SALES_CREDIT") or "370"
SELMENU_SC = os.environ.get("MRERP_SELMENU_SALES_CREDIT") or "118"

HEADED = (os.environ.get("MRERP_HEADED") or "1") != "0"
VIEWPORT = {"width": 1440, "height": 900}

DOCS_DIR = PROJECT_ROOT / "docs" / "integrations"
SCREENSHOTS_DIR = DOCS_DIR / "screenshots"
TEMPLATES_DIR = DOCS_DIR / "templates"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

TEST_INVOICE_NO = "PEARNLY-TEST-001"
# 2026-05-18 Zihao 手动建客户 "0006" / Skin Trading Co., Ltd.
# 客户码格式不是三段式 · 是公司自定义 4 位数字(见 known-facts §1 修订)
TEST_CUSTOMER_CODE = "0006"
TEST_CUSTOMER_NAME = "Skin Trading Co., Ltd."
TEST_RUN_ID = datetime.now().strftime("%Y%m%d-%H%M%S")


# ============================================================
# Logging · 凭据自动遮挡
# ============================================================
class CredStripFilter(logging.Filter):
    def filter(self, record):
        if not record.msg or not isinstance(record.msg, str):
            return True
        if PASSWORD and PASSWORD in record.msg:
            record.msg = record.msg.replace(PASSWORD, "***")
            record.args = None
        if USERNAME and USERNAME in record.msg and "user=" in record.msg.lower():
            # 用户名在调试上下文中遮一半
            record.msg = record.msg.replace(USERNAME, USERNAME[:2] + "***")
            record.args = None
        return True


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
)
log = logging.getLogger("probe-mrerp")
log.addFilter(CredStripFilter())


# ============================================================
# 截图 / 状态记录
# ============================================================
class ProbeState:
    def __init__(self):
        self.step = 0
        self.shots: List[Tuple[str, str]] = []  # [(filename, scenario)]
        self.findings: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.dialogs: List[str] = []  # JS alert/confirm 消息(实测发现 frmupload 用 alert 报错)

    def shot(self, page: Page, name: str, scenario: str = ""):
        self.step += 1
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-")
        fname = f"{self.step:02d}-{slug}.png"
        path = SCREENSHOTS_DIR / fname
        try:
            page.screenshot(path=str(path), full_page=True)
            self.shots.append((fname, scenario or name))
            log.info(f"📷 {fname}  {scenario}")
        except Exception as e:
            log.error(f"screenshot fail({fname}): {e}")
        return path

    def err_shot(self, page: Page, name: str, exc: BaseException):
        self.step += 1
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-")
        fname = f"{self.step:02d}-ERR-{slug}.png"
        path = SCREENSHOTS_DIR / fname
        try:
            page.screenshot(path=str(path), full_page=True)
            scenario = f"❌ {exc.__class__.__name__}: {exc}"
            self.shots.append((fname, scenario))
            self.errors.append(scenario)
            log.error(f"📷 {fname}  {scenario}")
        except Exception as inner:
            log.error(f"err_shot fail: {inner}")
        return path

    def manifest(self) -> str:
        lines = [f"# Probe run {TEST_RUN_ID}", ""]
        for fname, sc in self.shots:
            lines.append(f"{fname}\t{sc}")
        return "\n".join(lines)


STATE = ProbeState()


# ============================================================
# Step 1 · 预热 + 落地
# ============================================================
def step_01_landing(page: Page):
    log.info(f"→ STEP 01 · 预热 GET {LOGIN_URL}")
    page.goto(
        LOGIN_URL or "https://www.mrerp4sme.com/", wait_until="domcontentloaded", timeout=30000
    )
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except PWTimeout:
        log.warning("  networkidle 超时 · 继续")
    STATE.shot(page, "landing-marketing-page", f"GET / · URL={page.url}")
    STATE.findings["landing_url"] = page.url

    # 实测发现:站根目录是营销页 · 登录表单在 /login/login.php
    # 链接锚文本"เข้าสู่ระบบ" · href="login/login.php"
    log.info("  落地是营销页 · 进登录页")
    login_link = page.locator('a[href*="login.php"], a[href*="/login/"]').first
    if login_link.count() > 0:
        try:
            login_link.click(timeout=5000)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PWTimeout:
                pass
            log.info(f"  ✓ 点登录链接 → {page.url}")
            STATE.findings["login_nav_method"] = "click 'เข้าสู่ระบบ' link"
        except Exception as e:
            log.warning(f"  click 失败 ({e}) · fallback nav")
            page.goto(f"{LOGIN_URL}/login/login.php", wait_until="networkidle", timeout=15000)
            STATE.findings["login_nav_method"] = "direct nav (fallback)"
    else:
        page.goto(f"{LOGIN_URL}/login/login.php", wait_until="networkidle", timeout=15000)
        STATE.findings["login_nav_method"] = "direct nav (no link)"

    STATE.shot(page, "login-page", f"URL={page.url}")
    STATE.findings["login_page_url"] = page.url


# ============================================================
# Step 2 · 登录
# ============================================================
def step_02_login(page: Page):
    log.info("→ STEP 02 · 登录")
    user_in = page.locator('input[name="txtusers"]')
    pass_in = page.locator('input[name="txtpasswords"]')
    if user_in.count() == 0:
        STATE.shot(page, "login-form-missing", "input[name=txtusers] 不存在")
        raise RuntimeError("login form not found")
    user_in.first.fill(USERNAME)
    pass_in.first.fill(PASSWORD)
    STATE.shot(page, "login-filled", "登录表单已填(凭据已遮)")

    # 提交按钮 · 多 selector 兜底
    submit_sels = [
        'input[name="btnsubmit"]',
        'input[type="submit"]',
        'button[type="submit"]',
        'button:has-text("Submit")',
    ]
    clicked = False
    for sel in submit_sels:
        btn = page.locator(sel)
        if btn.count() > 0:
            try:
                btn.first.click(timeout=5000)
                clicked = True
                log.info(f"  点击提交({sel})")
                break
            except Exception as e:
                log.warning(f"  click {sel} 失败: {e}")
    if not clicked:
        pass_in.first.press("Enter")
        log.info("  无提交按钮 · 用 Enter 兜底")

    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except PWTimeout:
        pass
    STATE.shot(page, "post-login", f"提交后 · URL={page.url}")

    # 强化判定:必须有 logout 链接 OR 能访问 selectdb.php · 否则 = 失败
    url_low = page.url.lower()
    body_low = (page.content() or "")[:8000].lower()
    body_text = ""
    try:
        body_text = page.locator("body").inner_text(timeout=2000) or ""
    except Exception:
        pass

    # 失败信号(任一命中)
    failed = False
    if any(kw in url_low for kw in ["checklogin", "/login/index", "/login/?", "/login.php"]):
        if "txtusers" in body_low or "txtpasswords" in body_low:
            failed = True
    if url_low.rstrip("/").endswith("/index.php") or url_low.rstrip("/").endswith("mrerp4sme.com"):
        # 营销首页 = 没登进去
        if "เข้าสู่ระบบ" in body_text and "ออกจากระบบ" not in body_text:
            failed = True

    # 成功信号:有 logout / 在 selectdb / 在 mainmenu
    has_logout = "ออกจากระบบ" in body_text or "logout" in body_low
    in_protected = any(kw in url_low for kw in ["selectdb", "mainmenu", "impartran", "imparse"])

    if failed and not (has_logout or in_protected):
        STATE.shot(page, "login-failed", f"被踢回 {page.url}")
        STATE.findings["login_failed_url"] = page.url
        raise RuntimeError(f"login failed · 仍在公共区 · URL={page.url}")

    # 验证:试访问 selectdb.php · 看是否被踢回 login(double check)
    page.goto(f"{LOGIN_URL}/login/selectdb.php", wait_until="networkidle", timeout=10000)
    if "login.php" in page.url.lower() and "selectdb" not in page.url.lower():
        STATE.shot(page, "login-failed-bounce", f"访 selectdb 被踢 → {page.url}")
        raise RuntimeError(f"login failed (selectdb bounce) · URL={page.url}")

    STATE.shot(page, "post-login-verified", f"已认证 · URL={page.url}")
    STATE.findings["post_login_url"] = page.url
    log.info(f"  ✓ 登录成功 · 已到 {page.url}")


# ============================================================
# Step 3 · 选公司
# ============================================================
def step_03_select_company(page: Page):
    log.info(f"→ STEP 03 · 选公司(comidyear={COMIDYEAR}, seldb={SELDB})")
    # 先看页面上有没有 TEST2019 / company 选项 · 优先点击(纯 UI 路径)
    test2019 = page.get_by_text("TEST2019", exact=False)
    if test2019.count() > 0:
        try:
            test2019.first.click(timeout=5000)
            page.wait_for_load_state("networkidle", timeout=10000)
            STATE.shot(page, "company-clicked-TEST2019", f"点 TEST2019 · URL={page.url}")
            STATE.findings["company_select_method"] = "click TEST2019 button"
            return
        except Exception as e:
            log.warning(f"  click TEST2019 失败: {e}")

    # 兜底:浏览器 nav 到 mainmenu URL(仍是 page.goto · 不是 HTTP POST · 不违反 §7)
    target = f"{LOGIN_URL}/login/mainmenu.php?comidyear={COMIDYEAR}&seldb={SELDB}"
    log.info(f"  fallback nav: {target}")
    page.goto(target, wait_until="networkidle", timeout=15000)
    STATE.shot(page, "mainmenu-direct-nav", f"URL={page.url}")
    STATE.findings["company_select_method"] = "direct nav to mainmenu"


# ============================================================
# Step 4 · 进销项赊销批量导入
# ============================================================
def step_04_navigate_sc_import(page: Page):
    log.info(f"→ STEP 04 · 进 SC 批量导入(idmenu={IDMENU_SC})")
    # 优先:从主菜单点 menu(纯 UI)
    clicked = False
    for txt in ["ขายเชื่อ", "Sales (credit)", "Sales Credit", "销售-赊销", "นำเข้าข้อมูล"]:
        loc = page.get_by_text(txt, exact=False)
        if loc.count() > 0:
            try:
                loc.first.click(timeout=3000)
                page.wait_for_load_state("networkidle", timeout=10000)
                if "formupload" in page.url.lower() or "impartran" in page.url.lower():
                    clicked = True
                    log.info(f"  ✓ 菜单点 '{txt}' → URL={page.url}")
                    STATE.findings["sc_nav_method"] = f"click menu '{txt}'"
                    break
            except Exception as e:
                log.debug(f"  click '{txt}': {e}")
    if not clicked:
        # 兜底 nav 到已知 URL
        target = f"{LOGIN_URL}/impartran/formupload.php?idmenu={IDMENU_SC}"
        log.info(f"  fallback nav: {target}")
        page.goto(target, wait_until="networkidle", timeout=15000)
        STATE.findings["sc_nav_method"] = "direct nav (formupload.php?idmenu=370)"

    STATE.shot(page, "sc-import-form", f"URL={page.url}")
    STATE.findings["sc_import_url"] = page.url


# ============================================================
# Step 5 · 抓表单 + 找下载模板按钮
# ============================================================
def step_05_inspect_form(page: Page):
    log.info("→ STEP 05 · 抓表单结构")
    # 找下载模板按钮
    template_link = None
    template_sels = [
        'a[href*="template" i]',
        'a[href$=".xlsx"]',
        'a:has-text("ดาวน์โหลด")',
        'a:has-text("Template")',
        'a:has-text("ตัวอย่าง")',
        'button:has-text("Template")',
    ]
    for sel in template_sels:
        loc = page.locator(sel)
        if loc.count() > 0:
            try:
                href = loc.first.get_attribute("href") or "(no href)"
                template_link = href
                log.info(f"  📥 template link: {href}")
                break
            except Exception:
                pass

    # 抓 idus
    idus_el = page.locator('input[name="idus"]')
    idus_val = idus_el.first.get_attribute("value") if idus_el.count() > 0 else None

    # 抓 file input
    file_in = page.locator('input[type="file"], input[name="uploadfile"]')
    has_file_input = file_in.count() > 0

    # dump form HTML for analysis
    html_path = TEMPLATES_DIR / f"upload-form-{TEST_RUN_ID}.html"
    try:
        html_path.write_text(page.content(), encoding="utf-8")
        log.info(f"  📄 form HTML → {html_path.name}")
    except Exception as e:
        log.warning(f"  dump HTML 失败: {e}")

    STATE.findings.update(
        {
            "idus": idus_val,
            "has_file_input": has_file_input,
            "template_link": template_link,
            "form_html_dump": str(html_path),
        }
    )
    STATE.shot(page, "form-inspected", f"idus={idus_val} file_in={has_file_input}")


# ============================================================
# 工具 · 用 mrerp_xlsx_generator 构造测试 xlsx
# ============================================================
def build_test_xlsx() -> Tuple[bytes, str]:
    log.info("→ 构造测试 xlsx(monkey-patch invoice_no=PEARNLY-TEST-001)")
    import mrerp_xlsx_generator as gen

    original_derive = gen.derive_mrerp_invoice_no
    gen.derive_mrerp_invoice_no = lambda h: TEST_INVOICE_NO  # type: ignore

    try:
        test_history = {
            "client_id": 99,
            "invoice_number": TEST_INVOICE_NO,
            "invoice_date": "2026-05-18",
            "subtotal": "100.00",
            "vat": "7.00",
            "total_amount": "107.00",
            "items": [
                {
                    "name": f"PEARNLY TEST ITEM · {TEST_RUN_ID}",
                    "qty": 1,
                    "unit_price": 100.00,
                    "amount": 100.00,
                }
            ],
        }
        test_mappings = {
            "clients": [
                {
                    "erp_type": "mrerp",
                    "client_id": 99,
                    "erp_code": TEST_CUSTOMER_CODE,
                }
            ],
            "accounts": [],
            "taxes": [],
            "products": [],
        }
        xlsx_bytes = gen.generate_xlsx([test_history], test_mappings, sheet_kind="sales_credit")
        xlsx_path = TEMPLATES_DIR / f"test-invoice-{TEST_RUN_ID}.xlsx"
        xlsx_path.write_bytes(xlsx_bytes)
        log.info(f"  ✓ {len(xlsx_bytes)}B → {xlsx_path.name}")
        return xlsx_bytes, str(xlsx_path)
    finally:
        gen.derive_mrerp_invoice_no = original_derive


# ============================================================
# Step 6 · 上传 xlsx
# ============================================================
def step_06_upload(page: Page, xlsx_path: str):
    log.info("→ STEP 06 · 上传 xlsx")
    file_in = page.locator('input[type="file"], input[name="uploadfile"]')
    if file_in.count() == 0:
        STATE.shot(page, "upload-input-missing", "input[type=file] not found")
        raise RuntimeError("upload input not found")
    file_in.first.set_input_files(xlsx_path)
    STATE.shot(page, "file-chosen", f"已选 {Path(xlsx_path).name}")

    # 实测(2026-05-18) · MR.ERP 上传按钮是 type=button + onclick=frmupload()
    # 不是标准 type=submit · 必须明确 selector
    submit_sels = [
        'input[name="btnuploadfile"]',
        'input[id="btnuploadfile"]',
        'input[onclick*="frmupload"]',
        'input[value*="อัพโหลด"]',  # 注意:อัพโหลด(MR.ERP 拼写)≠ อัปโหลด(标准)
        'input[value*="อัปโหลด"]',
        'input[type="submit"]',
        'button[type="submit"]',
        'button:has-text("Upload")',
        'button:has-text("อัพโหลด")',
        'input[value*="Upload" i]',
    ]
    submitted = False
    for sel in submit_sels:
        btn = page.locator(sel)
        if btn.count() > 0:
            try:
                btn.first.click(timeout=5000)
                submitted = True
                log.info(f"  ✓ 提交上传({sel})")
                break
            except Exception as e:
                log.warning(f"  submit {sel} 失败: {e}")
    if not submitted:
        # 兜底:直接调 JS frmupload()(脚本里仍走浏览器 · 不是 HTTP RE)
        try:
            page.evaluate("typeof frmupload === 'function' && frmupload()")
            log.info("  ✓ JS frmupload() 兜底")
            submitted = True
        except Exception as e:
            log.warning(f"  JS frmupload 失败: {e}")

    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except PWTimeout:
        log.warning("  upload networkidle 超时")

    # 实测(2026-05-18)·frmupload() 走 AJAX · 上传成功后调 sdpt() 跳 formrdpc.php
    # 等待 URL 变化(成功)或检测 alert(失败 · 已挂全局 dialog handler)
    try:
        page.wait_for_url("**/formrdpc.php**", timeout=10000)
        log.info("  ✓ AJAX 成功 · 自动跳 formrdpc")
    except PWTimeout:
        log.warning(f"  ⚠ AJAX 没跳 formrdpc · 当前 URL={page.url}")
        if STATE.dialogs:
            log.warning(f"  alert 消息: {STATE.dialogs[-3:]}")
            STATE.findings["upload_alert_messages"] = list(STATE.dialogs)

    STATE.shot(page, "after-upload", f"URL={page.url}")
    STATE.findings["post_upload_url"] = page.url


# ============================================================
# Step 7 · preview + confirm
# ============================================================
def step_07_preview_confirm(page: Page, xlsx_path: str = ""):
    log.info("→ STEP 07 · preview + confirm + 抓 report.php")
    # 检测服务端 500(实测 probe 多次跑后服务端会 500 · 但 standalone 同 xlsx 200)
    # 重新触发整个 upload 链路(重新登录 + 重新上传)是最稳的 · 等上层重跑
    if "500 Internal Server Error" in (page.content() or "")[:1000]:
        log.warning("  ⚠ formrdpc.php 返 500")
        STATE.shot(page, "preview-500", "formrdpc 500 · 服务端临时错误")
        STATE.findings["preview_500"] = True
        # 试着 retry 一次:回到 formupload + 重 upload
        if xlsx_path and os.path.exists(xlsx_path):
            log.info("  等 45s 后 retry from formupload.php")
            time.sleep(45)
            try:
                page.goto(
                    f"{LOGIN_URL}/impartran/formupload.php?idmenu={IDMENU_SC}",
                    wait_until="networkidle",
                    timeout=15000,
                )
                page.locator('input[type="file"], input[name="uploadfile"]').first.set_input_files(
                    xlsx_path
                )
                page.locator('input[name="btnuploadfile"]').click()
                page.wait_for_url("**/formrdpc.php**", timeout=15000)
                log.info(f"  ✓ retry 后 URL={page.url}")
                if "500 Internal Server Error" in (page.content() or "")[:1000]:
                    log.error("  retry 后仍 500 · 放弃 step_07")
                    return {"success": False, "n_rows": 0, "reason": "preview_500_persistent"}
            except Exception as e:
                log.error(f"  retry 失败: {e}")
                return {"success": False, "n_rows": 0, "reason": f"retry_fail:{e}"}

    # 如果还没在 preview 页 · 找 preview 入口点
    if "formrdpc" not in page.url.lower():
        for sel in [
            'a:has-text("ดูข้อมูล")',
            'a:has-text("Preview")',
            'button:has-text("Preview")',
            'a:has-text("ตรวจสอบ")',
        ]:
            loc = page.locator(sel)
            if loc.count() > 0:
                try:
                    loc.first.click(timeout=5000)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    break
                except Exception as e:
                    log.warning(f"  preview click {sel}: {e}")

    STATE.shot(page, "preview-page", f"URL={page.url}")
    # sdpt 已经在 ctx.add_init_script 阶段全局 patch · 这里只验证

    # 错误关键词扫描(known-facts §9)
    try:
        body_text = page.locator("body").inner_text(timeout=3000) or ""
    except Exception:
        body_text = ""
    error_keywords = [
        "ไม่พบ",
        "ผิดพลาด",
        "ไม่ถูกต้อง",
        "ห้าม",
        "ซ้ำ",
        "error",
        "invalid",
        "duplicate",
        "fail",
    ]
    detected = [kw for kw in error_keywords if kw.lower() in body_text.lower()]
    if detected:
        log.warning(f"  ⚠ preview 上发现错误关键词: {detected}")
        STATE.findings["preview_error_keywords"] = detected

    # 数 cbimport 行
    cbs = page.locator('input[name^="cbimport["]')
    n = cbs.count()
    log.info(f"  preview 可勾行: {n}")
    STATE.findings["preview_row_count"] = n

    if n == 0:
        log.warning("  ⚠ preview 0 行 · xlsx 大概率被服务端拒")
        # 尝试抓红字 / alert 错误
        red_text = []
        try:
            for el in page.locator(
                'font[color="red"], span[style*="red"], div.error, .alert'
            ).all():
                t = el.inner_text() or ""
                if t.strip() and len(t) < 300:
                    red_text.append(t.strip())
        except Exception:
            pass
        if red_text:
            STATE.findings["preview_red_text"] = red_text
            log.warning(f"  red text: {red_text}")

        # dump preview HTML
        html_path = TEMPLATES_DIR / f"preview-empty-{TEST_RUN_ID}.html"
        try:
            html_path.write_text(page.content(), encoding="utf-8")
        except Exception:
            pass
        STATE.shot(page, "preview-empty", f"0 行 · err={detected or red_text}")
        return {"success": False, "n_rows": 0, "errors": detected, "red_text": red_text}

    # 勾选 + 确认
    for i in range(n):
        cb = cbs.nth(i)
        try:
            if not cb.is_checked():
                cb.check()
        except Exception:
            pass
    STATE.shot(page, "preview-checked", f"勾 {n} 行")

    # 先勾全选(cballfrmimportN · 每个 form 一个)
    for ball in page.locator('input[name^="cballfrmimport"]').all():
        try:
            if not ball.is_checked():
                ball.check()
        except Exception:
            pass

    # 实测(2026-05-18) · 优先用 page.evaluate('uploadfrm(N)') 触发
    # 因为 click btnuploadfrm 后 button detach · click 等 navigation 超时
    # 直接 JS 调用避开 locator 同步问题
    confirmed_count = 0
    try:
        # 探测有几个 form
        form_count = page.locator('form[id^="frmimport"]').count()
        log.info(f"  发现 {form_count} 个 frmimportN form")
        for fid in range(1, form_count + 1):
            try:
                page.evaluate(f"uploadfrm({fid})")
                confirmed_count += 1
                log.info(f"  ✓ uploadfrm({fid}) JS 调用")
            except Exception as e:
                log.warning(f"  uploadfrm({fid}) JS 失败: {e}")
    except Exception as e:
        log.warning(f"  JS evaluate 路径失败: {e} · 兜底 click")
        for sel in [
            'button[id^="btnuploadfrm"]',
            'button[onclick^="uploadfrm("]',
            'button:has-text("นำเข้าข้อมูล")',
        ]:
            btns = page.locator(sel).all()
            for btn in btns:
                try:
                    btn.click(timeout=5000, no_wait_after=True)
                    confirmed_count += 1
                    log.info(f"  ✓ 点确认({sel})")
                except Exception as e2:
                    log.warning(f"  confirm {sel} 失败: {e2}")
            if confirmed_count > 0:
                break

    # 关键 · sdpt patched 成 _self · confirm 成功后会自动跳 report.php
    report_captured = False
    try:
        page.wait_for_url("**/report.php**", timeout=12000)
        log.info(f"  ✓ 自动跳 report.php · URL={page.url}")
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except PWTimeout:
            pass
        report_html = page.content()
        report_html_path = TEMPLATES_DIR / f"import-report-{TEST_RUN_ID}.html"
        report_html_path.write_text(report_html, encoding="utf-8")
        log.info(f"  📄 report HTML → {report_html_path.name}")
        report_captured = True
        STATE.findings["report_html"] = str(report_html_path)
        # 找文件下载链接(MR.ERP 实测可能给 xlsx 报告下载)
        try:
            body_text = page.locator("body").inner_text(timeout=3000) or ""
            STATE.findings["report_body_preview"] = body_text[:1500]
        except Exception:
            pass
        STATE.shot(page, "import-report", f"成功跳 report · URL={page.url}")
    except PWTimeout:
        log.warning(f"  ⚠ 没跳 report.php · 当前 URL={page.url}")

    STATE.shot(
        page,
        "after-confirm",
        f"clicks={confirmed_count} · URL={page.url} · dialogs={STATE.dialogs[-2:] if STATE.dialogs else []}",
    )
    STATE.findings["confirm_clicked_count"] = confirmed_count
    STATE.findings["report_captured"] = report_captured
    if STATE.dialogs:
        STATE.findings["confirm_dialogs"] = list(STATE.dialogs[-5:])
    return {
        "success": confirmed_count > 0,
        "n_rows": n,
        "confirmed_count": confirmed_count,
        "report_captured": report_captured,
    }


# ============================================================
# Step 8 · 回主菜单 · 探索列表页 · 搜 PEARNLY-TEST
# ============================================================
def step_08_search_listing(page: Page):
    """实测(2026-05-18) · SC 列表页 = /artran/allview.php?idmenu=118
    路径模式:`<module>/allview.php?idmenu=N` · 跟 impartran 批量导入不同

    重要:**不要用 search filter** · search 后 listing 会按"编号/日期/客户名/金额"过滤
    但 row 显示的是 bill_no(SIPEARNLY-TEST-001) · 不是 invoice_no(PEARNLY-TEST-001)
    用 search PEARNLY-TEST 时,服务端模糊匹配可能命中(SIPEARNLY 是 PEARNLY 子串)·
    但我们直接看 listing top row 更稳(import 后 row 按日期 desc 排序在最顶)"""
    log.info("→ STEP 08 · 进 SC 列表 + 找 PEARNLY row(不用 search · 直接 inner_text 扫)")
    list_url = f"{LOGIN_URL}/artran/allview.php?idmenu=118&mode=l"
    log.info(f"  nav: {list_url}")
    page.goto(list_url, wait_until="networkidle", timeout=15000)
    STATE.findings["list_url"] = page.url

    # dump listing HTML (诊断用)
    list_html = TEMPLATES_DIR / f"sc-listing-{TEST_RUN_ID}.html"
    try:
        list_html.write_text(page.content(), encoding="utf-8")
    except Exception:
        pass

    STATE.shot(page, "sc-listing-page", f"URL={page.url}")

    # 在 row HTML 而非 search input value 里找 PEARNLY
    # listing row 用 `<p><span>SIPEARNLY-TEST-001</span><span>18/05/2569</span>...<a href="allform.php?id=N&status=del"></a>`
    # 抓 SIPEARNLY... row 的 delete 链接 id
    html = page.content() or ""
    bill_no = f"SI{TEST_INVOICE_NO}"  # generator 自动 SI 前缀
    test_db_id: Optional[str] = None
    import re as _re

    # find row containing bill_no
    p_pattern = _re.compile(
        r"<p\b[^>]*>(?:(?!</p>).){0,3000}"
        + _re.escape(bill_no)
        + r'(?:(?!</p>).){0,3000}allform\.php\?id=(\d+)&[^"]*status=del',
        _re.DOTALL,
    )
    m = p_pattern.search(html)
    if m:
        test_db_id = m.group(1)
        log.info(f"  ✓ 找到 row · db_id={test_db_id}")
    else:
        # fallback · 任意 PEARNLY+del id pattern
        m2 = _re.search(
            r'PEARNLY-TEST.{0,2000}allform\.php\?id=(\d+)&[^"]*status=del', html, _re.DOTALL
        )
        if m2:
            test_db_id = m2.group(1)
            log.info(f"  fallback ✓ db_id={test_db_id}")

    STATE.findings["found_in_listing"] = test_db_id is not None
    STATE.findings["test_db_id"] = test_db_id
    STATE.shot(
        page,
        "search-result",
        f"row found · db_id={test_db_id}" if test_db_id else "PEARNLY row NOT in listing",
    )
    return test_db_id is not None


# ============================================================
# Step 9 · 删除测试数据
# ============================================================
def step_09_delete(page: Page):
    """实测(2026-05-18) · 删除流程 = 2 步:
    1. nav 到 allform.php?id=N&status=del(打开删除前确认页 · 不真删)
    2. 点 #btndel 按钮(触发 confirmdel(N) JS + 弹 confirm dialog)
    3. dialog accept(已挂全局 handler)→ POST 真删 + 跳 allview.php"""
    log.info("→ STEP 09 · 删除测试数据")
    test_db_id = STATE.findings.get("test_db_id")
    if not test_db_id:
        STATE.shot(page, "delete-no-id", "step_08 没拿到 db_id · 无法删除")
        log.warning("  ⚠ 没 db_id · 跳过删除")
        return False

    del_form_url = f"{LOGIN_URL}/artran/allform.php?id={test_db_id}&status=del"
    log.info(f"  nav 删除前确认页: {del_form_url}")
    try:
        page.goto(del_form_url, wait_until="networkidle", timeout=15000)
        STATE.shot(page, "delete-form-page", f"URL={page.url}")
        # 点 btndel(触发 confirmdel JS + 弹 confirm dialog)
        del_btn = page.locator('button[id="btndel"]')
        if del_btn.count() == 0:
            STATE.shot(page, "delete-btn-missing", "btndel 不存在")
            log.warning("  ⚠ btndel 按钮不存在")
            return False
        del_btn.first.click(timeout=5000)
        page.wait_for_timeout(3000)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except PWTimeout:
            pass
        STATE.shot(page, "after-delete", f"URL={page.url}")
        log.info(f"  ✓ 点 btndel · URL={page.url}")
        return True
    except Exception as e:
        log.warning(f"  delete 失败: {e}")
        STATE.shot(page, "delete-failed", str(e))
        return False


# ============================================================
# Step 10 · 再次搜索 · 确认已删
# ============================================================
def step_10_verify_deletion(page: Page):
    log.info("→ STEP 10 · 验证已删除")
    # 进 listing(不 reload · 直接 nav 拿 fresh state)
    list_url = f"{LOGIN_URL}/artran/allview.php?idmenu=118&mode=l"
    page.goto(list_url, wait_until="networkidle", timeout=15000)
    html = page.content() or ""
    # 在 HTML 而非 inner_text 里搜 SIPEARNLY 或 PEARNLY-TEST(避开 search input 的 false positive)
    bill_no = f"SI{TEST_INVOICE_NO}"
    still_in_rows = (bill_no in html) or (
        TEST_INVOICE_NO in html and "searchdataval" not in html.split(TEST_INVOICE_NO)[0][-300:]
    )
    log.info(f"  删除后 listing 仍含 SIPEARNLY? {still_in_rows}")
    STATE.findings["deletion_verified"] = not still_in_rows
    STATE.shot(
        page,
        "verify-deletion",
        "✅ 删除成功 · listing 不含 PEARNLY" if not still_in_rows else "⚠ listing 仍含 PEARNLY",
    )
    return not still_in_rows


# ============================================================
# Main
# ============================================================
def main() -> int:
    if not (LOGIN_URL and USERNAME and PASSWORD):
        log.error("缺凭据 · 检查 .env.local(MRERP_LOGIN_URL / USERNAME / PASSWORD)")
        return 2

    log.info("=" * 60)
    log.info(f"🚀 MR.ERP probe · run_id={TEST_RUN_ID}")
    log.info(f"   target: {LOGIN_URL}")
    log.info(f"   user: {USERNAME[:2]}*** (password 已遮)")
    log.info(f"   mode: {'headed (1440x900)' if HEADED else 'headless'}")
    log.info("=" * 60)

    # 先离线构 xlsx · 快失败
    try:
        xlsx_bytes, xlsx_path = build_test_xlsx()
    except Exception as e:
        log.error(f"xlsx 构造失败: {e}")
        STATE.errors.append(f"xlsx_build: {e}")
        traceback.print_exc()
        return 3

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not HEADED, slow_mo=150 if HEADED else 0)
        ctx = browser.new_context(viewport=VIEWPORT, locale="th-TH")

        # 实测(2026-05-18) · 上下文级 init script 在每个 page load 后自动 patch sdpt
        # 把 _blank 改 _self · 让 report.php 在同 page 加载 · Playwright 直接抓
        # 比 step_07 临时 patch 更稳(避免 timing race)
        ctx.add_init_script("""
            (function() {
                var patched = false;
                function tryPatch() {
                    if (patched) return;
                    if (typeof window.sdpt === 'function') {
                        var orig = window.sdpt;
                        window.sdpt = function(objval, actionval, targetval) {
                            console.log('SDPT_PATCHED', actionval);
                            return orig(objval, actionval, '_self');
                        };
                        patched = true;
                    }
                }
                if (document.readyState === 'complete') tryPatch();
                else {
                    window.addEventListener('load', tryPatch);
                    document.addEventListener('DOMContentLoaded', tryPatch);
                }
                // 兜底:200ms 后 retry(jQuery $(document).ready 可能晚于 load)
                setTimeout(tryPatch, 200);
                setTimeout(tryPatch, 800);
            })();
        """)

        page = ctx.new_page()

        # 全局 dialog handler · 抓所有 JS alert/confirm
        # 实测发现:frmupload() 失败时用 alert(error_msg) 报错 · 不挂会丢信息
        def _on_dialog(d):
            msg = (d.message or "")[:500]
            log.info(f"  💬 dialog ({d.type}): {msg}")
            STATE.dialogs.append(f"[{d.type}] {msg}")
            try:
                d.accept()
            except Exception:
                pass

        page.on("dialog", _on_dialog)

        fatal: Optional[BaseException] = None
        try:
            step_01_landing(page)
            step_02_login(page)
            step_03_select_company(page)
            step_04_navigate_sc_import(page)
            step_05_inspect_form(page)
            step_06_upload(page, xlsx_path)
            confirm = step_07_preview_confirm(page, xlsx_path=xlsx_path)
            STATE.findings["confirm_result"] = confirm

            if confirm.get("success") and confirm.get("n_rows", 0) > 0:
                found = step_08_search_listing(page)
                if found:
                    deleted = step_09_delete(page)
                    STATE.findings["delete_clicked"] = deleted
                    if deleted:
                        step_10_verify_deletion(page)
                else:
                    log.warning("  搜索未命中 · 跳过删除")
            else:
                log.warning("  preview 失败 · 跳过搜索/删除")
        except BaseException as e:
            fatal = e
            log.error(f"❌ FATAL: {e}")
            STATE.err_shot(page, "fatal", e)
            traceback.print_exc()
        finally:
            if HEADED:
                log.info("  headed mode · 留 5s 让你看最后状态")
                time.sleep(5)
            try:
                ctx.close()
                browser.close()
            except Exception:
                pass

        # 写 screenshot 清单 + findings JSON
        try:
            (SCREENSHOTS_DIR / "manifest.txt").write_text(STATE.manifest(), encoding="utf-8")
            import json

            findings_path = DOCS_DIR / f"probe-findings-{TEST_RUN_ID}.json"
            findings_path.write_text(
                json.dumps(
                    {
                        "run_id": TEST_RUN_ID,
                        "findings": STATE.findings,
                        "errors": STATE.errors,
                        "shots": [{"file": f, "scenario": s} for f, s in STATE.shots],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            log.info(f"📋 findings → {findings_path.name}")
        except Exception as e:
            log.warning(f"manifest/findings 写盘失败: {e}")

        if fatal:
            return 1
        return 0


if __name__ == "__main__":
    sys.exit(main())
