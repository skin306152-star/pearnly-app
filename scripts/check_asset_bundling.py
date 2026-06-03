#!/usr/bin/env python3
"""前端打包机械闸(防 view-source 退化 + 打包漏项 · 铁律#27 防屎山 · E7 打包机制守门)。

未来窗口改 UI / 加 CSS-JS 时,不靠读文档自觉,靠这道闸拦下并告知怎么做:

  闸②  源页只引 bundle:home.html / login.html / admin.html 的 stylesheet link 必须指向
        static/dist/ bundle,script src 必须是 dist/ 或白名单。直接 link 单个 home-*.css /
        landing/*.js = view-source 退化,拦。
  闸③  清单完整:static 下的 home-*.css 与 landing/* 资产必须都在 build-home-{css,js}.mjs
        的打包清单里。新增文件忘了加清单 = 不进 bundle 样式丢,拦。

(闸① 打包一致性 = CI/pre-push 跑 `npm run build` 后 `git diff --exit-code static/dist/`,
 不在本脚本 · 那道堵"改源忘重新打包"。)

用法: python scripts/check_asset_bundling.py   (exit 1 = 有违规)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 源 HTML 里允许的非 dist 资产白名单(数据文件 / 第三方 CDN / favicon 不是 link[stylesheet])
SCRIPT_WHITELIST = (
    "/static/dist/",
    "/static/i18n-data.js",  # 715KB 纯数据 · 故意独立 · 见 build-home-js.mjs 注释
    "/static/admin/",  # admin SPA 专属 JS · 超管页防抄需求低 · 故意留独立(同 admin.html 不 minify)
    "cdnjs.cloudflare.com",  # jsPDF
    "cloudflareinsights.com",  # CF beacon(部署注入)
)
SOURCE_HTML = ["home.html", "login.html", "static/admin/admin.html"]


def check_source_html(fails):
    for rel in SOURCE_HTML:
        p = ROOT / rel
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8")
        for m in re.finditer(r'<link[^>]*rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)', html):
            href = m.group(1)
            if not href.startswith("/static/dist/"):
                fails.append(
                    f"{rel}: 明文 stylesheet `{href}` — 新 CSS 要加进 "
                    f"scripts/build-home-css.mjs 的清单,别直接 <link>(否则 view-source 退化)"
                )
        for m in re.finditer(r'<script[^>]*src=["\']([^"\']+)', html):
            src = m.group(1)
            if not any(w in src for w in SCRIPT_WHITELIST):
                fails.append(
                    f"{rel}: 明文 script `{src}` — 新 JS 要加进 "
                    f"scripts/build-home-js.mjs 的清单,别直接 <script src>"
                )


def manifest(script_name):
    """从 build-*.mjs 提取打包清单里的 css/js 文件名(含 landing/ 前缀)。"""
    s = (ROOT / "scripts" / script_name).read_text(encoding="utf-8")
    return set(re.findall(r"""['"]([\w./-]+\.(?:css|js))['"]""", s))


def check_manifest_complete(fails):
    css_manifest = manifest("build-home-css.mjs")
    js_manifest = manifest("build-home-js.mjs")

    for f in (ROOT / "static").glob("home-*.css"):
        if f.name not in css_manifest:
            fails.append(
                f"static/{f.name}: 不在 build-home-css.mjs 清单 — "
                f"新增 home CSS 要加进 HOME_CSS 或 ADMIN_CSS 数组(否则不进 bundle)"
            )
    landing = ROOT / "static" / "landing"
    if landing.exists():
        for f in landing.glob("*.css"):
            if f"landing/{f.name}" not in css_manifest:
                fails.append(
                    f"static/landing/{f.name}: 不在 build-home-css.mjs 的 LANDING_CSS — 加进去"
                )
        for f in landing.glob("*.js"):
            if f"landing/{f.name}" not in js_manifest:
                fails.append(
                    f"static/landing/{f.name}: 不在 build-home-js.mjs 的 landing files — 加进去"
                )


def main():
    fails = []
    check_source_html(fails)
    check_manifest_complete(fails)

    print("=" * 70)
    print("前端打包机械闸(view-source 不退化 + 打包不漏项)")
    print("=" * 70)
    if fails:
        for f in fails:
            print(f"  [X] {f}")
        print(f"\n结果: FAIL - {len(fails)} 处违规")
        return 1
    print("结果: PASS - 源页只引 bundle, 资产全在打包清单")
    return 0


if __name__ == "__main__":
    sys.exit(main())
