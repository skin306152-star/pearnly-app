// REFACTOR-A1.3 (2026-05-22) · Vite entry · side-effect imports
//
// 把已抽出的 ES module 集中到这里 · Vite bundle 成 static/dist/main.js
// 加载顺序:home.html <script src=home.js> 同步 → <script type=module src=/static/dist/main.js> defer
// 所以 dashboard / billing 执行时 · home.js 提供的全局(t/showToast/escapeHtml/...)已就绪
//
// 后续阶段 C 持续从 home.js 抽模块 → 都进 src/home/ → 在这里 import

import './home/dashboard.js';
import './home/billing.js';
import './home/test-center.js'; // REFACTOR-C1 · 测试中心(skin only)
import './home/workspace-switcher.js'; // B4 · workspace 工作模式切换器(取代旧 ClientSwitcher)

if (typeof console !== 'undefined' && typeof console.info === 'function') {
    console.info('[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher');
}
