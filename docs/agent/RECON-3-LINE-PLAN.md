# 三个对账 → LINE Agent · 方案(依次落地)

> 2026-07-02 · Zihao 拍板顺序②:三对账依次出方案、依次落地。
> "三个对账"=对账中心三 tab(src/home/recon-center-x-store.ts:33):
> M4 银行对账(bank_recon_v2_task)· M3 收入对账(gl_vat_task)· M2 销项税报告核查(vat_recon_tasks)。
> 另有「自动做账·银行对账」(/api/bank-recon/*·写凭证)是第四样,不在本程序内。

## 共同原则

- Agent 侧全部先做**只读**(概览+明细钻取),复用各 store 现成 list/get 函数,不动对账计算一行。
- 明细上限 N 条(默认 5)防刷屏;数字全来自工具结果(钱路红线);空数据诚实引导去网页跑。
- 触发对账(收文件→起任务)是**写路**:双文件配对+计费+异步完成通知,须建"收件配对"底座——
  放在方案一(银行)先建,二/三复用。每步闸 fail-closed,新闸独立可回滚。
- 验收一律:单测+corpus+模拟舱+prod 真数据 E2E(测试租户先用真实样例文件把三种任务各跑出 ≥1 条)。

## 方案一 · M4 银行对账(已有概览 → 补明细 + 收件触发)

现状:recon_overview 只报最近任务 matched/unmatched 计数;对账单图已有靶向引导(PR#38)。

1. **明细钻取** `recon_detail`:问"哪些对不上/差在哪"→ 最新(或按银行名/文件名定位)任务的
   unmatched 明细(读 bank_recon_v2_task.detail_json,截前 N 条:日期+金额+方向+侧别)+ 锚点四余额。
2. **收件触发(收件配对底座)**:LINE 收到银行对账单(已能认出)→ 不再只引导去网页,改问
   "要现在做银行对账吗?还需要 GL 总账文件和科目号"→ 检查点存暂存件(照 _stage_uploads 落盘+TTL)
   → 用户补发 GL 文件、报科目号 → 起异步 job(复用 /api/recon/bank-v2/submit 的服务层)→
   job 完成回推结果概览(job runner 补 LINE 通知钩子·失败人话)。
   若 X:只发了一个文件超时 15 分钟 → 那么 Y:作废并告知;若 X:科目号答非数字 → 追问一次。
   新闸 agent_recon_intake 默认关。
3. 计费口径:与网页同(recon.create 权限口径),起任务前预检余额,不足如实拦。

## 方案二 · M3 收入对账(GL 收入科目 ↔ 销项税报告)

零接入 → 接读:

1. `recon_overview` 扩三档:一次返回 bank/income/tax 三类各最近 3 条计数摘要
   (income 用 list_gl_vat_tasks,与 bank list 同形状),大脑按用户问的档位成文;
   问法含糊("对账结果怎样")→ 三档都给一句。回执兜底文案扩三档(agent_i18n↔i18n-data.js key parity 同步)。
2. `recon_detail` 扩 income 档:diff/unmatched 明细来自 gl_vat_task.detail_json(科目+期间+两侧金额+差额)。
3. 触发:复用方案一收件配对底座,文件对=GL+销项税报告,job_type=glvat(二期,底座验稳后开)。

## 方案三 · M2 销项税报告核查(销项发票 ↔ 销项税报告)

零接入,且有两套实现 → **选 A 路径 vat_recon_tasks**(与对账中心 tax tab 同源;
旧 reconciliation_task/row 屏留网页,Agent 不碰):

1. `recon_overview` 补 tax 档:get_vat_recon_tasks_kpi(现成 KPI 汇总:任务数/matched/mismatched/差额)
   + list_vat_recon_tasks 最近 3 条(期间+客户+配错计数)。
2. `recon_detail` 补 tax 档:mismatched 明细来自 raw_data_json(票号+两侧金额+差额,截 N 条)。
3. 触发:同二期,文件对=销项发票批+报告,job_type=salesvat。

## 落地顺序与验收门

- PR 按方案一→二→三依次;每个 PR:单测+corpus(+2/档)+模拟舱+prod E2E(真任务数据)→ merge → 放量。
- 方案一的"收件触发"体量最大,若单 PR 过大拆两个(读明细先行,触发随后),顺序不变。
- 全程不动 recon 计算/网页路由行为;Agent 层坏了=关闸回现状。
> 2026-07-03 · /simplify 收口(PR#52):效率/复用/高度四角审查已应用;记债项与触发条件见桌面清单。
