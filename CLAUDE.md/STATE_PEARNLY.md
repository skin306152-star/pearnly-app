# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-01 · **整顿主线 C3 进行中** · R15~R20 抽 8 modal + 删 1 死 modal · home.html 1495→1171 上线 prod 11850058)

- **模式**:整顿封锁期 · **整顿主线 C3 进行中**(Zihao 2026-06-01 拍板:DMS 全链路收尾闭环 → 回整顿)。**当前 task = C3 拆 home.html → <1000**:本窗口 R15~R20 后 **1171**(还差 ~171)。下个候选:`page-ocr`(~150·识别主页·高耦合·**留最后·需先查 OCR 主流程 eval 期是否引用其内部元素**·最接近达标的单块)/ `email-modal`~155〔牵涉 `line-email-modal.js` 🔴高敏·跳过〕/ 其余零散 on-demand modal/page 占位。**app shell(顶栏~128/侧栏~143)boot 关键勿轻动**。孤儿 i18n key(billing-modal-title/help/google-open)R19 删 markup 后留存·无害·可日后清(需 bump i18n-data.js?v=)。
- **✅ MR.ERP DMS 例外任务全链路闭环**(commit tag `MRERP-DMS-INTEGRATION`·非整顿):① 集成上线(身份证→订车单·Playwright 真登录+表单契约·防误推三重保险)② Codex 3 轮 UI 复测全 PASS(首轮 6 缺陷+二轮 R5/R7+隐藏地址全修)③ 推送可视化 UX(推送日志/异常栏 ERP 下拉筛选 + 身份证订车按 DMS 字段〔订车单号/客户/身份证末4〕展示 + 4 语友好错误不裸露 ERR_* + 详情/弹窗 DMS 标签)④ 导航文案统一(上传发票→上传识别 / 发票记录→识别记录·4 语)。**全程发票推送零改动**·全量 2153 + prod E2E 绿。详见记忆 [[mrerp-dms-integration]] + 交接 `docs/integrations/mrerp-dms-integration-handoff.md`。
- **C3 进度封存**:home.html 1730→**1171**(本窗口 R15~R20 共 **-324**·抽 8 modal/drawer + 删 1 死 modal):R15 `#bank-cand-drawer` `277b377` + R16 `#client-modal-mask`+`#wsclient-modal-mask`→`modal-client-edit.js` `bf42884` + R17 `#camera-tips-modal`+`#bank-client-picker-modal` `d773424` + R18 `#endpoint-modal`→`endpoint-modal-html.js` `6264f2a`(⚠️erp-integration 无守卫 IIFE·import 严置其前) + **R19 删死 markup `#billing-modal-mask` `83099ee`(纯删·免 build/免 bump)** + **R20 `#pearnly-confirm-modal`+`#confirm-modal`→`confirm-modals-html.js` `9af4783`(showConfirm/pearnlyConfirm·纯 on-demand+守卫)**(更早 R13 `#page-history`/R14 `#onboarding-modal`)·抽出均字节等价〔脚本提取+校验模板===git HEAD inner〕+prod E2E 验〔R16/R20 真浏览器开弹窗·R17/R18 查 wbInjected+子元素〕)。范式见记忆 [[wb-src-home-c3-split-playbook]](留空壳 + `*-html.js`/`modal-*.js` eval 注入 inner + 子树初译 + import 置消费模块前;消费模块 load()/_bindOnce/DOMContentLoaded/on-demand 守卫绑定→eval 注入恒早于首次绑定·非竞态)。app.py 1731→500 仍卡 auth 专窗口(剩高敏 @app·需 Zihao 在场)。
- **🔑 部署 cache-bust 铁律(今日血泪·必守)**:静态资源 `Cache-Control: immutable max-age=30d`·改 `static/dist/main.js`(npm run build 后)/`static/i18n-data.js`/`static/home-NN.css` 后**必须 bump home.html 对应 `?v=`**,否则缓存用户拿不到(Playwright/Codex 无缓存→E2E 过≠真用户生效)。`/api/version` 从 `dist/main.js?v=` 自动读·bump 版本必配 4 语 release_notes(`meta_aliases_routes.py`·铁律 #6)。详见记忆 [[fe-cache-bust-vparam-required]]。
- **部署铁律**:改 src/*.js 必 `npm run build` + commit `static/dist` + bump `?v=`(纯后端 .py 免 build/免 bump);home.html/css/i18n-data.js 是 CRLF+prettierignored·禁 sed/prettier·只 Edit 或 Python `newline=''`;pre-push 机械闸跑 ruff/black/eslint(0 error)/build·本地 scratch 文件勿留(会被扫)。**E2E 部署后首跑常因后端冷启动登录瞬态失败·重试即过**。
- **防误推三重保险(高危·别动)**:mrerp_dms `auto_push` 强制 false · 不进发票抽屉推送列表(ocr-push.js 过滤)· push_to_endpoint 硬拒 `ERR_DMS_NOT_INVOICE_ENDPOINT` · 身份证自动推送另用 `config.id_card_auto_push`。计费 kind=pdf units=1 不污染发票额度。
- **测试账号**:Pearnly 真数据号 `18685123459@163.com`/`xiaopi19950730..`(谨慎);e2e_1/2/3 见 `C:\Users\skin3\Desktop\pearnly_test_accounts.txt`(e2e_1=`pearnly_e2e_1`/`Pe@rnly-E2E-1k9`·只读验证用·**无 DMS 数据**·DMS 真实视觉须 skin306152 眼验);DMS 测试站 `dmstest`/`dmstest`(只本地 env 注入)。
- **最后 commit**:`9af4783`(C3 R20 抽两个全局确认弹窗 inner→运行期注入 · REFACTOR-WB-C3 · bump `?v=` 11850057→11850058)· `git log --oneline -8` 查最新。**均已 push 上线·prod 11850058 健康**。**整顿轮 cache-bust:仍 bump `?v=` 保缓存正确,但不重写 release_notes(Zihao 2026-06-01:纯重构忽视新版本横幅·见记忆 [[refactor-skip-version-banner]])**。home.js 拆迁全收官 33768→0(范式 [[home-js-batch-split-bridge]])。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
