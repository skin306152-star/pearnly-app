# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-01 · 🎉 **5 大巨石全收官** + **模块化深化启动:auth_signup 2379→428** 〔均真账号 E2E 绿·已上线〕· prod 健康)

- **模式**:整顿封锁期 · 🎉 **最后一块巨石 app.py 完成 1731→491**(refactor_progress 代码规模 100%)。本窗口拆高敏 OCR 热路径(铁律 #26·Zihao 在场授权 R1+R2 连做):
  - **R1**(`5020d11`)`_handle_line_image_ocr`(LINE Bot OCR 后台)→ `services/ocr/line_image_ocr.py`·改 line_webhook_routes import。
  - **R2 逐刀**(`6537bef`/`60a1610`/`50f2b3d`/`6220197`)`ocr_recognize` 三段拆 → `services/ocr/recognize/{cache,persist,autopush}.py`,主路由 + `_choose_engine` → `ocr_recognize_routes.py`(495·APIRouter·`app.include_router`)·meta_aliases v1 别名改 import。**纯搬家 0 逻辑改**。
  - **R3**(`e0d94c9`)精简两段冗余墓碑注释 → app.py 505→491。
  - 新模块全 <500:routes 495 / persist 392 / cache 133 / autopush 94 / line_image_ocr 288。
- **🟢 末尾真账号 E2E 总验(prod·pearnly_e2e_1·Zihao 授权)全绿**:spec 16 OCR 识别热路径×2(缓存 16.9s + 非缓存真 Gemini 22.2s·登录→上传真发票→200+history_id+pages+台账动)、spec 11 扣费充值台账闭环、spec 09 充值弹窗、spec 05 异常栏 全 PASS。**6 commit 已 push 上线·pre-push 机械闸跑 2155 unittest 绿放行**。
- **R2 拆法范式(给后续高敏拆参考)**:① 逐刀 verbatim 抽(脚本 `newline=''` 保 app.py CRLF + 边界断言)② **ruff F821 兜底漏传参 / 漏返回**(cut1 漏 file_hash·cut2 漏 content/file_hash 全被 ruff 抓)③ **删 import 前查 re-export 契约**:`_async_run_exception_checks`/`_auto_push_*`/`_plan_permissions`/`_tid`/`import db` 全有 contract(test_*_contract / 测试 monkeypatch app.db)→ 保留 + `# noqa: F401` 别删 ④ 每刀全量 unittest。
- **🚀 模块化深化(2026-06-01 · Zihao 拍板「高敏先做·最简单排最后·我在场」)**:5 巨石外还有 24 个 .py >500(模块化进度卡 75%)。**已完成第 1 个最高敏:`auth_signup.py` 2379→428**(6 刀 `9cc24a9..4f5b737` 已 push 上线):cut1 密码找回/重置/改密 → `auth_password_routes.py`·cut2 OAuth 建号 → `services/auth/oauth_create.py`·cut3 超管工具 8 路由 → `auth_admin_routes.py`·cut4 `_ensure_schema` → `services/auth/schema.py`·cut5 共享 helper+常量 → `services/auth/signup_core.py`·cut6 link_line/get_my_plan → `auth_me_routes.py`·新模块全 <500。**纯搬家 0 逻辑改**。范式:路由组 lazy import 破循环(同 oauth_routes)、helper 模块 top-level import、auth_signup re-export 全名字(noqa)给 account_merge/team_routes/lazy 消费者、ruff F821 兜底缺参。E2E:spec 01 登录×2 + spec 13 改密核心断言全过(teardown flake 非回归)·14/17 失败测的是未动文件(line_binding_routes/auth_email_code_routes)非回归。**下个对象=按敏感度往下**(OCR core pipeline/layer2 等·见 [[wa-ocr-core-split-entangled]]·或 ERP/recon 普通块)。记忆 [[app-py-route-split-reexport-contracts]]。
- **🔑 部署 cache-bust 铁律**:静态资源 `Cache-Control: immutable max-age=30d`·改 `static/dist/main.js`(npm run build 后)/`static/i18n-data.js`/`static/home-NN.css` 后**必须 bump home.html 对应 `?v=`**,否则缓存用户拿不到(Playwright/Codex 无缓存→E2E 过≠真用户生效)。`/api/version` 从 `dist/main.js?v=` 自动读。整顿轮 bump `?v=` 但不重写 release_notes(记忆 [[refactor-skip-version-banner]] [[fe-cache-bust-vparam-required]])。
- **部署铁律**:改 src/*.js 必 `npm run build` + commit `static/dist` + bump `?v=`(纯后端 .py 免 build/免 bump);home.html/css/i18n-data.js 是 CRLF+prettierignored·禁 sed/prettier·只 Edit 或 Python `newline=''`;pre-push 机械闸跑 ruff/black/eslint(0 error)/build/check_ai_smell·本地 scratch 文件勿留。**E2E 部署后首跑常因后端冷启动登录瞬态失败·重试即过**。
- **防误推三重保险(高危·别动)**:mrerp_dms `auto_push` 强制 false · 不进发票抽屉推送列表(ocr-push.js 过滤)· push_to_endpoint 硬拒 `ERR_DMS_NOT_INVOICE_ENDPOINT` · 身份证自动推送另用 `config.id_card_auto_push`。计费 kind=pdf units=1 不污染发票额度。MR.ERP DMS 全链路闭环详见记忆 [[mrerp-dms-integration]]。
- **测试账号**:e2e_1/2/3 见 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`(e2e_1=`pearnly_e2e_1`/`Pe@rnly-E2E-1k9`·只读验证用·**无 DMS 数据**);Pearnly 真数据号 `18685123459@163.com`(谨慎·当前 401 勿反复试);DMS 测试站 `dmstest`/`dmstest`(只本地 env 注入)。
- **最后 commit**:`4f5b737`(auth_signup cut6·428)。本窗口两段:① app.py 巨石 `5020d11..e0d94c9`(6 commit) ② auth_signup 模块化深化 `9cc24a9..4f5b737`(6 commit)+ 文档·**全 push 上线·prod 健康·真账号 E2E 绿**。`git log --oneline -15` 查最新。**🎉 5 大巨石全收官**(home.js 0/home.css 0/db.py 344/home.html 397/app.py 491)+ auth_signup 428。**下个 task = 模块化深化继续**(Zihao 定的「高敏先做·按顺序」):剩 23 个 .py >500·按敏感度往下=OCR core(pipeline 751/layer2 850·[[wa-ocr-core-split-entangled]])→ ERP(mrerp_adapter 1909/erp_push 1518)→ recon(bank_recon_v2 6745 等)→ 简单报表最后。或切 ratchet fail([[ratchet-flip-not-low-risk]])/测试深化·等 Zihao 续指令。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
