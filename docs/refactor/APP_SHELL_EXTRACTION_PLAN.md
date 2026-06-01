# C3 收尾 · app shell(顶栏+侧栏)抽进 JS 的最稳妥方案 · REFACTOR-WB-C3

> 2026-06-01 上个窗口产出。Zihao 拍板:坚持把导航框架也搬进 JS,做到 Claude 那种
> 「view-source 连框架都只见外壳」。这是 home.html C3 的**最后一块、也是最高风险一块**。
> 本文是给执行窗口的完整作业书。**不照做、直接 push 试 = 大概率重蹈 R3 覆辙(全 app 导航瘫痪)。**

## 0. 为什么它比前面 12 块都险(先认清)

前面抽的是模态框(`display:none`,注入晚没人看见)、业务页(有自己 loading 态)。
**顶栏/侧栏是「永远可见的框架」+ boot 关键路径**,两个新风险:

1. **FOUC 闪屏**:留空壳等 JS 注入 → 浏览器可能先画空导航条再被填充 → 用户每次进页面看到导航**闪一下**。必须用骨架屏消除(见 §3)。
2. **R3 竞态雷区**:`core-boot.js`(main.js 第 2 个 import·boot 编排器·bootstrap 尾部自执行)在 eval 期 `document.querySelectorAll('.nav-item').forEach(绑 click)` + sidebar-toggle 绑定。漏一个 eval 期消费者没在注入后 → 导航点不动 / 启动崩。记忆 [[wb-src-home-c3-split-playbook]] 记着「R3 曾因 boot 期竞态 revert」。
3. **blast radius = 整个 app**:不是某弹窗坏,是所有人登录后导航全瘫。

## 1. 精确边界(基于本窗口收尾时的 home.html · 661 行 · 执行前用 grep 重新定位防偏移)

- **顶栏**:`<div class="topbar">`(约 L155)→ 其 `</div>`(约 L281)。
- **侧栏**:`<nav class="sidebar" id="sidebar">`(约 L284)→ `</nav>`(约 L422)。
- 两者之间(L282-283)是注释/空行;侧栏后(L423-427)空行,`<main class="main">` 约 L428。
- 执行前必须 `grep -nE 'class="topbar"|<nav class="sidebar"|</nav>|<main' home.html` 重新确认行号(别信本文写的数字 · 文档手写行数铁律)。

## 2. 抽法(沿用本窗口已验证 12 次的 R6 注入范式 + wbInject 公共助手)

1. **空壳**:home.html 留
   `<div class="topbar"></div>` 和 `<nav class="sidebar" id="sidebar"></nav>`(**保留 class/id**,CSS 与布局靠它们)。
2. **新模块** `src/home/app-shell-html.js`:
   - `import { wbInject } from './wb-inject.js';`(本窗口已建的公共助手 · 别再抄样板 · 别加注释 emoji,有 `check_ai_smell` 闸拦)。
   - 两个 const 存 verbatim inner(脚本逐字节提取 · 禁手抄),`wbInject('topbar-shell-id', TOPBAR_HTML)` … 注意:topbar 当前无 id,抽时给空壳加个 id(如 `id="topbar"`)或用 class 选择——**wbInject 现在按 id 找**,所以**给顶栏空壳加 `id="topbar"`**,sidebar 已有 `id="sidebar"` 直接用。
   - 脚本提取 + 断言 `模板 === git HEAD:home.html 对应 inner`(CRLF→LF 归一)· 本窗口每轮都这么验。
3. **import 位置(命门)**:`app-shell-html.js` 必须插在 **main.js 的 `core.js`(约 line 10)之后、`core-boot.js`(line 12)之前**(即现在 page-ocr-html.js 所在的 line 11 同区)。
   理由:core-boot 在 eval 期绑 `.nav-item`,模块按 import 顺序 eval,注入必须先发生。**page-ocr-html.js 已在此位且验证可行 → 此位已被证明能赶在 core-boot 前**。
   还要确认在 `layout.js`(line 31·applySidebarVisibility 权限显隐)之前——line 11 天然满足。

## 3. FOUC 骨架屏(必做 · 否则导航闪屏)

home.html 的 `<head>` 或某 `home-NN.css` 里加:空壳未注入时显骨架,注入后(`[data-wb-injected]`)隐藏。例:
```css
.topbar:empty { /* 占位高度 + 背景,避免塌陷/闪烁 */ min-height: 48px; }
.sidebar:empty { min-width: 200px; }
```
或更稳:给空壳内联一个极简骨架(纯 CSS 灰条),wbInject 注入真内容后骨架被 innerHTML 覆盖。**目标:任意时刻框架占位尺寸不变 · 不塌不闪**。
> wbInject 注入是同步的、在模块 eval(defer · DOM 解析后、DOMContentLoaded 前)发生,通常先于首次有意义绘制;但**必须本地反代亲眼确认无闪**,别假设。

## 4. 验证(铁律 · 不许跳)

**先本地反代真浏览器验,验透了再 push**(记忆 [[verify-local-proxy-harness]]):
- 起 `_uitest/proxy.cjs`(gitignore)拦本地 `home.html` + `static/dist/main.js`(+.map),其余透传 prod;改写 Origin→pearnly.com、删 CSP、Location 改回 localhost。
- 临时 spec(用完即删 · 别 commit 到 tests/e2e/ 长期):内联轻量登录(`waitForFunction(token)` 不等 load),然后逐项验:
  1. 登录后顶栏渲染(logo/搜索/头像可见 `getComputedStyle`)
  2. 侧栏所有 nav-item 渲染 + **逐个点击切到每个页面**(dashboard/ocr/history/clients/automation/settings…)路由正常
  3. **无 FOUC**:截图首帧 / 观察框架不闪
  4. sidebar-toggle 汉堡折叠 + 移动端视口(iPhone 视口)响应式
  5. 顶栏搜索框点击触发 cmdk(命令面板)
  6. 头像菜单展开
  7. 权限显隐:owner vs employee 看到的 nav-item 不同(layout.js applySidebarVisibility)——至少验 owner 账号;employee 显隐若无账号则记 TODO
  8. `assertNoConsoleErrors`
- **本地全绿** → 才 `npm run build` + commit `static/dist` + **bump `dist/main.js?v=`** + push。
- push 后立即跑 `01-login 03-clients 04-history`(它们覆盖 boot+顶栏+侧栏路由)+ 上面针对性 spec 对 prod 复跑。
- **红 → 立即 `git revert` + push 回滚**(铁律 #26 D 项)。

## 5. 收益与止损

- 做成:home.html 661 → ~400,view-source `<body>` 基本只剩挂载点,达到 Zihao 要的 Claude 级。
- **若本地反代验出 FOUC 消不掉 / 竞态难解 → 停 · 回滚 · 找 Zihao**。不要带病上线导航。
- 这块**不在「整顿轮忽视版本横幅」豁免之外**:仍 bump `?v=`,release_notes 整顿轮不重写(记忆 [[refactor-skip-version-banner]])。

## 6. 去 AI 味(本窗口新增机械闸 · 别再漏)

写 `app-shell-html.js` 时:**注释禁 emoji**(⚠️🔴✅ 等)、**禁 console.log**、用 wbInject 别抄样板。
`scripts/check_ai_smell.py` 已挂 pre-push 第 7 道闸,改前端碰到会拦——但别等它拦,写的时候就干净。

---
范式总纲见记忆 [[wb-src-home-c3-split-playbook]];部署/CRLF/bump 见 [[fe-cache-bust-vparam-required]]、[[c3-commits-source-only-dist-rebuilt]]、[[home-css-html-crlf]]。
