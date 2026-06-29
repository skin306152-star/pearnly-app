# 交接 · OCR 准度「确定性闸」一批(2026-06-29)

> 起因:Vertex 切换实测复盘(只换门·模型/输出/速度全没变)+ 谷歌 25 真票归档,
> 钉出结论 —— **模型不是瓶颈,确定性兜底层才是**。本批不动模型/不动 prompt/不动热路径
> 抽取行为,只在抽取**之后**加确定性闸 + 给每次改动一把硬数字尺。
> 根因全文见记忆 `ocr-determinism-layer-root-cause` / `selfhost-ocr-recipe-archive`。

## 落地了什么(5 commit · 已 push master)

| commit | 内容 |
| --- | --- |
| `2de550eb` | ① 发票字段级评测 harness(`tests/eval/invoice_scorer.py` 打分器 + `run_invoice_eval.py` 运行器 + 合成真值) |
| `1e3e2105` | ②a 发票合理性硬闸 `services/ocr/sanity.py` + page_runner 接线 |
| `69e6ab6c` | 打分器钱字段 `0 ≡ 空` 等价(非税票无 VAT 行不误判) |
| `ff5f58b7` | ②c 银行两法分歧守门 `services/recon/bank_arbitration_guard.py` |
| `9bae051f` | /simplify 收口:共享解析 `services/ocr/money.py` + 分歧独立键 + glob 预缓存 |

### ① 评测 harness — 给改动一把硬数字尺
- **为什么**:发票侧此前只能肉眼比对 before/after;换模型/改 prompt/补闸是真提升还是
  按下葫芦浮起瓢,没有逐字段证据。银行侧早有 `run_eval.py`,发票侧补齐对等尺。
- **打分器**按业务代价加权(钱=5、税号/发票号=2~3、名称=1):总额读错 40 倍和卖方名
  差一个空格,代价天差地别,不能等权平均。
- **隐私边界**:打分器/运行器/合成示例进 git;真票真值 `ground_truth_local/` + 跑批结果
  `_runs/` 全 gitignored。

### ②a 合理性硬闸 sanity(triggers.py 的洞 → 强制转人工)
诚实边界:抓「**结构上不可能**」的错,不抓「语义选错列且无明细佐证」(pur05-44.67 那类
需供应商历史量级基线,是另一道闸)。4 条规则,每条都保守(宁漏抓不误杀):
1. 负数金额(credit_note 例外)
2. 卖方税号 == 买方税号(串了表头税号)
3. 总额 < 最大单行小计且无折扣(选错列)
4. **洞④**:缺 VAT 但小计/总额对不上 —— `净额 = 小计 − 折扣`,总额须 ≈ 净额 或 净额+7%。
   ★必须减折扣,否则误杀 7-11 折扣票(小计 115 − 折扣 5 = 总额 110)。

### ②c 银行两法分歧守门
免费解析 vs Gemini 两法对账结果对不上(异号必分歧 / 同号超 5% 相对阈值)→ 标
`method_divergence` + 转人工,不静默二选一。只在两法 row_count 都 > 0 时比对。

## 验证(没误杀 + 真提升)
- 10 份真值**逐张回核打印面值**,钱字段 100% 正确(含 BBL 透支账户 closing=0.00 这种
  反直觉真值 —— 教训:**别拿被告当法官**,真值只认打印面值,不靠多次解析投票)。
- 复现 0.63 → 0.9448,钱字段 20/20(真值修正后)。
- 闸逐条验「不误杀」:折扣票(②a 规则4)、非税票无 VAT 行(打分器 0≡空)均不触发。
- 每个新文件均带单测(`test_ocr_sanity` 15 例 / `test_bank_arbitration_guard` 6 例 /
  `test_ocr_money`)。

## 还没做(显式存档·非遗漏)

### 准度侧残留
- **②b 发票号斜杠归一**:已知残差(`119/2560` vs `879/2566` 格式),本批不碰。
- **②c live true-positive**:守门逻辑已单测;线上真触发验证留待 prod/vertex(本地缺
  Vision SA 凭据跑不通整条发票 pipeline)。
- **供应商历史量级基线闸**:抓 pur05-44.67 那类语义选错列(★仅当明细行在场时 ②a
  规则3 才拦得住;整张漏读明细则兜不住),需攒供应商历史,另起。

### 速度侧 · 整半未动(原始需求是「准度 + 速度」,本批只交准度半)
识别单张耗时本批**零改动**,与改前完全一致。慢的根子 = L3「看图复读」过度触发 →
9–61s 长尾(见 `docs/smart-intake/09`)。三个提速口子,**均未做**:
1. **收窄 L3 触发(主力杠杆)**:砍长尾。★前置已就位 —— 本批的 ②a sanity 硬闸 +
   ① 评测 harness 正是安全网:收窄触发后用 harness 守准度不掉,即便偶尔放过坏票
   sanity 兜底转人工。**没有这层安全网不该盲砍 L3**。改点在 `triggers.py` 升级判断。
2. **换更轻模型档**:flash-lite 更快,但 SG Vertex 门 404(见 `ocr-llm-backend-gateway`)
   → 需换门/换区,非纯代码改。
3. **网页上传异步化**:体感快(不阻塞),不改识别本身 —— 另一窗口方案
   `docs/refactor/PLAN-gap4-web-ocr-async.md` 待批。

> 下一步最直接 = 口子 1(用本批 harness 守着收窄 L3),把准度+速度的另一半补齐。

## CI 备注(向前盖)
`9bae051f` 的 /simplify 抽出 `money.py`(+34·DRY 去重·sanity.py 同步 -16)与
`bank_recon_v2.py`(+5·新增 method_divergence 键)是正当增长,但漏在该 commit message 标
`RATCHET-EXEMPT` → lint-size 棘轮红。已 push 不可 amend(master 禁强推),本交接 commit
「向前盖」:棘轮逐 commit 跑 `HEAD~1..HEAD`,增长落入 base 后不再计入 diff。

RATCHET-EXEMPT: services/ocr/money.py +34 · DRY 抽共享解析(sanity.py 同步净减)· 永久
RATCHET-EXEMPT: services/recon/bank_recon_v2.py +5 · 新增 method_divergence 分歧键 · 永久
