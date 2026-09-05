---
name: frontend-change
description: 修改 Pearnly 页面、样式、交互或用户可见文案时，核对真实入口、构建缓存、多语言与浏览器验证；包含导出和 LINE 文案。
---

# 前端与多语言

改页面时先按 [入口地图](references/entry-map.md) 核对路由、实际组件和可读源。用当前分支代码、浏览器请求与页面确认目标；不要仅凭测试 harness 中存在组件就认定它是实际入口。

- `src/**` 和 `scripts/build-html-minify.mjs` 的 TARGETS 所列源页变化时运行 `npm run build`，对应 `static/dist` 产物同批提交。独立静态资源按实际引用更新；不能笼统认为 HTML/CSS 不用构建。
- 更新受影响的 `?v=` 引用；不要为过闸改无关缓存键。新增对外页面同步 TARGETS、外壳及路由契约。
- 保持现有 UTF-8 和 CRLF/LF；遵守 `.prettierignore`，避免全文件转换。尤其留意 `home.html`、`login.html`、`static/i18n-data.js` 和存量 CSS。
- 使用现有设计令牌和组件，令牌值从 `static/pearnly-ui.css` 与 `static/home-01-base.css` 读取。需要设计细节时读 `docs/project/DESIGN_SYSTEM.md`。
- 涉及文案或切换语言时读 [多语言参考](references/i18n.md)。保留加载、空、错误与正常状态，检查受影响的手机/桌面布局、触控与最长语言。
- 根据文件类型运行 `docs/GATES.md` 对应检查；修改默认行为时搜索相关 E2E 并更新受影响断言。动画/断点验证要等待页面稳定。
- 用真实浏览器验证受影响路径并保存截图；扫码/键盘行为使用真实按键事件。证据要求见 `docs/agent/VERIFICATION.md`，通过的检查不无故重复。
