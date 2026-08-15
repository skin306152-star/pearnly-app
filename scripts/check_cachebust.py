#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/check_cachebust.py · 缓存破机械闸(2026-07-10 血泪事故固化)。

真实事故:改了 static/dist/main.js 却没 bump home.html 里的 `dist/main.js?v=`,CDN 的
`immutable` 30 天缓存让 prod 一直吃旧 bundle,改动"上线了却没生效",返工一轮才根治。

本闸:一个 commit range 内,若打包产物变了,引用它的源 HTML 的 `?v=` 指纹必须也变,否则
非零退出并打人话——把"忘了 bump ?v"从人肉自觉变成 CI 红线。

两张监控清单:
  CACHE_BUST_PAIRS —— HTML 里写死引用的产物,产物变则查它自己的 ?v(覆盖主站 / 超管 /
                      门户 / DMS / AI 五个入口);
  CACHE_BUST_DIRS  —— 运行时 fetch、URL 由 JS 现拼的目录产物,指纹是借别人的(见该常量注释)。
**新增任何带 ?v= 的对外产物必须同步加一行** —— 漏一行,闸就在它没覆盖的地方安静地绿着
(已犯三次:2026-07-23 ai.js、2026-07-25 home.css、2026-07-26 教程 JSON)。

用法:
  python scripts/check_cachebust.py                                   # 默认 HEAD~1..HEAD
  python scripts/check_cachebust.py --base origin/master --head HEAD  # PR 全 diff

退出码:0 = 无违规(或产物没变,无需检查);1 = 产物变了但源 HTML 指纹没 bump。
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class CacheBustPair(NamedTuple):
    """一对「打包产物 ↔ 引用它的源 HTML + HTML 里 ?v= 前的路径片段」。"""

    bundle: str  # 产物路径(git 路径 · 正斜杠)
    html: str  # 源 HTML 路径
    ref: str  # 源 HTML 中该产物的引用片段(?v= 之前那段)


class CacheBustDir(NamedTuple):
    """一组「目录产物 ↔ 它借用的那个 ?v」—— 与 CacheBustPair 的映射方向不同,见下方注释。"""

    prefix: str  # 目录前缀(git 路径 · 正斜杠 · 结尾带 /)
    html: str  # 借指纹的源 HTML
    ref: str  # 借的是这个产物的 ?v=(注意:不是本目录自己的)
    why: str  # 这层间接关系的人话解释 · 直接印进违规信息,免得下一个人以为闸写错了


# 监控清单:按入口页列出它引用的、带 ?v= 的仓库内产物(URL 原样,派生 bundle 路径)。
#
# 这个闸真正的失效方式不是判定写错,是**清单漏一行** —— 漏掉的产物永远报 PASS。已犯两次:
#   2026-07-23 ai.js 的 ?v 停在 79 而五次改动无人知晓;
#   2026-07-25 home.css(主站最常改的产物)从来就不在清单里。
# 故 tests/unit/test_check_cachebust.py 有一条覆盖率测试:入口页里每个指向仓库内文件的
# ?v= 引用都必须在这里有一行,漏了就红。加新产物照着加,别指望人眼。
#
# i18n / 设计系统 CSS 不进 bundle,是带 ?v 直接 serve 的:改了不 bump 就服旧文案或旧样式
# (pearnly-ui.css 被五个入口共用,漏 bump = 五个站一起吃旧样式)。
_ENTRY_ASSETS = {
    "home.html": (
        "/static/dist/main.js",
        "/static/dist/home.css",
        "/static/dist/pre.js",
        "/static/dist/post.js",
        "/static/i18n-data.js",
        "/static/pearnly-ui.css",
    ),
    "static/admin/admin.html": (
        "/static/dist/admin.css",
        "/static/admin/admin.js",
        "/static/admin/admin-i18n.js",
        "/static/pearnly-ui.css",
    ),
    "static/console/console.html": (
        "/static/dist/console.js",
        "/static/dist/console.css",
        "/static/console/console-i18n.js",
        "/static/pearnly-ui.css",
    ),
    "static/dms/dms.html": (
        "/static/dist/dms.js",
        "/static/dist/dms.css",
        "/static/pearnly-ui.css",
        "/static/dms/dms-i18n.js",
        *(f"/static/dms/dms-i18n-{lang}.js" for lang in ("zh", "th", "en", "ja")),
    ),
    "static/dms-booking-edit/dms-booking-edit.html": (
        "/static/pearnly-ui.css",
        "/static/dms-booking-edit/dms-booking-edit.css",
        "/static/dms-booking-edit/dms-booking-i18n.js",
        "/static/dms-booking-edit/dms-booking-api.js",
        "/static/dms-booking-edit/dms-booking-language.js",
        "/static/dms-booking-edit/dms-booking-edit.js",
    ),
    "static/daily/daily.html": (
        "/static/daily/daily.webmanifest",
        "/static/dist/daily.css",
        "/static/daily/daily-i18n.js",
        "/static/dist/daily.js",
    ),
    # POS 是在卖钱的产品,它这 5 个带指纹的产物此前一个都没被守(2026-07-25 覆盖率测试照出来)。
    "static/pos/pos.html": (
        "/static/dist/pos.js",
        "/static/dist/pos.css",
        "/static/pearnly-ui.css",
        "/static/pos/pos-i18n.js",
        "/static/pos/cashier.webmanifest",
    ),
    "login.html": (
        "/static/dist/landing.js",
        "/static/dist/landing.css",
    ),
    "static/console/invite.html": (
        "/static/dist/invite.js",
        "/static/dist/console.css",
        "/static/console/console-i18n.js",
    ),
    "static/landing/portal.dc.html": (
        "/static/landing/vendor/three.min.js",
        "/static/landing/vendor/gsap.min.js",
        "/static/landing/vendor/ScrollTrigger.min.js",
        "/static/landing/vendor/support.js",
        "/static/landing/vendor/fonts.css",
    ),
    "static/terms.html": ("/static/legal.css",),
    "static/privacy.html": ("/static/legal.css",),
    "static/ai/ai.html": (
        "/static/dist/ai.js",
        "/static/dist/ai.css",
        "/static/pearnly-ui.css",
        "/static/ai/ai-i18n.js",
        "/static/ai/ai-i18n-bank-sales.js",
        "/static/ai/ai-i18n-blocked.js",
        "/static/ai/ai-i18n-board.js",
        "/static/ai/ai-i18n-empty.js",
        "/static/ai/ai-i18n-fail.js",
        "/static/ai/ai-i18n-machine-actions.js",
        "/static/ai/ai-i18n-states.js",
        "/static/ai/ai-i18n-steward.js",
        "/static/ai/ai-i18n-steward-chat.js",
        *(
            f"/static/ai/ai-i18n-{lang}{suffix}.js"
            for lang in ("zh", "th", "en", "ja")
            for suffix in ("", "-2")
        ),
    ),
}

CACHE_BUST_PAIRS = tuple(
    CacheBustPair(bundle=url.lstrip("/"), html=html, ref=url)
    for html, urls in _ENTRY_ASSETS.items()
    for url in urls
)


# 目录清单:**产物和它的 ?v 不是同一个文件**,与上面的 pairs 恰好差一层间接。
#
#   pairs :产物 A 变 → 查 HTML 里 A 自己的 `A?v=`(HTML 里写死的引用,一一对应);
#   dirs  :目录里任何文件变 → 查 HTML 里 **另一个产物** 的 `?v=`。
#
# 为什么会有这种借用:这些资源不在 HTML 里,是运行时 fetch / 现拼 URL 的,指纹从页面上 main.js
# 的 ?v 里抠(src/home/asset-fingerprint.ts 的 withFingerprint())。所以「改教程 JSON 要去
# bump main.js 的 ?v」不是笔误——它俩共用一个指纹,main.js 的 ?v 就是整个前端发版号。
#
# 2026-07-26 事故固化:改了教程正文、dist 提了、CI 全绿、文件也部署上去了,会计打开还是旧的。
# 因为只动 JSON 没动 main.js,?v 没变,CDN 按 URL 缓存一直发旧的
# (curl `setup.json?v=12017001` 出旧内容,换 `?nocache=随机` 出新内容 —— 文件新,URL 旧)。
CACHE_BUST_DIRS = (
    CacheBustDir(
        prefix="static/dist/guide-content/",
        html="home.html",
        ref="/static/dist/main.js",
        why="教程正文是运行时 fetch 的 JSON,URL 上的 ?v 抠自页面里 main.js 的 ?v"
        "(src/home/asset-fingerprint.ts · withFingerprint())",
    ),
    CacheBustDir(
        prefix="static/dist/guide-shots/",
        html="home.html",
        ref="/static/dist/main.js",
        # 2026-07-26 起配图 <img src> 也带同一指纹(guide-page.ts figureHtml → withFingerprint),
        # 所以这条不再是「提醒一下」而是真的破得掉缓存:图名固定,界面改了重拍必然同名,
        # 不 bump 就永远发旧图。E2E 闸 scripts/_guide_page_verify.cjs 逐张核 ?v 等于页面指纹。
        why="教程配图 URL 的 ?v 与正文共用页面里 main.js 的那个指纹(重拍同名图靠它换新)",
    ),
    # 扫码的两个懒加载产物(摄像头引擎 + ZXing 兜底)不写在任何 HTML 里,是 scan-loader.js
    # 运行时现拼 URL 拉的,?v 抠自页面上 dist bundle 的 ?v(assetVersion())。所以「改了
    # scan-camera.js 要去 bump 引它那个页面的 bundle ?v」不是笔误 —— 两者共用一个指纹,
    # 不 bump 就是店员的机器永远拿旧的解码器,而文件明明已经新了。
    # 一个产物两页各借一次:POS 借 pos.js 的,主站借 pre.js 的(loader 就住在这两个 bundle 里)。
    *(
        CacheBustDir(
            prefix=prefix,
            html=html,
            ref=ref,
            why="扫码懒加载产物的 ?v 抠自页面上常驻 bundle 的 ?v"
            "(static/scan/scan-loader.js · assetVersion())",
        )
        for prefix in ("static/dist/scan.js", "static/dist/zxing.js")
        for html, ref in (
            ("static/pos/pos.html", "/static/dist/pos.js"),
            ("home.html", "/static/dist/pre.js"),
        )
    ),
    # 超管后台引擎页三支模块(admin-engine*.js)改按需注入后不再写在 admin.html 里:
    # admin.js 进引擎页签才现拼 <script> 拉取,URL 的 ?v 抠自页面里 admin.js 的 ?v ——
    # 所以「改了 admin-engine*.js 要去 bump admin.html 里 admin.js 的 ?v」不是笔误,
    # 两者共用一个指纹,不 bump 就是超管永远拿旧的引擎页代码。
    # echarts 同理:admin.js / admin-engine-charts.js 里按需拉 static/vendor/echarts,
    # 加载时同样抠 admin.js 的 ?v(升级换文件名那天闸才看得见)。
    *(
        CacheBustDir(
            prefix=prefix,
            html="static/admin/admin.html",
            ref="/static/admin/admin.js",
            why="引擎页懒加载产物的 ?v 在注入时从页面里 admin.js 的 ?v 抠"
            "(admin.js 动态注入 · scan-loader.js 同招)",
        )
        for prefix in (
            "static/admin/admin-engine.js",
            "static/admin/admin-engine-cost.js",
            "static/admin/admin-engine-charts.js",
            "static/vendor/echarts/",
        )
    ),
)


def extract_vparam(html_text: str, ref: str) -> Optional[str]:
    """从 HTML 抓 `<ref>?v=<指纹>` 的指纹值;找不到返 None。"""
    m = re.search(re.escape(ref) + r"\?v=([\w.-]+)", html_text or "")
    return m.group(1) if m else None


def find_violations(
    changed: set[str],
    base_html: dict[str, str],
    head_html: dict[str, str],
    pairs=CACHE_BUST_PAIRS,
    dirs=CACHE_BUST_DIRS,
) -> list[str]:
    """产物变了但源 HTML 指纹没变 = 违规。返回人话违规说明列表(空 = 通过)。

    changed:本次 range 改动的 git 路径集合(git diff --name-only,含新增与删除)。
    base_html / head_html:{html 路径: 文本},分别取自 range 两端(缺省视作空串)。
    """
    fails: list[str] = []
    for pair in pairs:
        if pair.bundle not in changed:
            continue  # 产物没动 → 无需 bump
        old = extract_vparam(base_html.get(pair.html, ""), pair.ref)
        new = extract_vparam(head_html.get(pair.html, ""), pair.ref)
        if old == new:
            fails.append(
                f"{pair.bundle} 变了,但 {pair.html} 里 `{pair.ref}?v=` 没 bump"
                f"(仍是 {old})——CDN immutable 缓存会让 prod 吃旧 bundle。"
                f"改 {pair.html} 的 ?v= 值(任意新指纹)后重新提交。"
            )
    for rule in dirs:
        hits = sorted(p for p in changed if p.startswith(rule.prefix))
        if not hits:
            continue
        old = extract_vparam(base_html.get(rule.html, ""), rule.ref)
        new = extract_vparam(head_html.get(rule.html, ""), rule.ref)
        if old == new:
            sample = "、".join(hits[:3]) + ("…" if len(hits) > 3 else "")
            fails.append(
                f"{rule.prefix} 下有 {len(hits)} 个文件增删改({sample}),但 {rule.html} 里"
                f" `{rule.ref}?v=` 没 bump(仍是 {old})——{rule.why};"
                f"?v 不变 = URL 不变 = CDN 一直发旧的,文件是新的也没人看得到。"
                f"改 {rule.html} 的 ?v= 值(任意新指纹)后重新提交。"
            )
    return fails


def git(*args: str) -> str:
    """跑 git 命令 · 返回 stdout(失败 raise)。"""
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} 失败 · exit {result.returncode}\nstderr: {result.stderr}"
        )
    return result.stdout


def _show(ref: str, path: str) -> str:
    """取某 commit 下某文件内容;文件在该 commit 不存在 → 空串。"""
    try:
        return git("show", f"{ref}:{path}")
    except RuntimeError:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="缓存破机械闸 · 产物变则源 HTML ?v= 必 bump")
    ap.add_argument("--base", default="HEAD~1", help="diff base(默认 HEAD~1)")
    ap.add_argument("--head", default="HEAD", help="diff head(默认 HEAD)")
    ap.add_argument("--quiet", action="store_true", help="只在违规时输出")
    args = ap.parse_args()

    try:
        git("rev-parse", "--git-dir")
    except (RuntimeError, FileNotFoundError) as e:
        print(f"⚠️  不在 git 仓库或 git 不可用 · 跳过缓存破检查:{e}")
        return 0

    try:
        git("rev-parse", "--verify", args.base)
    except RuntimeError:
        print(f"⚠️  base ref `{args.base}` 不存在(可能首次 commit)· 跳过缓存破检查")
        return 0

    commit_range = f"{args.base}..{args.head}"
    try:
        changed = {
            line.replace("\\", "/").strip()
            for line in git("diff", "--name-only", commit_range).splitlines()
            if line.strip()
        }
    except RuntimeError as e:
        print(f"⚠️  git diff 失败 · 跳过:{e}")
        return 0

    htmls = {p.html for p in CACHE_BUST_PAIRS} | {d.html for d in CACHE_BUST_DIRS}
    base_html = {h: _show(args.base, h) for h in htmls}
    head_html = {h: _show(args.head, h) for h in htmls}

    fails = find_violations(changed, base_html, head_html)

    if args.quiet and not fails:
        return 0

    print("=" * 72)
    print("🧨 缓存破机械闸 · 产物变则源 HTML ?v= 必 bump")
    print("=" * 72)
    print(f"  Diff 范围 : {commit_range}")
    if fails:
        print(f"  🔴 违规   : {len(fails)}")
        print()
        for msg in fails:
            print(f"  [FAIL] {msg}")
    else:
        print("  ✅ PASS   : 无产物变更 / 指纹已同步 bump")
    print("=" * 72)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
