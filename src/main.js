// REFACTOR-A1.1 (2026-05-22) · Vite entry 占位
//
// 本文件是 Vite build 的入口 · 当前只验证工具链跑通
// 后续:
// - A1.3 真 import dashboard / billing 模块(改自 static/home/*.js IIFE)
// - 阶段 C 持续 import 从 home.js 抽出的小模块
//
// home.js 33000 行不进 Vite(铁律 #18 · 渐进翻新)· 仍走 <script src> 老路
// 本 bundle 输出到 static/dist/main.js · home.html 用 <script type=module> 加载

if (typeof console !== 'undefined' && typeof console.info === 'function') {
  console.info('[pearnly] vite bundle loaded · REFACTOR-A1.1');
}

export {};
