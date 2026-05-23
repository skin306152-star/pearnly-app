# 交接备忘 · 下窗口接手必读

> **最后更新**:2026-05-23(第七会话) · 当前版本 **v118.35.0.65** · cache bust **home.js?v=11835063**
> **本窗口主线**:银行对账 OCR 的**可信度攻坚** — 让用户能信任结果、把人工核对降到最低。
> **核心心法(别偏离)**:目标不是"OCR 0 误读"(物理上做不到),而是 **"0 静默错误"** —— 错的必标 ⚠、可数学反推的自动修正并标注、看不清绝不替用户猜。"没有 ⚠ = 可信"是要守住的铁律。

---

## 0. 一句话:我们在做什么

skin 今天搞到 **7 份真实泰国银行账单**(在 `D:\Users\Skin\Desktop\账单`),用它们逐一压测银行对账模块,发现并修复了一批会"误导用户/让用户兜底"的问题。这是一个**持续攻坚 OCR 可信度**的过程,不是一次性任务。skin 反复强调:**先摸清逻辑再改、别越改越乱、要诚实(做不到就说做不到)、用中文沟通。**

---

## 1. 🔴 本会话最重要的发现(下窗口必须知道)

**密集多页扫描件被系统性漏读 30–40%,而且此前从未被发现。**

- 通过新做的"完整性交叉校验"(对账单页脚印的笔数 vs 我们读出的笔数)实测:
  - **BAY 9789**:页脚印 314 笔存款 / 31 笔取款 · 我们只读出 **179 / 20**
  - **KBank 8477**:页脚印 266 / 33 · 我们只读出 **199 / 19**
- 为什么以前没发现:**余额链对"读出来的那部分"是自洽的**,所以漏掉整行不会破坏余额校验,⚠ 数量看着很低 → 假象。
- **根治方案 = 逐页识别再合并(见 §3 路线图 P1,这是下窗口 OCR 的头号任务)**。本会话先做到"检测到并主动告警",不让漏读悄悄溜过去。

---

## 2. 本会话已完成(v0.61–v0.65 · 全部已 push master · 已部署)

| 版本 | commit | 做了什么 | 测试 |
|---|---|---|---|
| v0.61 | `a80b054` | **对账结果诚实化**:diff=0 是会计恒等式假象(190 SCB 0匹配/185 仅1匹配都显示"差异0"染绿✓误导)→ 加"已匹配笔数/匹配率"、低匹配时 diff 不染绿+红字横幅。**多账户 .xls 分账户校验**(KTB 8258+8606 被并成一条余额链跳到 -737万 → 分账户独立校验)。GL 不匹配文案写进 Excel(此前只前端)。 | honesty 4 + multi_account 3 |
| v0.62 | `adea687` | **Gemini temperature=0**:根治"同图每次结果不同"(实测 BAY 212↔274 行 → 稳定 302=302)。**余额链自动修复金额** `_repair_amount_from_balance`:金额读错但前后余额能唯一反推时自动改(差异<30%才动 · 大额疑似漏行保持⚠)。修正行标"✎ 已修正"黄底(透明)。 | amount_repair 5 |
| v0.63 | `d0739fc` | **完整性交叉校验** `_audit_completeness`:页脚笔数/合计 + 期末平衡交叉对账 → 抓漏行(就是 §1 那个发现)。防 Gemini 把 closing 误填进合计字段(只信 count + 期末)。**持久化磁盘缓存** `_disk_cache_*`(跨重启/多worker一致)。max_output_tokens=32768。 | completeness 6 |
| v0.65 | `38b576b` | **OCR 评测集运行器** `tests/eval/run_eval.py`(让改进可量化 · 见 §4)。 | 手验跑通 |

**累计测试**:银行/对账/OCR 全绿(~135 passed)· i18n 0 缺失 0 多余 · release_notes 每次覆盖式更新。

---

## 3. 路线图(按优先级 · 可逐步完成 · 不要偏离)

> skin 已拍板:**做①②③(全免费),Document AI(④)先不做**,等量化后再决定。

### 🥇 P1 · 逐页识别再合并(头号任务 · 免费 · 根治 §1 漏读)
- **问题**:整份密集 PDF 一次性喂 Gemini → 它不逐行穷举,漏 30-40%。
- **方案**:把 PDF **按页拆开**(`PyMuPDF`/`pdfplumber` 渲染单页,或直接传单页 PDF),**每页单独让 Gemini 提取**(单页行数少→能读全),再**合并**(注意:期初只在第一页、期末/页脚汇总只在最后一页;去重用 row_hash)。
- **验收**:用评测集(§4)跑 BAY/KBank,逐行召回率应从现在的 ~60% 升到 90%+,完整性校验的 count_mismatch 应消失或大幅缩小。
- **风险/控成本**:N 页 = N 次调用 · 但有磁盘缓存兜底 · 且建议只对"完整性校验不过"的文件才走逐页(便宜页保持整份一次过)。
- **入口**:`bank_recon_v2.py` `_gemini_parse_statement`(改成可逐页)+ `parse_bank_statement_pdf`(触发条件)。

### 🥈 P2 · 标注评测集 + 量化(配合 P1)
- 见 §4。先标 AM(已起头)、BAY/KBank 页脚笔数,跑出 P1 改造前后的召回率对比。

### 🥉 P3 · few-shot 提示词(本会话**未做** · 中等价值)
- **为什么没做**:做好需要每家银行的"正确提取范例",仓促给坏例子会帮倒忙;且 §1 的漏读用 few-shot 解决不了(那是穷举度问题,P1 才治)。会话尾声改提示词还会再烧 Gemini + 风险。
- **怎么做**:在 `_gemini_parse_statement` 提示词里,针对已知格式(kbank/bbl/ktb)各放 1 个"这种版面应提成这样"的小范例(2-3 行 + 页脚)。用 §4 评测集验证是真提升再留。**改提示词记得 bump `_STMT_PROMPT_VER`**(否则旧缓存返回旧结果)。

### ④ Document AI 双引擎共识(skin 暂不做 · 留决策点)
- 谷歌专用文档 AI · 密集表格扫描件通常更准 + 每格带置信度 · 约 $30–65/千页。
- **正确用法**:不是换掉 Gemini,而是"第二个证人"——两个引擎都读,一致→高可信,打架→标⚠。
- **决策依据**:等 P1+P2 做完,用评测集让 Gemini vs Document AI 打擂台,用数字决定值不值这个钱。

---

## 4. 评测集怎么用(已建好 · `tests/eval/`)

```powershell
# 扫描件 PDF 需要 Gemini key;xlsx 免费
$env:GEMINI_API_KEY="AIza..."     # key 位置见 §6
python tests/eval/run_eval.py --samples "D:/Users/Skin/Desktop/账单"
```
- 标准答案放 `tests/eval/ground_truth_local/<名>.json`(**gitignored · 隐私**)· 格式见 `tests/eval/ground_truth/example_synthetic.json` + `tests/eval/README.md`。
- 已起头:`ground_truth_local/AM_1-69.json`(AM 页脚明确 4 笔)。**下窗口先把 BAY/KBank 的页脚笔数填进去**(BAY 314/31,KBank 266/33),就能量化 P1 的提升。
- 输出逐行召回率 + 笔数/期末是否吻合 + 写 `tests/eval/_runs/`(gitignored)。

---

## 5. 关键代码地图(银行对账 OCR)

- **`bank_recon_v2.py`**(核心 · 大文件):
  - `parse_bank_statement_pdf`:统一入口(route 对所有账单文件都调它 · 内部按扩展名分流)。文本/表格免费解析 → 不行才 `_gemini_parse_statement`(付费扫描件)。
  - `parse_bank_stmt_xlsx_direct`:xlsx/xls 免费直读 · **多账户分 sheet 解析 + 逐账户余额校验**(v0.61)。
  - `_gemini_parse_statement`:Gemini 调用(temp=0 · max_tokens=32768 · 内存+磁盘缓存 · 提示词版本 `v63-totals`)。
  - 余额三件套(顺序固定 · 都在 `parse_bank_statement_pdf` 收尾调):`_correct_direction_from_balance`(方向读反)→ `_verify_row_balances`(标 ⚠)→ `_repair_amount_from_balance`(自动修金额)。
  - `_audit_completeness`:完整性交叉校验(抓漏行)。
  - `_disk_cache_get/_put`:持久化缓存(目录 `PEARNLY_OCR_CACHE_DIR` · 默认 `cwd/.ocr_cache`)。
  - `reconcile`:3 层匹配引擎 → `BankReconRow` + `BankReconSummary`。
  - `export_bank_recon_excel`:导出(4 sheet · 顶部警告横幅 · 匹配率 · ✎已修正 标注)。
- **`recon_routes.py`**:
  - `bank_v2_run`(主路由):parse → merge → reconcile → 算 `brv2_warnings`(`_detect_recon_mismatch` + multi_account + completeness)→ 落库 → 返回。
  - `_BRV2_WARN` / `_brv2_warn`:4 语警告文案。`_completeness_details`:完整性 issue → 可读片段。
  - 导出端点:从落库的 `summary_json` 读 `_brv2_warnings` 重传给 export。
- **前端**:`home.js` `_brv2RenderWarnings`(警告横幅 · warnings 数组自动渲染 · 新增警告无需改前端)。

---

## 6. 测试用的 Gemini key / 真实账单(都在本地 · gitignored)

- **Key**:`_gemini_key.local/`(`新建文本文档.md` 里是 AIza API key · `pearnly-vision-key.json.json` 是 Vision 服务账号)。脚本里这样加载(**别打印 key**):
  ```python
  import re, os
  t = open(r'_gemini_key.local\新建文本文档.md', encoding='utf-8').read()
  os.environ['GEMINI_API_KEY'] = re.search(r'AIza[0-9A-Za-z_\-]{20,}', t).group(0)
  ```
- **7 份真实账单**:`D:\Users\Skin\Desktop\账单`(AM/AMK/AMZ/BAY/KBank/SCB 各 PDF + KTB .xls 双账户 + general ledger BANK.pdf 是 GL)。
- skin 说过"不要怕用谷歌额度去测",但**非确定性已被 temp=0 解决 + 有磁盘缓存**,别重复烧。

---

## 7. 必守铁律(`CLAUDE.md/CLAUDE.md` 全文 · 这里只列最容易踩的)

1. **任何改动先摸清背后逻辑**(skin 原话:"不要上了就改")· 诊断 > 编码。
2. **中文沟通**(别用日语/英语)· 对用户诚实("做不到"要直说 · 不画 100% 的饼)。
3. **release_notes 覆盖式 + 官方语言 + 无技术词**(铁律 §6 · 守门测试 `test_release_notes_no_history.py`)· 每次用户可见改动都更新 + bump `home.js?v=`(**只用 Edit 工具改 home.html · 绝不用 sed/python 写 · 否则 CRLF→LF 污染整文件**)。
4. **always on master · push 用户授权后让用户自己 `! git push origin master`**(harness 会拦)。
5. **整改期别污染巨型文件**:新逻辑进 `services/` 或独立函数 · 不堆进 home.js/app.py。
6. **i18n 改动跑 `python scripts/check_i18n.py --strict`**(0 missing 0 extra 才算过)。
7. **改 Gemini 提示词必 bump `_STMT_PROMPT_VER`**(否则缓存返回旧结果)。
8. **自动修正/猜测的红线**:只在**数学唯一可证**时自动改(如余额反推)· 真模糊一律标 ⚠ 不猜 · 改了必标"✎已修正"透明告知。

---

## 8. 收尾欠账 / 已知未解决

- **few-shot 提示词**(§3 P3)未做 · 已说明原因 + 怎么做。
- **逐页识别**(§3 P1)未做 · **这是下窗口 OCR 头号任务**。
- 评测集只起头了 AM · BAY/KBank/其余待标注(§4)。
- 那 11+15 个 `test_mrerp_*` / `chromium` 集成测试报错是**环境性既有问题**(需实时 ERP/浏览器)· 与本会话无关 · 别误判成回归。
- STATE_PEARNLY.md 已加本会话指针(见该文件顶部"第七会话")。

> **下窗口第一步建议**:读完本文件 → 跑 §4 评测集(填好 BAY/KBank 页脚)拿到当前召回率基线 → 动手 §3 P1 逐页识别 → 再跑评测集看提升。**始终用数字说话,别靠感觉。**
