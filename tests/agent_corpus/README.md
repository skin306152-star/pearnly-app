# Agent 对抗语料库(永久回归资产)

一组语料(JSONL),两个跑法(设计:`docs/agent/M3-M4-CLOSED-LOOP-DESIGN.md` §4):

- **离线(CI 闸)**:`tests/unit/test_agent_corpus.py` 读取本目录所有 `*.jsonl`,
  把 `script` 注入模型决策层,跑**真实
  路由代码**(loop 循环 / slots 接地 / 多笔守门 / 出口护栏 / 兜底 / LINE 入口分流),断言终态。
  测的是管道:模型给出任何输出(含故障输出),路由与护栏行为全对。
- **在线(prod 验收台)**:`scripts/agent_sim.py --corpus tests/agent_corpus/corpus.jsonl`
  忽略 `script`,真模型真跑,人眼评模型判意图的那一半。

## 行 schema(JSONL)

```
id        唯一名(cat-lang-序)
cat       类目(emotion/playful/negation/.../fault/entry-*)
suite     loop = 直驱 loop.handle_turn;entry = 驱动 line_expense.handle_expense_text 全链
lang      zh/th/en/ja(期望回复语言,离线走 detect_text_lang 真代码)
text      用户消息原文
write     loop 套件:写子闸开关(缺省 true)
history   喂给 loop 的对话记忆(缺省 [])
script    模型决策脚本,按步弹出:
            {"step": {kind,tool,args,message,say,reason}}   直接给 LoopStep
            {"outcome": {ok,data,raw}}                       给假 ProviderOutcome,
                                                             走真 _parse_step/救援(故障注入)
          step.message_repeat=[片段,次数] 展开成重复串(失控输出用)
tools     canned 工具结果 {handler: {ok,data,error_code}};record_expense 恒走真实执行器
          (真金额接地),未 canned 的只读工具被调用 = 语料 bug,runner 直接报错
flags     entry 套件:{enabled, write}
understand entry 套件:旧大脑 understand() 的桩返回(null=None)
expect    断言(见 runner);must/must_not 查终态文本;records=入账次数;
          decide_calls=模型被问次数(0=确定性前置拦下,模型根本没上场)
online_only true = 离线跳过(纯模型质量探针,如 711 金额风险)
probe     一句话:这条在防什么
```

## 铁律

- 语料只加不删。线上每翻一次车,先加一条复现语料(红),再修(绿)。
- `corpus.jsonl` 放手写/事故复现语料;`generated_matrix.jsonl` 放多语言矩阵扩面语料。
- `expect.records` 与金额断言是钱路红线:否定/假设/情绪/缺金额/编造金额 一律 0。
