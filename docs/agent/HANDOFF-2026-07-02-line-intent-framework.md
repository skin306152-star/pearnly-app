# HANDOFF · LINE 意图框架(LI)· 2026-07-02

> 设计正本:`docs/agent/LINE-INTENT-FRAMEWORK-DESIGN.md`(Zihao 拍板方向:理解用户发图/
> 说话的目的,对 Pearnly 能力,带能力反问,确认后实现,遇阻告知引导——通用框架,LINE 侧)。
> 分支 `worktree-agent-line-intent`,每 commit CI 绿。网页 Agent(旧 M5)继续搁置未动。

## 交付了什么(LI-0 ~ LI-5)

| 块 | 内容 | 状态 |
|---|---|---|
| LI-0 | 总设计(意图模型/四终端/钱路红线/施工顺序) | ✅ |
| LI-1 | 决策核 `services/agent/image_intent.py`(纯逻辑)+ 16 条 image 语料进 CI | ✅ |
| LI-2 | 接线:`line_image_route.intercept`(line_image_ocr 唯一挂点·499/500)+ 四终端 + `plan_incoming_doc` 工具 + `line_pending_intents` 表(话先图后)+ 新闸 `agent_image_intent` 默认关 | ✅ |
| LI-3 | 反问/多轮语料锁死(7 条:查无端点回真实列表反问·反问后只答名字的多轮补全·闸关矫正·入口全链)★顺手抓出真 bug:slots 把列表槽压成 `"['x']"` 字符串(已修) | ✅ |
| LI-4 | 遇阻引导审计:**目录已存在,零新代码**(agent.failure.* 每条自带下一步·LI-2 文案带指路·反问喂真实资产)——不造活凑数 | ✅(审计) |
| LI-5 | 决策核 500 轮确定性混沌进 CI(三不变量)+ 全量 5629 绿 + 本交接 | ✅ |

## 用户能干什么(闸开后)

```
"ใบต่อไปส่งเข้า MR.ERP เลย ไม่ต้องบันทึก" → 发图 → 不记账,直接出推送确认卡
"下一张记到มานะชัย那套账"              → 发图 → 记进指定套账
"รูปหน้าไม่ต้องทำอะไร"                 → 发图 → 只识别不落账(费照现行口径)
什么都不说发普通票                       → 和今天一模一样自动记账(主流量零打扰)
"推到 SAP"(没这端点)                  → 回真实端点列表反问 → 答 "MR.ERP" → 计划拼全
```
推送永远确认卡把关(M3/M4 已真机验证的那套机械,原样复用)。

## 闸位与回退(秒级)

- `agent_image_intent`:**prod 未创建 = 默认关**,关=图片路逐字节现状(gate 契约测试+混沌不变量锁)。
- 开法:allowlist 先放测试号 → 真机验 → all。回退:关闸/收名单;逐块 revert 均可。
- 新表 `line_pending_intents`(首用 ensure 自愈建·apply_tenant_rls·TTL 15min 单发单用)。

## 诚实偏差与记债(别让下个窗口踩)

1. **图先话后的推送盲区(记账租户)**:发图默认记账走 purchase_docs 不写 ocr_history,
   事后说"推刚才那张"定位不到(推送机械只认 history)→ 诚实报找不到。当前解法=用户
   **事先**说(plan)或说"都要"(both 写载体行)。根治(记账路同写载体或推送认 purchase_docs)
   动现状主路,单独报方案。
2. **图片侧大脑问询(ambiguity consult)留插座未通电**:decide 恒 summary=invoice,
   身份证在上游 not_invoice 就被拦、低置信有现成草稿卡兜着——通电价值低,LI-3 语料里
   大脑越权矫正等红线已锁,等真实需求再开。
3. **push 载体行不挂异常 hook**(重复票预检/5 类规则):载体行只为推送;推送侧自有
   匹配闸/VAT 闸/去重。若要求载体行也进异常栏,补挂即可。
4. LI-4 无新代码(见上表)——是"已存在"不是"没做"。

## 真机验收剧本(人类门·闸开 allowlist 后)

1. LINE 发:`ใบต่อไปส่งเข้า MR.ERP เลย ไม่ต้องบันทึก` → 应回 ack(计划已存)
2. 发一张采购/销项发票图 → **不应出现记账卡**,应直接出推送确认卡(票号/金额/端点)
3. 点确认 → "正在推送" → 成功回执;MR.ERP TEST2019 列表见新单
4. 再发:`รูปหน้าไม่ต้องทำอะไรนะ` → 发图 → 只回识别摘要,查 DB 零新账
5. 什么都不说发一张普通票 → 与今天行为完全一致(记账卡)
6. 15 分钟后再发图(计划过期)→ 默认记账(不粘住)

## 坑(本窗踩的)

- black 会把多参调用展开:接缝写完必跑 `check_file_size`(踩过 501)。
- slots `model_freeform` 原本 str() 压平列表槽(已修·测试锁)。
- 语料 JSONL 尾行换行风格要跟文件一致;PYTHONUTF8=1 常备。
- RATCHET-EXEMPT 逐文件写进 commit message,新文件也算净增。

## 新债豁免声明(2026-07-02 · master 向前盖)

`line_intent_store.ensure_table` 命中 lint-debt 反模式 #5(运行期建表)。豁免理由:本仓 LINE 侧
新表的既定 dual-run 惯例(prod 无 alembic 钩子 → 首用 ensure 自愈;`line_action_nonces`/
`line_voice_quota` 同款先例),alembic `0045_line_pending_intents` 已留档。分支逐 commit 闸
因 LI-2 run 被后续 push 取消而漏扫,merge 全量 diff 在 master 炸出 → 本 commit 补声明转绿。
