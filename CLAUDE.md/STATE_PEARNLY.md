# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ 前端 C9 五个最大文件 store 中心化拆分 · 全 push 上线 + prod 实测**)

- **本窗口连收 5 个前端 C9 + simplify ✅**:bank-recon-v2 1592→**405** / bank-recon(M10) 1252→**181** / exceptions 1250→**176** / gl-vat-recon 896→**66** / clients 878→**329**。各 +4~6 子模块(store/helpers/...)。commit `b944e03/1d08fbd/e1a9f7f`(批1)+ `1a800de/4924909`(批2)· prod `/api/version` 11850064→**11850069** · 3 批 prod spec 全绿。
- **C9 范式([[c9-store-centralization-bankrecon]])**:stateful IIFE 私有 `let` 状态 → 共享 store 对象(**从不重赋值的对象直接 `export const`** · 可重赋值原始值包对象 · **只单簇用的随簇移为模块私有**免 store)。子模块间**真 ESM import/export**(调用点 verbatim · cyclic import 全 runtime 调用 + 提升函数 → 安全)。生成器**按行 verbatim 切片 + de-indent + 词边界状态替换** · **覆盖率**(每 CODE 行恰好归一处·零丢失无重叠)+ **逐行 CODE 等价**双校验。CRLF/LF 匹配源文件(brv2/bank-recon CRLF · exceptions/glv/clients LF)。
- **真浏览器验**:本地反代 harness(拦本地 `main.js` · 其余透传 prod)+ e2e_2 · **loadTask 真数据**(brv2 U盘 11.68 配套对 · 169 行 · matched=25 · 渲染逐字段 == 后端 JSON)+ 各页 window 桥 `function` + 零 console error。fixture:`D:银行对账需求`(11.68 配套对出真实行 · 无关对出 0 行)。
- **simplify 收口**:4 agent 审定拆分**干净**(无效率回归 · cyclic import 全 runtime 安全 · bundle +1.4KB · 无死 import/export · altitude 对路)。3 个跨切面 follow-up([[c9-split-followups]]:建 `recon-utils.js` 统一微工具 / exceptions 命名标准化 / 跨 feature `window._clientsCache` 桥)**故意未在收尾改**(会动已 push 钱路 + 破 verbatim) · 留专窗口。
- **最后 commit**:`4924909`。**剩 11 个 `src/home/*.js` >500**:erp-mappings 739 / email-ingest 726(C9)· erp-exceptions 742 / folder-watcher 668 / erp-xero 663 / core-boot 565 / archive-settings 530 / upload-camera 506(非 C9 · verbatim 提取)· ocr-recognize 550(OCR 路径 · 改前报方案)· excel-formula-recon 877 / test-center 706(skin-only · e2e_2 无法 E2E)。下窗口照 C9 范式续拆。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
