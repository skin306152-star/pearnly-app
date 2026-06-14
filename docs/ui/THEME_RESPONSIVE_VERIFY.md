# 暗夜模式 + 手机端 验收流程

> 改任何前端(`static/home-*.css` / `src/home/*` / 组件 HTML)都走这一页。
> 机械闸只兜底硬伤,**"合理"靠真浏览器双主题×双视口扫图** —— headless 定宽 ≠ 真机(血泪在案)。

## 两层防线(各管一半)

| 层 | 工具 | 管什么 | 管不了什么 |
|---|---|---|---|
| 机械闸(pre-push 硬拦) | `scripts/check_theme_responsive.py --gate` | 暗夜不翻面的写死色(3位hex/white·black/不透明rgb)只许降;入口页 viewport 必须在;固定大宽度无响应只许降 | 配色对比度、间距在窄屏是否挤、暗夜下某块"能看但难看" |
| 真机扫图(改前端必跑) | `tests/e2e/_ui_audit_full.spec.js` | 浅/暗 × 桌面/手机 四象限全路由截图,肉眼扫白底洗白、窄屏溢出、控件挤成一团 | 真 iOS Safari 动态地址栏/svh(只有真手机暴露,见下) |

## 写代码时(让机械闸天然绿)

颜色**一律走令牌**,暗夜随 `:root.dark` 翻面:

```css
/* 对 */
.card { background: var(--bg); color: var(--ink); border: 1px solid var(--line); }
.card { box-shadow: 0 2px 8px rgba(0,0,0,.12); }   /* 半透明阴影叠任意底色都成立 · 闸豁免 */

/* 错(暗夜下不翻面 → 白底洗白字 → 闸拦) */
.card { background: #fff; color: black; }
.card { background: rgb(255,255,255); }
```

需要暗夜单独处理(如 logo 垫白底)→ 写 `:root.dark .selector { ... }` 补丁,不要改基础规则。
令牌定义见 `static/home-01-base.css`(`:root` 浅 + `:root.dark` 暗)。

手机端:容器别写死大宽度,用 `max-width` + `width:100%`;断点用 `@media (max-width: 768px)`。

## 推之前(本地自查机械闸)

```bash
python scripts/check_theme_responsive.py            # 看报告(各类命中 + viewport)
python scripts/check_theme_responsive.py --gate     # 棘轮裁决(超基线/缺 viewport → 非零退出)
# 改对后命中下降了 → 收紧基线防回潮:
python scripts/check_theme_responsive.py --update-baseline
```

## 真机扫图(改前端必跑 · 暗夜+手机 四象限)

需测试账号环境变量 `PEARNLY_E2E_USER` / `PEARNLY_E2E_PASS`(HKCU setx · 绝不进 git)。
脚本内部一次跑浅 + 暗两遍;视口由 `PEARNLY_AUDIT_MOBILE` 切,跑两次拿桌面 + 手机:

```powershell
# 桌面(浅+暗)→ scripts/_ui_audit_full/d-*.png
npx playwright test tests/e2e/_ui_audit_full.spec.js --reporter=line
# 手机(浅+暗)→ scripts/_ui_audit_full/m-*.png
$env:PEARNLY_AUDIT_MOBILE=1; npx playwright test tests/e2e/_ui_audit_full.spec.js --reporter=line
```

产出 `scripts/_ui_audit_full/{d,m}-{L0,DARK}-<route>.png`。**逐张扫**:

- 暗夜(`*-DARK-*`):有没有白底块洗白字、边框消失、图标看不见、对比度过低。
- 手机(`m-*`):有没有横向溢出、卡片/表格挤出屏、按钮叠在一起、文字被截。

## 真机最后一关(机械+headless 都测不到的)

固定底栏 / 动态地址栏 / `svh` / 软键盘顶起内容这类,**只有真 iOS Safari + 真 Android Chrome 暴露**。
重排底栏/吸顶/全屏弹窗/登录页这类布局,收尾前在真手机上过一眼再说"已验证"。
