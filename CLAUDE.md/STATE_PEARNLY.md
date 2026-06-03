# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-03 · **✅ 前端模块化收官 · 所有源文件(后端+前端)≤500 达成 · check_file_size FAIL 0**)

- **本窗口连收 11 个 `src/home/*.js`(11→0 FAIL · 全 push 上线 + prod 真浏览器验)**:archive-settings 530→434 / upload-camera 506→401 / folder-watcher 668→462 / core-boot 565→469 / erp-mappings 739→316 / email-ingest 726→452 / ocr-recognize 550→460 / erp-xero 663→475 / erp-exceptions 742→411 / excel-formula-recon 877→298 / test-center 706→404。commit `215bcb9..372381f` · prod `/api/version` 11850069→**11850080** · prod E2E:21 个 window 桥全 `function` + 零 console error。
- **三类范式([[c9-store-centralization-bankrecon]])**:① module-scope 抽内聚簇(纯工具走 ESM import·不污染 window) ② stateful IIFE → **store 中心化**(`S={}` · `_x→S.x` 词边界 subst) ③ 去 IIFE 变 ESM module(export 共享物给子模块)。verbatim:字节切片+dedent+subst · 逐行/字符多重集等价校验全 ==。顺手删 4 处死代码。
- **法律页**:`/terms` `/privacy` 此前是 prod 孤儿(未进 git)· 本窗口捞回 `static/{terms,privacy}.html` + 共享 `static/legal.css` · 重做标准界面(正文 verbatim · 邮箱还原 hello@pearnly.com)· prod 真浏览器验绿。
- **✅ 着陆页换新全部收工·上线**(REFACTOR-WB-landing · `e87f192..0e37f3f`):旧 `login.html` 4998 行巨石 → 28 行壳 · 资产入 `static/landing/`(全 ≤500)· 玻璃 logo 悬浮标 + 自绘自适应气泡 + 登录卡盖背景第二层 · **全站品牌 favicon + 侧栏 logo**(`static/brand/` 11 资产)· **猫猫互动音效**(猫头/logo=喵·盆栽=浇水·水杯=倒水·电脑=电脑音·音量随系统·音频 `?v=2` 破 immutable 缓存)· 热区全体对齐 + 缩放漂移修复 + **手机端布局修复**(min-height:0 解 914 撑爆)· /simplify 收口(提 `localCenter` 去重 + 删死代码 + `--badge-*` 变量)。资产 `?v=7`。**桌面源已退役 · repo `static/landing/` 为唯一源**(sync_landing.py 功成身退)。prod 桌面+手机真浏览器验绿 · 0 console err。
- **最后 commit `0e37f3f`**(全 push 上线 · prod 验绿)。**下一步(铁律#30 · 整顿最后一步)= 代码目录重组**:123 root .py → `app/{routes,services,core}` 包 · 前置「全文件 <500」已满足 · 全项目最大 blast radius · 文件集已冻结 → 一次性搬 + import 只改一遍。其后:闲置笔记本 staging(Wave3)。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
