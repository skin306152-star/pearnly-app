# 11 · UI 硬规定落地草案(等另一窗口结束后对着这个落 · 主仓库)

> Zihao 2026-06-04:全站统一弹窗 + 切换/主按钮蓝不用黑(只导航栏黑)+ 纠正色值冲突 ·
> **要硬性机械闸,不只文档**。另一个窗口正在改主仓库 → 本草案先备好,等放行再一次性落、避免撞车。
> 落地全程遵 [[ui-design-before-build-rule]] + 铁律 #16(改前确认在 master + 真浏览器验)。

## 落地顺序(等"清了"后)

1. 切 master + `git pull`(确认另一窗口的改动已进来,基于最新落)。
2. 改 4 处黑底按钮 → 蓝(下 §3)。
3. 加 `--btn-blue` token(下 §3)。
4. 扩 `check_ui_consistency.py`(下 §1)+ 跑一次取真实基线。
5. 挂进 `pre-push`(下 §2)。
6. 改 CLAUDE.md / DESIGN_SYSTEM.md 文字(下 §4)。
7. `npm run build` + bump `home.html ?v=` + `git add static/dist` → 真浏览器验按钮变蓝 + curl prod CSS 字节 → commit + push master。

---

## §1 · check_ui_consistency.py 新增两条硬规则

加在现有 B1-B4/C1 之后。**两条用独立基线,不并进 480 总账**(更硬更清晰):

```python
# ── 规则 D1:全站弹窗 · 禁新增抽屉(.drawer)· Zihao 2026-06-04 ──
# 现存抽屉冻结成基线(只许减不许增);新增一处 .drawer = 红。
DRAWER_BASELINE = None  # 落地时跑一次填真实数(约 HTML/JS 57 + CSS 定义 63)
drawer_hits = []
for f in HTML_FILES + JS_FILES:
    txt = read(f)
    for m in re.finditer(r'class\s*=\s*"[^"]*\bdrawer[\w-]*\b[^"]*"', txt):
        drawer_hits.append((f.name, m.group(0)[:60]))
for f in CSS_FILES:
    txt = read(f)
    for m in re.finditer(r'\.drawer[\w-]*\s*[{,]', txt):
        drawer_hits.append((f.name, m.group(0)))
results["D1 抽屉用法(禁新增 · 用弹窗 .modal)"] = drawer_hits

# ── 规则 D2:按钮/切换 黑底(只导航栏可黑)· 目标基线 0 ──
# 逐 CSS 规则块扫:选择器含 btn/toggle/switch/.act-btn/.primary,
# 且 background 用 var(--ink)/#000/#111/#1a202c → 违规。
# 排除:nav/sidebar 选择器(允许黑)· TOKEN_CSS(home-38 用 #2563eb 不算)。
BLACK_BG = re.compile(r'background[^;:}]*:\s*[^;}]*(var\(--ink\)|#000\b|#000000\b|#111\b|#111111\b|#1a202c\b)', re.I)
BTN_SEL = re.compile(r'(btn|toggle|switch|act-btn|\.primary)', re.I)
NAV_SEL = re.compile(r'(nav|sidebar)', re.I)
black_btn = []
for f in CSS_FILES:
    if f.name in TOKEN_CSS:
        continue
    css = read(f)
    for block in re.finditer(r'([^{}]+)\{([^}]*)\}', css):
        sel, body = block.group(1), block.group(2)
        if BTN_SEL.search(sel) and not NAV_SEL.search(sel) and BLACK_BG.search(body):
            black_btn.append((f.name, sel.strip()[:60]))
results["D2 按钮/切换黑底(应蓝 · 只导航栏可黑)"] = black_btn
```

裁决(加在 ratchet_verdict 之外,独立硬判):

```python
DRAWER_BASELINE = <落地时实测>   # 冻结
BLACK_BTN_BASELINE = 0           # 改完 4 处后 = 0 · 任何黑底按钮即红
hard_fail = False
if len(drawer_hits) > DRAWER_BASELINE:
    print(f"🔴 新增抽屉 {len(drawer_hits)} > 基线 {DRAWER_BASELINE} · 用 .modal 弹窗,别用 .drawer")
    hard_fail = True
if len(black_btn) > BLACK_BTN_BASELINE:
    print(f"🔴 按钮/切换黑底 {len(black_btn)} 处 · 改蓝(var(--btn-blue))· 只导航栏可黑")
    hard_fail = True
# 退出码:原 ratchet 不过 OR 任一硬规则不过 → 非零
return 0 if (ok and not hard_fail) else 1
```

> 注:正则是粗筛,落地时跑一遍对样例肉眼校一遍(防误报/漏报),再定基线。

---

## §2 · pre-push 挂硬拦(`scripts/git-hooks/pre-push`)

现有"防屎山闸"段(check_file_size / check_line_ratchet)后面加一段:

```sh
echo "  · check_ui_consistency(禁新增抽屉 + 按钮黑底 · 全站弹窗+蓝按钮硬规)"
python scripts/check_ui_consistency.py --quiet || fail "UI 硬规:新增了抽屉 或 按钮黑底(用 .modal + var(--btn-blue))"
```

> 给 check_ui_consistency.py 的 main() 加 `--quiet`(只在失败时打详情),对齐其它守门。
> CI 的 `lint-ui` 翻 fail 模式要改 `.github/workflows/ci.yml`(token 缺 workflow scope → 需 `gh auth refresh -s workflow` · 暂靠 pre-push 兜底)。

---

## §3 · 4 处黑底按钮改蓝 + 加 --btn-blue token

### 先在 home-38-buttons.css 顶部加 token(它在 TOKEN_CSS · 可裸 hex · 单一来源)

```css
:root {
    --btn-blue: #2563eb;
    --btn-blue-hover: #1d4ed8;
}
```

### 4 处精确改法

| 文件:行 | 现状 | 改成 |
|---|---|---|
| `home-04-results.css:13` | `.btn-primary { background: var(--ink); color: #fff; }` | **整行删**(home-38 收口已用 `!important` 接管 `.btn-primary`,这行是被盖住的死声明) |
| `home-29-vat-recon-clients.css:926` | `.sv-act-btn.primary:hover { background: var(--ink); border-color: var(--ink); }` | `background: var(--btn-blue); border-color: var(--btn-blue);` |
| `home-29-vat-recon-clients.css:516` | `.bv-files-toggle.open .bv-files-count { background: var(--ink); color: #fff; }` | `background: var(--btn-blue); color: #fff;` |
| `home-15-team-folder.css:521` | `.drawer-push-btn:hover { background: var(--ink); }` | `background: var(--btn-blue);` |

> 改完 `check_ui_consistency` D2 = 0,基线设 0(此后任何黑底按钮即红)。
> 改的是 .css(nginx 直 serve)· 仍需 `npm run build`(打包一致性闸)+ bump `home.html ?v=` + 真浏览器验色 + curl prod 字节(grep 类名不算)。

---

## §4 · 主项目文档纠正(规定统一 · 让闸有据)

### CLAUDE.md/CLAUDE.md(§30 NAV-IA 视觉对齐铁律那行)

把:
> `active/focus 仍可保黑系或随蓝(侧栏 active 视觉另议)· 但 .btn-primary 一律蓝。`

改成:
> **全站按钮/切换(toggle/switch/active 操作按钮)一律品牌蓝 `#2563EB`,不用黑;只有左侧导航栏(sidebar)可保黑作当前位置指示。机械闸 `check_ui_consistency.py` D2 硬拦(基线 0)。**

并加一条:
> **全站弹窗:新 UI 一律用 `.modal` 弹窗,禁新增 `.drawer` 抽屉(机械闸 D1 ratchet · 存量冻结、不retrofit)。**

### DESIGN_SYSTEM.md
- §2.1 `--brand #1a365d` 那行加注:`⚠️ 主按钮真值以 home-38-buttons.css #2563EB 为准 · 此处 #1a365d 为旧值勿用作按钮底`。
- §8 按钮:加"按钮/切换黑底 = 违规(check_ui_consistency D2)· 用 var(--btn-blue)"。
- §10 抽屉:标"⚠️ 已弃用于新功能 · 新 UI 用 §11 模态 · 存量保留不retrofit · 机械闸 D1 禁新增"。

---

## 不做(明确边界)

- ❌ 不 retrofit 现存 57 处抽屉(Zihao:只管"以后新增")。
- ❌ 不动 :root 全局变量 / 不逐页挤牙膏(沿用 [[btn-black-root-cause-global-collapse]] 教训 · 只加 --btn-blue 单一 token + 改 4 处叶子)。
- ❌ 不碰 nav/sidebar 黑底(那是当前位置指示 · 合规)。
