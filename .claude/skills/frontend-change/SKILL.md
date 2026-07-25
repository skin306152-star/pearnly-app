---
name: frontend-change
description: 动前端必读 —— src/** 或 static/** 或任何用户可见 UI 改动的前置确认(生产真实路径)、构建产物同提交、?v 破缓存、CRLF 禁忌、UI 一致性闸、四态与设计令牌。改页面、改样式、加组件、改 SPA 之前用。
---

# 前端改动

## 0. 先确认要改的东西是生产真实活着的路径

血泪(2026-07-24):改完"集成抽屉 Express 连接卡"、截图全绿、正要 push —— 生产根本没有那个抽屉,真实入口是录入工作台的另一组件,全部白干丢弃。

- 先在生产真实点击路径上走一遍,确认那张卡/那个流程是当前活的
- 测试脚本能到达的代码路径 ≠ 生产在用的路径
- 入口 → 源文件映射唯一权威:`AGENTS.md` §5-bis

## 1. 提交纪律(最常见的"改了没生效")

- 改 `src/**`(Vite 源)→ `npm run build` + `git add static/dist` **同一个 commit**。生产部署不重建 dist,只提交源码 = 线上跑旧 bundle。
- 纯 `.css` / `.html` 改动不用 build(nginx 直接 serve),但**引用处的 `?v=` 必须 bump**,否则 CDN 回旧文件。
- 改 `static/admin/*` 要 bump `admin.html` 里的 `?v=`;改 `src/home/*` 要 bump 根 `home.html` 的 `?v=`。
- 新增对外页面必须进 `scripts/build-html-minify.mjs` 的 TARGETS + 外壳闸测试 + 路由契约表。

## 2. 编码 / 换行禁忌

`home.html` · `login.html` · `static/i18n-data.js` · `static/home-*.css` · `static/pos/*.css` 是 CRLF 且在 `.prettierignore` 里:

- 禁 `sed`、禁 `prettier --write`、禁 python/node 用 latin1 追加(会毁 UTF-8 中泰文)
- 禁 PowerShell `Get-Content -Raw`(无编码参数会读坏中泰文)→ 用 Edit 工具
- 删大块用 node 读行数组 + join 保 CRLF

## 3. 设计语言

- 颜色一律 `var(--token)`,不写死 hex(注释里的 hex 也被闸计数)。令牌真值:`static/pearnly-ui.css` + `static/home-01-base.css`
- 按钮走 `.pu-btn` 组件层;只有左侧导航栏可用黑底表示当前位置
- 四态必须都有:加载(骨架)/ 空 / 错 / 正常。空态要指路,不只写"暂无数据"
- 图标只用 SVG line(lucide/feather),禁 emoji 当图标
- 手机端:桌面布局 + `@media (max-width: 800px)` 降级,触控目标 ≥44×44,表格横滚或卡片化,hover-only 操作必须有 click 备选
- 完整规范:`CLAUDE.md/DESIGN_SYSTEM.md`

## 4. 前端三闸 + UI 闸(push 前手跑)

```powershell
npm run format:check            # prettier(按提交内容校验)
npm run lint                    # eslint
npm run typecheck               # 改 .ts 才需
python scripts/check_ai_smell.py <改的文件>
python scripts/check_ui_consistency.py --quiet
node scripts/ui_design_lint.mjs --gate
python scripts/check_theme_responsive.py --gate --quiet
python scripts/check_asset_bundling.py
```

## 5. 验收

UI 改动一律真浏览器 + 截图为证(抓 `isVisible` / `getComputedStyle`)。详见 `verification` skill 第 3 节。
