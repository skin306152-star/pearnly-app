# ADR-001 · 前端上 Vite + ES modules(不上 Webpack · 不留裸文件)

> **状态**:已采纳(2026-05-22 · Zihao 拍板"路径 B 上 Vite")· A1 全 4 子已落地
> **关联 task**:REFACTOR-A1(Vite + ES modules 落地)
> **关联铁律**:#23 硬门槛 #3(`home.js` 封死 · 新前端业务逻辑只能进 `src/home/*`)· 路径选择 L3

---

## 背景

整顿前 Pearnly 前端是"裸文件 SaaS":`home.html` 直接 `<script src="home.js?v=...">` 引一个
33,000+ 行的巨石 `home.js`(单函数曾达 12,694 行)· 加两个独立 IIFE(`dashboard.js` /
`billing.js` / `version-banner.js`)。**没有 build pipeline、没有模块系统、没有依赖图** ——
0% ES modules · 改一处容易牵连 · 切换交互延迟 3-5 秒。

整顿主计划"Google 级 90%" 工程化目标里明确要求:`Build pipeline 无(裸文件)→ Vite + esbuild`、
`ES modules 0% → 100%`、`TypeScript 化 0% → 80%+`。A1 是阶段 A(工具链升级)的核心,后续
C 阶段拆 `home.js` 成 50-100 个 `src/home/*` 模块完全依赖它先到位。

## 决策

**前端上 Vite 6 + ES modules,作为后续所有前端拆分的构建底座。新前端业务逻辑一律进 `src/home/*`
(ES module),不再往 `home.js` 巨石塞,也不再新建 `static/*.js` IIFE(除完全独立的小组件)。**

| 方案 | 取舍 | 结论 |
|---|---|---|
| 维持裸文件 `home.js` | 0 改造成本 · **但无模块系统/无 build/无 tree-shaking · 巨石永远拆不动** | ❌ 治标不治本 |
| Webpack | 生态成熟 · **但配置重(loader/plugin 链)· 冷启动慢 · 对单人项目过度** | ❌ 偏重 |
| **Vite 6 + esbuild** | 配置极简 · esbuild 打包快 · 原生 ESM · 产物固定文件名进 git · **服务器零改动** | ✅ 选这个 |
| 换框架(React / Vue) | = 路径 L2 换技术栈 · 业务停 2-3 月 · 有真实付费用户不可接受 | ❌(主计划已否决) |

**关键约束 · prod 部署链不动**:Vite 在**本地 build**(`npm run build`)· 产物
`static/dist/main.js`(固定文件名)直接进 git · 服务器仍走原 git pull + `cp home.* static/` +
`systemctl restart`。`home.html` 用老的 `?v=` cache_bust,不引入 hash + manifest(留后续 A1.x)。

## 落地交付(A1 4 子 · 全 ✅)

| 子任务 | 内容 | commit |
|---|---|---|
| A1.1 | 装 Vite 6 + 配 esbuild(`vite.config.mjs` + 本地 build) | `e11e81d` |
| A1.2 | CI 加 vite build step(`ci.yml` · 进 5 关守门) | `cfbb7d5` |
| A1.3 | `dashboard.js` / `billing.js` IIFE → ES module(`git mv` 到 `src/home/` · `home.html` 改 script · cache_bust++) | `1c4c3bd` |
| A1.4 | 验证 prod 全跑通(`/api/version` 返 11835032 · `/static/dist/main.js` serve OK) | 2026-05-22 |

**`vite.config.mjs` 关键配置**(实物):
- `build.outDir = 'static/dist'` · `emptyOutDir: true` · `sourcemap: true` · `minify: 'esbuild'` · `target: 'es2020'`
- 入口 `src/main.js` · `entryFileNames: '[name].js'`(固定 `main.js` · 不带 hash · 配合老 cache_bust)

**`package.json` 脚本**:`build` = `vite build` · `build:watch` · `test:e2e`(Playwright)· `lint`(ESLint)· `format`(Prettier)。

## 理由

1. **Vite 配置极简 + esbuild 快**:相比 Webpack 的 loader/plugin 链,Vite 一份 `vite.config.mjs`(约 30 行)即可,esbuild 打包秒级。单人项目维护成本是 Webpack 的几分之一。
2. **原生 ESM 是拆巨石的前提**:`home.js` 22k+ 行要拆成 50-100 个 `src/home/*.js`,必须有模块系统让模块互相 `import`(如各 feature 模块 import 公共件 `src/home/_shared.js`)。裸文件做不到。
3. **本地 build + 产物进 git = 服务器零改动**:不动 `git-deploy.sh` / webhook(触发铁律 #16 红线),把整顿风险压到最低。
4. **保留 FastAPI + vanilla → 渐进**:= 路径 L3(内部整顿 + 路径 B),不推倒重写,真实付费用户业务不中断。

## 取舍 / 边界

- **暂不上 hash + manifest**:产物用固定文件名 `main.js` + `home.html` 老 `?v=` cache_bust。代价是缓存控制不如内容 hash 精细,但换来服务器零改动。切 hash 模式留后续 A1.x。
- **暂不强制 TypeScript**:工程化目标里 TS 化 80%+ 是 C5 的事,A1 只铺 ESM 底座,vanilla JS 先跑通。
- **巨石 `home.js` 不在 A1 拆**:A1 只把已经独立的 IIFE(`dashboard`/`billing`)迁成 ESM 验证范式,真正拆 22k 行是 C1 的长跑。

## 后果

- ✅ **硬门槛 #3 生效**:`home.js` 封死 —— 新前端业务逻辑只能进 `src/home/*`(Vite ES 模块)。此条**更正了**旧铁律 #17 / #21 的措辞"新前端放 `static/xxx.js` IIFE":自 A1 上 Vite 后,只有"完全独立、不依赖主应用"的小组件(如 `version-banner`)才允许留 `static/*.js`。
- ✅ C 阶段拆 `home.js`(C1)有了构建底座:已抽 `dashboard` + `billing`(IIFE→ESM)+ 测试中心 → `src/home/test-center.js`(`0377055`);i18n 字典 9,763 行 → `static/i18n-data.js`。
- ⚠️ CI 多一道 vite build 守门(`npx vite build` 进 5 关之一)· 产物 `static/dist/` 要随代码一起 commit,漏了会导致 prod 引到旧 bundle。
- 📌 后续:hash + manifest 模式、TS 化(C5)、`home.js` 拆到 50-100 模块(C1)都在 Vite 底座上继续。
