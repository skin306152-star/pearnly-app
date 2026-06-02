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
- **着陆页换新(进行中·另窗口在设计)**:新设计 = 纯登录一屏(桌面 `pearnly_landing_layered_*` · 营销内容以后加屏)· 接入脚手架 `scripts/sync_landing.py` 就位(只读桌面·只写仓库·--dry-run 验过)· **旧 login.html(豁免 5000)待新设计定稿 → 原子 swap 替换**(删旧+上新同 commit·零空窗·先本地反代验登录再 push)。
- **最后 commit `9523012`**。下一步候选:① login 换新(新设计好→跑 sync 脚本+本地反代验+原子 swap) ② **代码目录重组**(123 root .py → app/{routes,services,core}·铁律#3·前置「全 <500」刚满足) ③ 闲置笔记本 staging(Wave3)。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
