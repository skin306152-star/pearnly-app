# 交接 · M3/M4 闭环施工完成(2026-07-02 · 分支 worktree-agent-m3m4-closed-loop)

> 面向接手窗口与验收。设计正本 `docs/agent/M3-M4-CLOSED-LOOP-DESIGN.md`(§ 引用指它)。
> 施工在独立 git worktree 分支,**未合 master、未部署**;新能力全部藏在默认关的闸后。
> 每个 commit CI 全绿(branch push 触发全部 job,lint-agent 已切 FAIL 硬门)。

## 一、你要的 / 已做的 / 还欠的

**要的(Zihao 2026-07-02 授权)**:按设计施工直到闭环,自做自检,push 盯 CI,自建模拟 LINE 对话压测。
两处开放点授权我拍板:① crash 时 L1 直录救援=做;② 无余额进大脑=不做(无计费口径、纯烧算力,
老路保留;要做时是一个 flag 的事,设计 §3.3-T3 留了位)。

**已做(全部 CI 绿)**:
| commit | 内容 |
|---|---|
| `2205e28a` | Phase 1 harness:82→124 条对抗语料 + 离线双套件回归(loop 直驱 + 入口全链)+ agent_sim 重写(修 stale API)|
| `ed38f540` | Phase 2 M4:push_status / rd_lookup / my_plan 三只读工具 + registry A 档接法声明({bucket,agent})+ lint-agent 切 FAIL |
| `b846431e` | Phase 3a:undo/edit 工具化 + 多笔直分发 + crash L1 救援 + **defer_edit 误记地雷修复**(闸 `agent_m3_tools` 默认关)|
| `06517232` | Phase 3b:推 ERP confirm-first 全套(备料→nonce 确认卡→postback→后台执行→三层幂等,闸 `agent_push_erp` 默认关)|
| `5f27c44d` | Phase 3d:T5 单一决策者(m3 开 → 旧 LLM understand() 物理退出灰度路)+ 契约测试 |
| (本 commit) | 压测 scripts/agent_stress.py(500+1000 轮混沌零违例)+ /simplify 收口 + 本交接 |

**还欠的(人类门,我不许抢跑)**:
1. **合 master + 部署**:分支未合;push 即上线,须 Zihao 拍板合并时机(注意与 MR.ERP 窗口协调)。
2. **开闸**:`agent_m3_tools` / `agent_push_erp` prod 全默认关。开法(超管跑):
   `store.set_setting("agent_m3_tools", {"rollout":"allowlist"}, True)` + allowlist 加灰度号 → 验稳再 all。
3. **真机 E2E**:记账写工具真机验证仍欠(需绑 LINE 的号);M3 工具/推 ERP 确认卡也要真机过一轮。
4. **推 ERP 真机放闸前**:确认 MR.ERP 直写链路已稳(push_to_endpoint 是共用入口,另一窗口在改内部)。

## 二、闸位与秒级回退(全 fail-closed:无记录/DB 异常=关)

| 闸(platform_settings key) | 管什么 | 关=? |
|---|---|---|
| `agent_enabled`(已有·prod all) | 前门大脑总闸 | 逐字节旧路 |
| `agent_write_tools`(已有·prod 开) | record_expense 直录 | 记账 defer 旧乐观路 |
| `agent_m3_tools`(新·默认关) | undo/edit 工具+多笔直分发+T5 单一决策者 | defer 交旧路(现状)|
| `agent_push_erp`(新·默认关) | 推 ERP confirm-first | 工具不可见,硬调得 not_available_yet 引导去 App |

代码级回退:各 Phase 独立 commit,可逐个 revert;crash L1 救援无闸(纯 fail-safe 增强,revert `b846431e` 内单段即可)。

## 三、本窗抓出的真问题(harness 的直接产出)

1. **defer_edit 误记地雷(已修+语料锁)**:「แก้รายการล่าสุดเป็น 80」「change the last one to 80」
   三个改错检测器全不认;模型 defer_edit 裁决被丢弃 → 老 L1 把"改成80"记成 ฿80 新支出。
   修 = `route_gated` 返回裁决串,入口尊重"模型已判=改错"。语料 `e-m3-off-edit-legacy-01` 回归锁。
2. **大脑故障期记账不可用(已修)**:crash 消费本轮导致供应商抖动时 "กาแฟ 50" 丢账
   (设计 §1.3)。修 = L1 确定性直录救援,四重否定守门(问句/改错形/收入/多笔不救),只直录永不反问。
3. **裸撤销/改错句到不了大脑**(记录,非 bug):correction 预路由(line_expense:68)确定性先接管
   ——这是好事;undo/edit 工具接的是检测器漏网的语句。语料 probe 已注明。
4. **scripts/agent_sim.py 曾整体失效**(stale API,§1.2-1),已重写;别再用旧用法。

## 四、验证资产(接手别重建)

- **语料**:`tests/agent_corpus/corpus.jsonl` 124 条(只加不删;线上翻车先加语料复现再修)。
- **离线回归**:`tests/unit/test_agent_corpus.py`(loop+entry 双套件,进全量 unittest=CI 闸)。
- **契约**:`tests/unit/test_agent_single_decider.py`(m3 开 → understand()==0 + 恰一出口)。
- **共享入口 harness**:`tests/unit/_agent_entry_harness.py`(真 L1 语义 + 真 loop,只 fake DB/出口/闸)。
- **混沌压测**:`python scripts/agent_stress.py --rounds 1000 --seed 7`(四不变量:不炸/单出口/
  无据不入账/单一决策者;500+1000 轮零违例)。
- **在线验收台**(prod 跑):`scripts/agent_sim.py --user <uid> --corpus tests/agent_corpus/corpus.jsonl`
  (真模型;`--write` 干跑只打印草稿绝不入账)。
- 单测计数:基线 5431 → 5499(+68,全绿)。

## 五、与设计的偏差(都有理由,验收时对照)

1. **M4 只做 3 工具**(push_status/rd_lookup/my_plan),ask_knowledge/books/erp_accounts 等
   走 registry `exempt:` 显式豁免——ask_knowledge 是计费型问答(฿0.50/答)不适合大脑自动触发,
   接入需单独报方案;文件导出类对话给不了附件。M4 闭环判据(§7)以"tool 或 exempt 全声明+闸 FAIL"达成。
2. **record_multi 不是模型工具**:多笔由确定性预判直接分发(模型无拆分权),比设计里"做成工具"更硬。
3. **推 ERP 真执行代码已写**(非 mock,镜像手动推权威范式 trigger="line_agent"),但闸默认关+分支未合
   = 没接线上真钱路;人类门=合并+开闸。nonce TTL 取 1h(mint API 粒度为小时,不为 15min 改共享 API)。
4. **executor 未拆 readonly/write 两文件**(现 ~300 行,<500 富余;拆分留到逼近上限)。
5. 无余额进大脑(T3)不做,理由见§一。

## 六、坑(血泪·本窗新增)

- worktree 内文件多为 CRLF:python 批量改必须 `newline=""` 读 + 归一 `\r\n→\n` 再匹配,否则多行
  pattern 永不命中(本窗踩了两次)。
- `line_quick_entry.py` 499/500、`line_correct.py` 491/500:一行都别往里加,新逻辑一律新文件。
- loop 的 scripted decide 测试桩签名用 `**kw` 收尾,loop 加 flag 参数不再连环炸。
- trigger="line_agent" 在推送日志 UI 的 trigger 过滤器(manual/auto)之外——日志能查到但下拉筛不出,
  UI 要不要加选项留后续(审计优先,先落库)。
