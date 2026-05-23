# 交接备忘 · 下窗口接手必读

> **最后更新**:2026-05-23(第八会话) · 当前版本 **v118.35.0.67** · cache bust **home.js?v=11835067**
> **本窗口主线**:接着第七会话的可信度攻坚 —— 用 skin 的真实账单跑评测集 + 14 份全量实测、修问题、再跑,把银行对账闭环。
> **核心心法(别偏离)**:目标不是"OCR 0 误读"(物理上做不到),而是 **"0 静默错误"** —— 错的必标 ⚠、可数学反推的自动修正并标注、看不清绝不替用户猜。"没有 ⚠ = 可信"是要守住的铁律。

---

## 0. 一句话:我们在做什么

skin 把真实泰国银行账单**全部搬到了 `D:\Users\Skin\Desktop\银行对账需求\银行账单模板`**(老路径 `D:\Users\Skin\Desktop\账单` 已废)。用它们逐一压测、修问题、再压测,持续攻坚对账可信度。skin 反复强调:**先摸清逻辑再改、别越改越乱、要诚实(做不到就说做不到)、用中文沟通。**

**第八会话(本窗口)结论**:把第七会话以为"必须烧钱逐页 OCR"的头号任务,用**免费**手段根治了(含原以为做不到的 KBank);再做 14 份全量实测,逐行核对导出件,确认真 OCR 错误率极低且全部被主动告警。

---

## 1. 🔴 本会话最重要的发现(下窗口必须知道)

**那些"被漏读 30-40%"的密集件(BAY/KBank)其实是『内嵌文本 PDF』,不是扫描图!已全部免费根治。**

- 第七会话以为它们是扫描件、只能逐页喂 Gemini。实测页数/文本量发现:**BAY 9789(24页)、KBank 8477(7页)都内嵌了完整文本**,真正的扫描图(BBL/KBANK6787/KKP/KTB6694)反而都只有 1 页。
- 漏读真因:`get_text()` 线性化后**丢了列的 x 坐标** → 存/取无法区分(BAY 314 笔存款被全判成取款)→ 余额链坏 → 触发 Gemini → Gemini 再漏读。
- **根治 = 坐标感知文本解析**(`_parse_stmt_text_coords`,两套策略 + 按余额链可信度取优):
  - **表头法** `_coords_by_header`:BAY **314/31 100% 命中**、SCB 救回 77 行 —— 免费、确定、还省了 Gemini 钱。
  - **数据驱动 x 聚类** `_coords_by_xcluster`:攻克 KBank 的"存取合并列"——金额 x 聚类找列、最右簇=余额、方向由余额涨跌定。**KBank 8477 从 199/19(Gemini 漏读)→ 266/33 完全正确,且 Gemini 调用 0(免费)。**
- 安全闸门:坐标解析只在 `_stmt_bad_ratio` 余额链可信时才被采用,认错列/漏行 → 链对不上 → 弃用回退,**不会引入静默错误**。

---

## 2. 本会话(第八)已完成(v0.66–0.67 · 全部已 push master · 已部署)

| 模块 | 做了什么 | 测试 |
|---|---|---|
| **KTB 多账户 .xls 静默错误修复**(v0.66) | `KTB 8258 และ 8606.xls`:① 归零户期末真 0 被 `str(c or "")` 当空丢掉 → 误报 3845.3(真值 0);② 期初汇总区被清空 → 改用首笔『余额−净额』反推(真值 39.15);③ .xls 路径过去无完整性校验 → 加逐账户期末交叉校验产出 `completeness`。修后两链对平、零误报,反向注入漏行能被抓到。 | multi_account +2 |
| **坐标感知文本解析**(v0.66–0.67) | `_parse_stmt_text_coords` 两套策略按余额链可信度取优:`_coords_by_header`(BAY 314/31、SCB 77 行)+ `_coords_by_xcluster`(KBank **266/33** · 攻克存取合并列)。全免费、Gemini 调用 0。 | coords +3 |
| **期初/期末兜底回填**(v0.67) | Gemini 不回传 opening/closing 时(AM:4 笔全对但期初期末显示 0)→ 从 B/F 行 + 末行余额数学补回。PDF 路径统一兜底。 | eval 验证 AM 期末 10786.33 |
| **缺页醒目提示**(v0.67) | 页脚印的笔数 ≫ 读到的(BBL 只上传末页)→ 完整性提示明确追加『疑似缺页·请确认上传完整页数』(4 语)。 | 验证 BBL2645 触发 |
| **评测集 10 份标准答案(P2)** | `ground_truth_local/`:AM/BAY/KBank/KTB/SCB(75/2)/AMK(41/3)/AMZ(8/20)/KKP(2/6)/KTB6694(0/0)/KBANK6787(0/1) —— 多数页脚核定。 | eval 10/11 ✓ |

**14 份全量实测**(路 3 · UI 同款后端 → 导出 Excel 到 `probes/_ui_downloads/` → 逐行核对):见 §4 表。**真 OCR 引擎错误仅 2 处**(AMZ 漏 1 笔、BBL2645 误读 1 笔扫款行),且**全部被完整性校验主动告警**;2 份 BBL 是"源文件只含末页"(引擎没错)。
**累计测试**:全单元 **402 passed**(0 失败)· bank/recon/coords/completeness/fuzz 全绿 · i18n 0/0 · release_notes 4 passed。

---

## 3. 路线图(按优先级 · 可逐步完成 · 不要偏离)

> skin 已拍板:**做①②③(全免费),Document AI(④)先不做**,等量化后再决定。

### 🥇 P1 · 密集件读全(第七会话头号任务)→ **✅ 完成**
- **原计划**(第七会话):逐页喂 Gemini。**已作废**——这些件是文本 PDF(§1),坐标解析更优。
- **已落地**:`_parse_stmt_text_coords` 两套策略。**BAY 314/31、KBank 266/33、SCB 77 行 —— 全免费、Gemini 调用 0、链全对平**。无核心剩余项。

### 🥈 P2 · 标注评测集 + 量化 → **✅ 基本完成(10 份)**
- 见 §4。已标 AM/BAY/KBank/KTB/SCB/AMK/AMZ/KKP/KTB6694/KBANK6787,多数按页脚核定。eval 跑 10/11 ✓(唯一 AMZ 因 1 笔漏读不过,已告警)。
- 待补(可选):各文件完整 `expected_rows`(逐行召回更精确)。

### 🥉 P3 · few-shot 提示词(**未做 · 评估后认为当前性价比低**)
- 现状:Gemini 路径的文件(AM/AMK/AMZ/KKP/KTB6694/KBANK6787/BBL)除 AMZ 漏 1 笔外都正确。
- **为什么暂不做**:改 `_gemini_parse_statement` 提示词会**让全部 Gemini 文件的缓存失效、需重跑验证**(烧 Gemini),且为修 AMZ 这 1 行有回归其余 5 个正确文件的风险。AMZ 那 1 笔已被完整性告警 → 不是静默错误。**做之前先用 §4 评测集量化证明真提升再留**;改了必 bump `_STMT_PROMPT_VER`。

### ④ 外部 OCR 引擎 / 双引擎共识(决策点 · 见 §9 模型评估)
- 仅对**真正的多页密集扫描件**(若用户上传完整版)才有价值;文本 PDF 已被坐标解析免费解决,扫描件目前 Gemini 够用。
- 候选与取舍见 **§9**(skin 问的 Qwen2.5-VL / PaddleOCR-VL / Document AI 对比)。**用法是"第二个证人"交叉验证,不是替换**;先用评测集打擂台、用数字决定。

---

## 4. 评测集怎么用(已建好 · `tests/eval/`)

```powershell
# 扫描件 PDF / KBank 需要 Gemini key;BAY/SCB/xls 免费
$env:GEMINI_API_KEY="AIza..."     # key 位置见 §6
python tests/eval/run_eval.py --samples "D:/Users/Skin/Desktop/银行对账需求/银行账单模板"
```
- 标准答案放 `tests/eval/ground_truth_local/<名>.json`(**gitignored · 隐私**)· 已标 10 份(见 P2)。
- **14 份全量实测最终结果**(2026-05-23 · 导出件在 `probes/_ui_downloads/`):

  | 文件 | 结果 | 真值 | 状态 |
  |---|---|---|---|
  | BAY_9789 | 314/31/末500 | 314/31 | ✅ 免费 100%(原 ~57%) |
  | KBank_8477 | 266/33/末391684 | 266/33 | ✅ 免费(原 199/19) |
  | KTB_8258_8606(.xls) | 1117/215/末−717万 | 同 | ✅ 免费 |
  | SCB_3171 | 75/2/末286825.59 | 75/2 | ✅ |
  | AMK_1-69 | 41/3 | 41/3 | ✅ |
  | KKP_2805 | 2/6/末319983.53 | 2/6 | ✅(图上 END OF STATEMENT) |
  | KTB_6694 | 0/0/末26.89 | 0/0 | ✅(休眠户) |
  | KBANK_6787 | 0/1/末0 | 0/1 | ✅(期初100→手续费100) |
  | AM_1-69 | 4/0/末10786.33 | 4/0 | ✅(v0.67 期初期末已回填) |
  | **AMZ_1-69** | 9/19/末82178.75 | 8/20 | ❌ Gemini 漏 1 笔(已告警 · 间歇余额 · 坐标法不可行) |
  | BBL 2645 | 17 笔(读对) | 页脚 318 | ⚠️ **源文件只含第 8/8 页** · 已提示缺页 |
  | BBL 2697 | 10 笔(读对) | 页脚整份 | ⚠️ **源文件只含第 2/2 页** · 已提示缺页 |

- **结论**:13 份对账单,行级内容准确率 ≈99.9%(读出 ~2177 行,真错 2 行:AMZ 漏 1 + BBL2645 误读 1 笔扫款行)· 整份完全可信 11/13 · 真错全部被主动告警。
- 输出逐行召回率 + 笔数/期末是否吻合 + 写 `tests/eval/_runs/`(gitignored)。

---

## 5. 关键代码地图(银行对账 OCR)

- **`bank_recon_v2.py`**(核心 · 大文件):
  - `parse_bank_statement_pdf`:统一入口(route 对所有账单文件都调它 · 内部按扩展名分流)。文本/表格免费解析 → 不行才 `_gemini_parse_statement`(付费扫描件)。
  - `parse_bank_stmt_xlsx_direct`:xlsx/xls 免费直读 · **多账户分 sheet 解析 + 逐账户余额校验**(v0.61)· **v0.66 加期末 0 归零户修复 + 空期初数学反推 + 逐账户期末交叉校验(产出 `completeness`)**。
  - **`_parse_stmt_text_coords`(v0.66 新)**:坐标感知内嵌文本解析 · `_coord_find_columns` 从表头(y 容差聚合)定位 取/存/余额 列 x · 金额按 x 归列 · 跨全部页。**密集文本 PDF(BAY/SCB)免费 100% 召回的根治**。存取合并列(KBank)返回空交回上层。接在 `parse_bank_statement_pdf` Step 4c(Gemini 前)· `_stmt_bad_ratio` 把关。
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
- **真实账单(已搬新路径)**:`D:\Users\Skin\Desktop\银行对账需求\银行账单模板`(AM/AMK/AMZ/BAY/BBL2645/BBL2697/KBANK6787/KBank8477/KKP/KTB6694 各 PDF + KTB 8258/8606 .xls 双账户 + SCB · `general ledger BANK.pdf` 是 GL)。**老路径 `D:\...\账单` 已废**。
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

- **AMZ 1-69 漏 1 笔**(取款 20→19)· Gemini 在"间歇余额+混列"密集文本件上漏读 · **已完整性告警**。坐标法不可行(只 18/29 行印余额,无法逐行校验)· 真要修走 P3(改 Gemini 提示词,性价比低)或人工。
- **BBL 2645 / 2697 源文件只含末页**(8/8、2/2)· 引擎读对了那一页 · 已提示"疑似缺页"· 修法 = 用户上传完整页。BBL2645 另有 1 笔扫款行被读成存款(已告警)。
- **few-shot 提示词**(§3 P3)未做 · 评估后认为当前性价比低(见 §3)。
- 评测集 `expected_rows`(逐行召回)可继续补(§4 已有 10 份笔数级标注)。
- 那批 `test_mrerp_*` / `chromium` / `test_erp_test_connection_*` 报错是**环境性既有问题**(需实时 ERP/浏览器)· 时过时不过(故称"偶发")· 与银行对账无关 · 别误判成回归。

> **下窗口第一步建议**:读完本文件 → 跑 §4 评测集拿基线(应 10/11 ✓,AMZ 唯一不过)→ 若要再提升,先用评测集量化证明,别凭感觉换模型/改提示词。**始终用数字说话。**

---

## 9. 外部 OCR 模型评估(skin 问:Qwen2.5-VL 72B / PaddleOCR-VL 值不值?)

**结论:基于当前实测证据,暂不值得引入;先拿到"真正的多页密集扫描件"用评测集量化再决定。**

- **现状瓶颈不在 OCR 模型**:文本 PDF(含最难的 BAY/KBank)已被坐标解析免费、100% 解决;单页扫描件(KBANK/KKP/KTB6694)Gemini 已读对。残留问题是 ① AMZ 漏 1 行(文本件,换模型未必更好)② BBL 缺页(用户上传问题)—— **都不是换 OCR 模型能解决的**。
- **Qwen2.5-VL 72B**:强开源 VLM,文档/表格不错。但 72B 自托管要 2×A100 级 GPU(基建成本高),走 API(DashScope/OpenRouter)成本与 Gemini 相当。泰文不如 Gemini 成熟。**不构成替换 Gemini 的明显理由**;可作"第二证人"做共识,但加成本。
- **PaddleOCR-VL**:版面/表格结构识别强、本地便宜。但**泰文识别弱于 Gemini**,且不懂语义(存/取要后处理)。对泰文银行账单不明显更好。
- **正确做法(别凭感觉换)**:① 先收集一份**完整的多页密集扫描**账单(目前手上的"密集件"几乎都是文本 PDF 或单页);② 用现有 Gemini 跑,看是否真漏读;③ 若真漏,把 Qwen/Paddle/Google Document AI 接进 `tests/eval/run_eval.py` 与 Gemini **打擂台**,用召回率数字决定;④ 即便引入,定位是"双引擎共识/第二证人"(一致→高可信,打架→标⚠),不是替换。
