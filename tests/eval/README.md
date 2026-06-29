# 银行对账 OCR 评测集(v118.35.0.65)

**目的**:让每次 OCR 改动都能用**数字**证明有没有提升、有没有引入新问题——而不是靠"感觉"或人肉抽查。这是把"还有很多未发现的问题"系统性挖出来的工具。

## 为什么需要它

OCR 是概率性的,改一个提示词/参数可能这里好了那里坏了。没有评测集,我们只能抽查几行就拍脑袋说"提升了"。有了它:
- 跑一条命令 → 得到「逐行召回率 X% / 笔数对不对 / 期末对不对」
- 改完再跑 → **对比数字**,确认是真提升还是按下葫芦浮起瓢
- 也是将来 **Gemini vs Document AI 打擂台**的裁判

## 隐私边界(重要)

| 内容 | 位置 | 进 git? |
|---|---|---|
| 运行器、比对逻辑、本说明 | `tests/eval/run_eval.py` `README.md` | ✅ 进 |
| 格式示例(假数据) | `tests/eval/ground_truth/example_synthetic.json` | ✅ 进 |
| **真实标准答案(真金额)** | `tests/eval/ground_truth_local/*.json` | ❌ gitignored |
| 真实账单样本 | `_bank_samples/` 或自定义目录 | ❌ gitignored |
| 运行结果 | `tests/eval/_runs/*.json` | ❌ gitignored |

## 标准答案 JSON 格式

放到 `tests/eval/ground_truth_local/<名>.json`(参考 `ground_truth/example_synthetic.json`):

```json
{
  "name": "AM_1-69",                       // 唯一名
  "file": "AM 1-69.pdf",                   // 样本目录里的文件名(或子串)
  "opening": 2786.33,
  "closing": 10786.33,
  "credit_count": 4,                       // 账单页脚印的存款笔数(强信号)
  "debit_count": 0,
  "total_credit": 8000.00,                 // 可选
  "total_debit": 0.00,
  "expected_rows": [                       // 可选 · 给了就算逐行召回率
    {"date": "2026-01-08", "deposit": 2000.0, "withdrawal": 0.0, "balance": 4786.33}
  ]
}
```

- **最低要求**:`file` + `credit_count`/`debit_count`(或 `closing`)。只填这些就能测"有没有漏行"。
- **完整**:再填 `expected_rows`,能算逐行召回率(最精确)。
- `expected_rows` 比对用 `(date, 净金额)` 宽松匹配,容差 0.05,不要求描述逐字一致。

## 怎么跑

```bash
# 扫描件 PDF / KBank 需要 Gemini key;BAY/SCB(坐标解析)/ xls 直读免费
set GEMINI_API_KEY=AIza...        # Windows: set / PowerShell: $env:GEMINI_API_KEY=
python tests/eval/run_eval.py --samples "D:/Users/Skin/Desktop/银行对账需求/银行账单模板"
```

输出每个文件的笔数/期末/逐行召回 + 汇总召回率,并写 `_runs/<时间戳>.json` 供回归对比。

## 已标注(`ground_truth_local/`)与待补

账单已搬到 `D:\Users\Skin\Desktop\银行对账需求\银行账单模板`(老路径 `…\账单` 已废)。

- ✅ 已标 **10 份**(笔数级,多按页脚核定):AM(含 4 笔 `expected_rows`)、BAY(314/31)、KBank(266/33)、KTB.xls(1117/215)、SCB(75/2)、AMK(41/3)、AMZ(8/20)、KKP(2/6)、KTB6694(0/0)、KBANK6787(0/1)。
- 跑 eval 应 **10/11 ✓**(唯一 AMZ 不过:Gemini 漏 1 笔,已告警)。
- ⬜ 可选继续补:各文件完整 `expected_rows`(逐行召回更精确)。

标注 `expected_rows` 时**以原始账单 PDF 为准逐行核对**,这是体力活但一次投入长期受益。

---

# 发票字段级 eval

银行侧上面那套测「行召回/笔数/期末」;发票侧此前只能肉眼比对 before/after。这里给发票
一个对等的尺子:同一份真值,任何一次抽取(线上 pipeline 或贴进来的 JSON)都能算出
**逐字段命中 + 钱权重加权分 + 钱字段精确率 + 关键字段漏判清单**。

## 为什么按权重而非平均

总额读错 40 倍(pur05:44.67 vs 真值 1780)和卖方名差一个空格,业务代价天差地别。
打分器(`invoice_scorer.py`)按读错代价给权重:总额=5、VAT/小计/税号/发票号/币种=2~3、
名称类=1。权重 ≥3 的字段读错计入 `critical_misses`。

## 隐私边界(同银行侧)

| 内容 | 位置 | 进 git? |
|---|---|---|
| 打分器 + 运行器 + 本说明 | `invoice_scorer.py` `run_invoice_eval.py` | ✅ 进 |
| 合成真值示例(假数据) | `ground_truth/invoices/example_invoice_synthetic.json` | ✅ 进 |
| **真票真值** | `ground_truth_local/invoices/*.json` | ❌ gitignored |
| 真票样本 | 自定义目录(`--samples`) | ❌ gitignored |

## 真值 JSON 格式

放 `ground_truth/invoices/<名>.json`(合成/脱敏)或 `ground_truth_local/invoices/<名>.json`(真票):
只填**要核对的字段**即可(最小可只给 `total_amount`);钱字段建议自洽 `subtotal+vat=total`。
字段名同 `ThaiInvoice`:`invoice_number / date / seller_tax / buyer_tax / subtotal / vat /
total_amount / discount / currency / document_type`,外加派生量 `items_count`(明细行数·测多票漏判)。

```json
{
  "name": "INV001", "file": "inv001.pdf",
  "total_amount": "1070.00", "vat": "70.00", "subtotal": "1000.00",
  "seller_tax": "0735527000289", "invoice_number": "IV6912-001", "items_count": 3
}
```

## 怎么跑

```bash
# A) 线上跑 pipeline(需 GEMINI_API_KEY · 扫描件才需要)
python tests/eval/run_invoice_eval.py --samples "D:/path/to/invoices"

# B) 离线打分:已有抽取结果(另一窗口跑出的 JSON)直接对真值打分,免 API
#    extracted.json 形如 {"<真值name>": {<ThaiInvoice fields>}, ...}
python tests/eval/run_invoice_eval.py --extracted before.json   # 换模型前
python tests/eval/run_invoice_eval.py --extracted after.json    # 换模型后 · 对比数字
```

打分逻辑(`invoice_scorer.py`)是纯函数,单测在 `tests/unit/test_invoice_scorer.py`,进 CI。
