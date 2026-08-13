# 交接 · 08-12 欠账清仓批收官 + 新发现账本(2026-08-13)

昨账本 `HANDOVER-2026-08-12-ctier-test-debts.md` 除「等拍板」「外部阻塞」外全部闭环:
A1 vat_report 400 根治(399dc7b1·PDF 当图片直塞 image_url,修在 http_common 组请求层,
生产复验 qwen3.7-flash status=ok)· B4 对账中心切 tab 卡死(af693769·runSeq 所有权票据,
顺治按钮死锁+旧 job 劫持视图两个真产品 bug)· 计费收口 P1×3+P2×4+P3×5+B3(a50d2d06·
净减 48 行·402 信封单源+契约测试·多页 PDF 预检按物理页数)· C5 额度抵扣标注两面
(1dbffa78)· C6 runner 盲等改条件等待(a22db5a1)· wrapup 文本同步(993129c9)。
六笔 CI run 31662919966 success,生产 99656ceb 健康 18s,巡检干净。
测试证据:`桌面 pearnly-local-ocr-stack/ctier-prod-test-2026-08-13/` + 会话 scratchpad 截图。

## A. 高敏(次日首批,主控方案+验收)

1. **🛑 账号灰度进不了异步对账 worker(A2 实弹揪出的真因,C 档切全局前必须堵)**:
   `set_principal(email)` 只在 HTTP 鉴权依赖(core/auth.py:351)设,contextvar 不进
   worker 线程——bank `/submit`→`recon_jobs/worker._run_one`→`engine_context("bank_statement")`
   不带 account,灰度号照走 Gemini(生产 ai_usage 实锤:skin306152 银行页 1.67 铢
   gemini-3.5-flash);旧同步 `/run` 的 `run_in_executor` 同病。gl-vat handler 同构同病。
   **08-12「入口普查:银行/GL/VAT 入口全部吃账号灰度」对异步对账车道不成立,以此为准。**
   修法=submit 时把 owner email 存进 job params,worker 开头 set_principal(或
   engine_context 显式带 account);同步路一并治。修完用 runner 银行入口复验
   ai_usage.model=qwen、成本≈1.15/页。
2. **ai_usage 归因缺失两处**:recon worker 行 tenant/user=NULL(worker 无上下文=已知);
   vat inline 路日志已 bind 租户但成本行仍 tenant=-(usage_context 没把绑定值带进
   log_ai_usage)。引擎成本页「未归因」桶持续进账,修归因时两处一起。

## B. 直派 worker

3. 「套餐内免费」旧文案三处同病(08-13 C5 只修了主站两面):
   `services/usage/billing_export.py` 导出 XLSX 计费列 / `static/dms/dms-billing-records.js`
   `dms-bill-rec-b-free` / admin 导出 CSV 无标注(description 列可读,低优)。
4. `tests/e2e/20-recon-step-resume.spec.js` 对 prod 存量红(与本批无关):侧栏「ลงบัญชี」
   组收起态,helper `openRoute` 点不可见子项超时;修=openRoute 前 `expandAllGroups()`。
5. `.claude/skills/verification/SKILL.md:21`「收尾跑全套机械闸」与铁律#2 新口径
   (10 秒自检)有张力,对齐一次。

## C. 记档(不施工)

- `src/home/recon-center-x.ts` 已 499 行贴 500 上限,下次动它先拆。
- `_save_excel_file` 服务层→路由层 import 被 `test_save_excel_file_stays_on_routes`
  契约测试钉死(先前拍板),计费收口批保留未动。
- `quota_pages_deducted` 是全租户聚合(ai_usage 与 credit_transactions 无关联键,
  按入口细分需新落点,设计取舍)。
- qwen 把「发票摞」喂 vat prompt 时多行发票拆逐行(行金额和=票面总额,字符级正确,
  行粒度语义问题非引擎错)。
- A2 实弹的 39/12546 匹配率是满量 GL 对单页对账单的拼配,测的是管线跑通非对账质量。

## D. 等 Zihao 拍板(沿袭+新增)

- (沿袭)163 余额 -92.98 冲正 / /ai 邀请去留 / C 档全局切换 / 真票验 C 档首单 /
  runner 进 CI 夜跑。
- (新增)**/ai 邀请名单与 qwen 灰度名单不重合**:唯一灰度号 skin306152 不在 /ai
  名单(vatcheck/fileconv/steward UI 对它全灭),唯一在 /ai 的 163 又不在灰度且余额负。
  要真 UI 验 /ai 侧 qwen,得让一个号两边都在。
- (口径)C 档切全局的前置由「A1+A2」更新为:**A1 已过;A2 改为堵上 A-1 灰度洞并复验**。

## E. 运维备忘

- W3 验证用的登录态=在 prod 上复用 skin306152 现役 jti 就地签发 token(零 DB 写、
  不轮换 jti、不踢现有会话、secret 不出机器),12h 自然过期,无需清理。
- skin306152 是计费豁免号(is_billing_exempt),验不了扣费链;扣费链证据=08-12 的
  163 号 402 实弹 + 本批 402 信封契约测试。
- 本批实弹总花费 ≈1.68 铢(银行 1.67 走了 Gemini 满价——正是 A-1 洞的实证;vat 两笔
  共 0.009 铢 qwen)。
