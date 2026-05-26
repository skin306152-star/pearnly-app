"""只读探测 · MR.ERP armas/allview.php 客户列表的『30 行以外』翻页机制。

授权:Zihao 2026-05-26 本轮授权用 test01/test01 · TEST2019 · 纯读不改数据。
目的:搞清 picker 下拉(/endpoints/{id}/customers)为何只返 ~30 条 ·
      allview.php 怎么暴露第 31+ 条客户(分页控件 / showdata.php 参数 / 滚动)。
跑法:python scripts/probe/probe-listing-pagination.py
输出:scripts/probe/_debug/listing_*.{html,png,txt}
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows GBK console → 打印泰文
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.erp.mrerp_adapter import MRERPAdapter  # noqa: E402
from services.erp.mrerp_customer_sync import parse_armas_listing  # noqa: E402

OUT = Path(__file__).parent / "_debug"
OUT.mkdir(parents=True, exist_ok=True)

LOGIN_URL = os.environ.get("MRERP_LOGIN_URL", "https://www.mrerp4sme.com")
USER = os.environ.get("MRERP_USERNAME", "test01")
PWD = os.environ.get("MRERP_PASSWORD", "test01")
COMIDYEAR = os.environ.get("MRERP_COMIDYEAR", "6")
SELDB = os.environ.get("MRERP_SELDB", "1")


def dump(name: str, text: str):
    p = OUT / name
    p.write_text(text, encoding="utf-8")
    print(f"  wrote {p} ({len(text)} chars)")


def main():
    adapter = MRERPAdapter(
        login_url=LOGIN_URL,
        username=USER,
        password=PWD,
        comidyear=COMIDYEAR,
        seldb=SELDB,
        headless=True,
        retry_attempts=2,
        retry_delays_seconds=(1.0, 5.0),
        serialize_sessions=False,  # 探测脚本不连 DB · 跳过跨进程会话锁
    )
    with adapter:
        adapter.select_company()
        page = adapter._page
        url = adapter.login_url + "/armas/allview.php"
        print(f"[1] goto {url}")
        page.goto(url, wait_until="networkidle", timeout=30_000)
        try:
            page.wait_for_selector("#showdata p", state="attached", timeout=30_000)
        except Exception as e:
            print(f"  wait_for_selector failed: {e}")
        page.wait_for_timeout(1500)

        html = page.content() or ""
        dump("listing_initial.html", html)
        page.screenshot(path=str(OUT / "listing_initial.png"), full_page=True)

        rows = parse_armas_listing(html)
        print(f"[2] parse_armas_listing → {len(rows)} rows")
        print(f"    first codes: {[r.code for r in rows[:3]]}")
        print(f"    last  codes: {[r.code for r in rows[-3:]]}")

        # #showdata p 真实数量(含 header)
        n_p = page.locator("#showdata p").count()
        print(f"[3] #showdata p count = {n_p}")

        # ---- 找翻页线索 ----
        print("[4] 翻页线索搜索:")
        for kw in ["showdata.php", "searchdata", "loadpage", "pagenum", "page=",
                   "limit", "offset", "pagination", "pager", "หน้า", "next",
                   "showmore", "loadmore", "rows", "perpage", "page_size"]:
            n = html.lower().count(kw.lower())
            if n:
                print(f"    '{kw}' × {n}")

        # 抽出所有 <script> 内含 showdata/searchdata 的片段
        scripts = re.findall(r"<script\b[^>]*>(.*?)</script>", html, re.DOTALL | re.I)
        js_hits = []
        for s in scripts:
            if re.search(r"showdata|searchdata|allview|loadpage|pagin", s, re.I):
                js_hits.append(s.strip())
        dump("listing_scripts.txt", "\n\n===SCRIPT===\n\n".join(js_hits) if js_hits
             else "(no matching inline scripts)")

        # 外部 js 引用
        ext_js = re.findall(r'<script\b[^>]*src=["\']([^"\']+)["\']', html, re.I)
        print(f"[5] external scripts: {ext_js}")

        # 列表区附近(showdata 之后)是否有 pager 控件 → 抽 #showdata 之后 2KB
        idx = html.lower().find('id="showdata"')
        if idx < 0:
            idx = html.lower().find("id='showdata'")
        if idx >= 0:
            tail = html[idx: idx + 4000]
            dump("listing_showdata_region.html", tail)

        # ---- 验证真分页:POST /armas/component/showdata.php(showdata.js 实证)----
        print("[6] POST component/showdata.php 分页验证:")
        ep = adapter.login_url + "/armas/component/showdata.php"
        all_codes = []
        for pg in range(1, 60):  # 上限 60 页 = 1800 行 · 防死循环
            try:
                resp = page.request.post(
                    ep,
                    form={
                        "showdata_numrows": "30",
                        "showdata_pages": str(pg),
                        "searchdataval": "",
                    },
                )
                body = resp.text() or ""
            except Exception as e:
                print(f"    page {pg} → ERR {type(e).__name__}: {str(e)[:120]}")
                break
            sub = parse_armas_listing(body)
            has_p = "<p>" in body.lower()
            has_nodata = 'id="nodata"' in body.lower()
            print(f"    page {pg} → HTTP {resp.status} · parsed {len(sub)} · "
                  f"has<p>={has_p} nodata={has_nodata} · {len(body)} chars")
            if pg == 1:
                dump("showdata_post_page1.html", body)
            all_codes += [r.code for r in sub]
            # showdata.js 终止条件:无 <p> 且无 nodata → pages=0 停
            if not (has_p or has_nodata) or len(sub) == 0:
                print("    → 终止(无更多行)")
                break
        uniq = list(dict.fromkeys(all_codes))
        print(f"[7] 分页累计:{len(all_codes)} 行 · 去重 {len(uniq)} 个唯一 code")

        print("\n[done] 看 scripts/probe/_debug/ 下的产物。")


if __name__ == "__main__":
    main()
