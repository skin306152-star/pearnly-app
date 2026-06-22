# 交接 · 2026-06-23 「体积闸 + lint-ui 全绿」窗口(托管任务·已完成)

> 承接 `HANDOFF-2026-06-23-全检收口-未完成交接.md` 的 4 件未完成任务。Owner 托管过夜、要求全做完+自检+E2E+盯CI+push。
> 当前 prod = master `d7d92bd5` · 网站正常(/home 200、登录可用)。

---

## 一、4 个任务全部完成并上线

| 任务 | 状态 | commit |
|---|---|---|
| 1. 拆 `oauth_routes.py` 539→<500(登录主路径) | ✅ | `bb992db7` |
| 2. 拆 `erp_push.py` 507→<500(推送主路径) | ✅ | `bb992db7` |
| 3. lint-ui 三道闸归零 | ✅ | `65f7008d` |
| 4. 全闸+CI+push+E2E+收尾 | ✅ | 见下 |

### 任务1 — oauth_routes.py 539→213(登录)
- LINE 段(connect-line / line start / callback / `_handle_connect_line` / connect-state)整段抽到新 `routes/oauth_line_routes.py`(自带 APIRouter·`app.include_router`)。
- Google+LINE 共用的 HMAC OAuth state 签名 + `login_redirect_path` 抽到 `services/auth/oauth_state.py`。
- `test_oauth_state.py` 经 oauth_routes 的别名 import(`_gen/_verify/_oauth_state_secret`)**零改动**;`test_line_login_autobind.py` 改指 `oauth_line_routes`。
- **纯搬迁·0 业务逻辑改**。

### 任务2 — erp_push.py 507→410(推送)
- `build_mrerp_adapter` + `load_mrerp_mappings` 抽到 `services/erp/erp_push_adapters.py`,`erp_push.py` re-export(`push_dispatch`/`erp_export_routes`/测试经 `erp_push.<name>` 访问的契约不变)。

### 任务3 — lint-ui 三道闸(真相:handoff 的"220违规必须为0"说法有误)
- **check_ui_consistency**:B1/C1/B4 合计 220 < 基线 480 本就是过的;真正红的只有 **D2 黑底按钮=1**(基线0)。修:`.hd-tab.active::after` / `.dx-tab.active:after` 的激活下划线 `var(--ink)`→`var(--btn-blue)`。→ 绿。
- **check_theme_responsive**:暗夜 3位hex 251>246。修:`home-02-switcher.css` 5 处 `color:var(--ink,#111)` 去掉死代码兜底 `#111`→`var(--ink)`(`--ink` 在 home-01 已定义亮/暗双值·兜底在暗夜本就错)。→ 246=基线·绿。
- **ui_design_lint**:max-width 265>259、内联弹窗 177>174。**真相:两个 delta 全是误报**——max-width 增量是合法 `@media` 响应式(express/history 已上线功能的手机适配),内联增量是 `.drawer-decision-zone` 等**子选择器**被 `.drawer\b` 误匹配。「改回」会破坏已上线功能=错。**正确修法**:让正则兑现意图——max-width 加 `skipLineRe:/@media/i` 跳过 @media 行(265→125)、`.drawer\b`→`.drawer(?![-\w])` 不匹配子类(177→58),`--update-baseline` 把基线全部**往下收紧**(259→125 / 174→58 / 210→204 / 969→967·无放宽)。/simplify 的 altitude agent 独立确认这是「修准非放水」。

### 任务4 — 自检/E2E/CI/收尾
- **全单测**:本地 4638 全绿(skip3)。
- **prod 登录 E2E 冒烟**(拆分后真站验):`google/start`→302 跳 Google(带正确 client_id/state)、`line/start`→302 跳 LINE、坏 state→`oauth_error=invalid_state`、`connect-line/start` 免登录→401、`/home`/`/login`→200。**登录拆分端到端验证通过**(共享 state 模块跨路由生成+校验正常)。
- **额外修了 2 处 handoff 谎报的 pre-existing CI 债**(见下)。
- **/simplify 收口**(`d7d92bd5`):noqa import 收一行 + 恢复 home-02 误翻的 CRLF。跳过 `oauth_line_routes` 的 LINE token+verify 两处重复(pre-existing·碰登录回调·留交互验证的 follow-up)。

---

## 二、额外修复(handoff 三处谎报)
本窗口发现上一个 handoff 三处不实陈述,顺手修了两处真·CI 阻塞:
1. **「桌面图标已验证白底」=假**:Owner 截图是黑底。上窗口自己的 `_desktop_shot.png` 是白底→Windows 图标缓存没刷新或后来重装回退(companion 独立仓库封装外观·非本仓库代码)。**未处理**(见遗留)。
2. **「prettier(tracked全过)」=假**:8 个 `src/home/*.ts`(express/history/onboarding 近期功能)有超 printWidth=100 长行,CI lint job 一直红。`prettier --write` 折行(保 4-空格+CRLF·纯格式·dist minify 不变)→ `commit 3ceee172`。
3. **「单测 4638 全过」=假**:3 个 `test_proof_pdf` 在 CI 红(见下·非本窗口能修)。

---

## 三、CI 现状(prod HEAD `d7d92bd5`)
- ✅ **绿**:`lint`(black/ruff/**prettier**/eslint)、`lint-size`、`lint-ui`、`lint-debt`。**这 4 个本窗口从红转绿**。
- 🔴 **仍红(pre-existing·非本窗口任务·不能盲改)**:`import+i18n+unit+vite-build` job 的单测步——3 个 `test_proof_pdf` 失败。
  - 根因=**pymupdf lock 漂移**:本地 PyMuPDF 1.24.10 跑 proof_pdf 16 测试全绿;CI 用 lock 里 `pymupdf==1.20.2`(旧版嵌图 API 不同)→ 票图页产 0 页 → `test_three_docs_with_images_cover_plus_pages`/`test_every_page_has_page_number`/`test_image_page_has_header_strip` 红。
  - 这是记忆 [[pip-audit-14cve-repaid]] 早记录的**已知 lock 漂移**(「将来重 compile 须验 PDF OCR」)。在我动手前的 prod HEAD `ff70eb09` 那次 CI 就**一模一样红着**(已核实)。
  - **修法**(需 Owner/下窗口·非盲改):重 `pip-compile` 把 lock 的 pymupdf 升到 1.24.10 + 真验 LINE「本月凭证PDF」+ PDF OCR 不回归。盲改会冒险破坏已上线功能。

---

## 四、遗留(交 Owner / 下窗口)
1. **companion 桌面图标黑底**(Owner 截图):清 Windows 图标缓存试试(`ie4uinit.exe -show` 或重建 iconcache),仍黑则 companion 仓库 `D:\pearnly-companion` 的 `pearnly.ico` 没换对·需重打包。非本仓库代码。
2. **CI 单测 proof_pdf 红**:pymupdf lock 升级(见上·需验 PDF 功能)。
3. **/simplify follow-up**:`oauth_line_routes.py` 的 LINE token+verify 可抽 `_exchange_line_code`(~30 行·pre-existing 重复·建议带交互登录 E2E 时做)。
4. **lint-routes**(WARNING 模式·不挡):新 `oauth_line_routes.py` 可补一个契约测试。

---

## 五、本窗口 commit
- `bb992db7` 拆 oauth_routes/erp_push <500
- `65f7008d` lint-ui 三闸归零
- `3ceee172` prettier 折行 8 个 src/home/*.ts
- `d7d92bd5` /simplify 收口(noqa 收一行 + home-02 CRLF)
