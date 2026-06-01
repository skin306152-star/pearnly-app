# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-01 · 🎉 **5 大巨石全收官** + **OCR 抽取核心 pipeline/layer2 双双 <500 收官**〔真账号 field-diff E2E 双票全绿·已上线〕· prod 健康)

- **模式**:整顿封锁期 · 模块化深化。**本窗口拆 OCR 抽取算法核心(全项目最娇贵·铁律 #26 高敏·Zihao 在场授权三刀连做 + 每刀自跑 field-diff E2E)**。三刀全 **verbatim 搬家**(AST/字节比对 identical·非纯文本搬家但 0 逻辑改),`WA_OCR_CORE_SPLIT_PLAN` 标的的「真重构」刀:
  - **L2-P**(`4e21891`)7 个 prompt 字符串常量 → 新 leaf `services/ocr/layer2_prompts.py`(AST literal 7/7 byte-identical)· layer2_structure 850→580 · 新 test_layer2_prompts_contract。
  - **L2-B**(`efd6fc4`)`_call_gemini_with_retry` → 并入 `layer2_gemini.py`(prompt 改引 layer2_prompts 叶子)· layer2_structure 580→**455 <500** · **翻** test_layer2_gemini_contract 锁「函数现在 gemini + re-export 同一对象」。
  - **P-D**(`7efbfea`)`_process_one_page`+`_process_pages`+`OCR_PDF_PAGE_WORKERS` → 新 leaf `services/ocr/page_runner.py`(两函数 AST identical)· pipeline 751→**464 <500** · 删 14 个仅被搬走函数用的 import(逐一核验非 re-export 契约)· **Step2 单测 patch 目标改 page_runner**(_process_pages 内部经 page_runner 命名空间;Step3 run_on_image 仍经 pipeline 命名空间·不改)· 新 test_pdsplit_contract。
- **🟢 真账号 field-diff E2E 双票全绿(prod·pearnly_e2e_1·非缓存真 Gemini·铁律 #26 授权)**:**INV2026030004** subtotal 3750 + vat 262.50 = total **4012.50**(VAT 7%)·items 5·2 页·chains=[text,L2]×2 **无 L3** ✓;**INV2026030010** 4 页·page2=[text,L2,L3] **触发 L3**(与 P-B 轮 L3 口径一字不差)·subtotal 9940+vat 695.8=10635.8(7%)·items 9 ✓。8 字段 0 漂移·L3 触发口径不变。**3 commit `4e21891..7efbfea` 已 push 上线·pre-push 机械闸跑 2164 unittest 绿放行**。
- **拆法范式(高敏 verbatim 搬家·给后续 OCR-core/recon 参考)**:① Python 字节切片(自动探测 LF/CRLF·边界 assert·错即中止)② **AST/literal 比对证 0 逻辑改**(搬函数比 ast.dump、搬常量比 ast.literal_eval)③ **monkeypatch 陷阱**:tests `patch.object(M, fn)` 的目标随被搬函数的「调用方命名空间」走——_process_pages 搬走→patch 改 page_runner,但 run_on_image 留 pipeline 故 patch 仍 pipeline(记忆 [[app-py-route-split-reexport-contracts]])④ 删「未用」import 前 grep 外部 `from X import` 查 re-export 契约 ⑤ 每刀 ruff+black+import app+全量 unittest+assertIs 契约,一组拆完真发票 field-diff E2E。
- **R2/auth 拆法范式(上窗口·仍适用)**:逐刀 verbatim·ruff F821 兜底漏传参/漏返回·删 import 前查 re-export 契约(noqa F401 别删)·路由组 lazy import 破循环。
- **🔑 部署 cache-bust 铁律**:静态资源 `Cache-Control: immutable max-age=30d`·改 `static/dist/main.js`(npm run build 后)/`static/i18n-data.js`/`static/home-NN.css` 后**必须 bump home.html 对应 `?v=`**,否则缓存用户拿不到(Playwright/Codex 无缓存→E2E 过≠真用户生效)。`/api/version` 从 `dist/main.js?v=` 自动读。整顿轮 bump `?v=` 但不重写 release_notes(记忆 [[refactor-skip-version-banner]] [[fe-cache-bust-vparam-required]])。
- **部署铁律**:改 src/*.js 必 `npm run build` + commit `static/dist` + bump `?v=`(纯后端 .py 免 build/免 bump);home.html/css/i18n-data.js 是 CRLF+prettierignored·禁 sed/prettier·只 Edit 或 Python `newline=''`;pre-push 机械闸跑 ruff/black/eslint(0 error)/build/check_ai_smell·本地 scratch 文件勿留。**E2E 部署后首跑常因后端冷启动登录瞬态失败·重试即过**。
- **防误推三重保险(高危·别动)**:mrerp_dms `auto_push` 强制 false · 不进发票抽屉推送列表(ocr-push.js 过滤)· push_to_endpoint 硬拒 `ERR_DMS_NOT_INVOICE_ENDPOINT` · 身份证自动推送另用 `config.id_card_auto_push`。计费 kind=pdf units=1 不污染发票额度。MR.ERP DMS 全链路闭环详见记忆 [[mrerp-dms-integration]]。
- **测试账号**:e2e_1/2/3 见 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`(e2e_1=`pearnly_e2e_1`/`Pe@rnly-E2E-1k9`·只读验证用·**无 DMS 数据**);Pearnly 真数据号 `18685123459@163.com`(谨慎·当前 401 勿反复试);DMS 测试站 `dmstest`/`dmstest`(只本地 env 注入)。
- **最后 commit**:`7efbfea`(P-D pipeline 464)。本窗口 3 commit `4e21891..7efbfea` 全 push 上线·prod 健康·真账号 field-diff E2E 双票全绿。`git log --oneline -10` 查最新。**🎉 OCR 抽取核心 pipeline 1044→464 / layer2_structure 981→455 双双 <500 收官**(全项目最娇贵代码·真账号字段比对 0 漂移)。仅剩 L2-C(layer2 抽取算法本体·已 <500 非必须·留进一步解耦再议)。**下个 task = 模块化深化继续**(Zihao「高敏先做·按顺序」):**ERP** mrerp_adapter 1909 / erp_push 1518 → **recon** bank_recon_v2 6745 等 → 简单报表最后。或切 ratchet fail([[ratchet-flip-not-low-risk]])/测试深化。剩 ~20 个 .py >500(模块化进度卡仍 75%·按文件数算)。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
