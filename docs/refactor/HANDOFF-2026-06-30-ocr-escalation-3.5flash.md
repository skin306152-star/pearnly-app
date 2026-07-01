# HANDOFF · OCR 兜底升级到 gemini-3.5-flash（覆盖所有问题票路径）

> 接窗口先读这份。本文件自包含——所有生产事实均已 2026-06-30 在 prod 实测，**勿重新假设、勿重测模型选型**。
> 相关记忆：`pearnly-line-agent-model-selection`（模型选型定案 + 评测数据）。

## 目标（一句话）
让**每一个** OCR 入口在"首读出问题/低置信"时，稳定升级用 `gemini-3.5-flash` 再读一次。
覆盖范围：**发票、采购单、对账（银行 PDF/图片 + VAT 报表扫描件）、身份证**。
原则不变：**便宜首读 + 只在出问题时升级到贵的 3.5-flash**（不要让首读全量用贵的）。

---

## 已验证的生产事实（2026-06-30 实测，作为前提，勿推翻）
- 生产机 ssh 别名 `pearnly`（66.42.49.213）。app 目录 `/opt/mrpilot`，venv `/opt/mrpilot/venv`，
  服务 `mrpilot.service`（`uvicorn app:app --host 127.0.0.1 --port 7860 --workers 4`），env 文件 **`/opt/mrpilot/.env`**。
- 后端 `OCR_LLM_BACKEND=vertex`，区域 `asia-southeast1`，凭据 = `GOOGLE_APPLICATION_CREDENTIALS`(SA key)。
- **当前所有 OCR 模型档全是 `gemini-2.5-flash`**（flash / flashlite / fallback / escalate 一模一样）
  → 兜底=用同一个模型再读一遍=白读；且首读没吃到便宜档。
- 可达性实测（走生产 Vertex）：
  - `gemini-3.5-flash` ✅ ok=True（**可用**）
  - `gemini-2.5-flash`  ✅ ok=True（对照）
  - `gemini-2.5-flash-lite` ❌ error_kind=`provider`（Vertex SG **不提供** → 首读没法换更便宜的，维持 2.5-flash）
- 准度实测（5 张真采购票，人工核对真值）：`gemini-3.5-flash` **5/5**，修复 `gemini-2.5-flash` 在
  税号(多1位)、日期(错月)、7-11 总额(110 读成 290) 上的错 → 是当前最强兜底读者。

---

## 任务分两部分（可分开上线）

### Part 1 — env 改动（覆盖 7 个走"升级管线"的入口）
**受益入口**：发票 OCR 主管线、采购单 intake、LINE 图片 OCR、银行对账单 Gemini、银行 GL Gemini、
银行对账管线(非PDF)、对账 job workers —— 它们都经 `gemini_models.fallback()` 读 `OCR_FALLBACK_MODEL`。

改 `/opt/mrpilot/.env`：
```
OCR_FALLBACK_MODEL=gemini-2.5-flash   →   OCR_FALLBACK_MODEL=gemini-3.5-flash
OCR_ESCALATE_MODEL=gemini-2.5-flash   →   OCR_ESCALATE_MODEL=gemini-3.5-flash
```
**保持不动**：`OCR_FLASH_MODEL` / `OCR_FLASHLITE_MODEL` = `gemini-2.5-flash`（首读便宜；flash-lite 404 用不了）。

步骤：① `cp /opt/mrpilot/.env /opt/mrpilot/.env.bak-20260630` ② 改这 2 行 ③ `systemctl restart mrpilot.service`
④ 验证：`systemctl is-active mrpilot` = active；跑附录 probe，确认 3.5-flash ok=True。
成本影响：仅触发兜底的 ~10% 票按 3.5-flash 计价（≈ +$3.5/万张），其余不变。**完全可逆**（改回 + 重启）。

### Part 2 — 代码补漏（3 个直调入口：一次性 flash、无升级，env 管不到）
照搬 **`services/recon/bank_stmt_gemini.py:151`（`_gemini_parse_statement` 用 `try_with_fallback`）** 的写法，
给以下入口加"首读失败/结果不可用 → 升级 `fallback()`(=OCR_FALLBACK_MODEL=3.5-flash)"：

| 入口 | 文件:行 | 现状 | 重要性 |
|---|---|---|---|
| 身份证 / DMS | `services/ocr/id_card_extract.py:99` `_gemini_vision_extract` | tier=`flash_lite` 一次性 | 客户身份 |
| VAT 报表扫描 PDF | `services/vat/vat_parser_gemini.py:288` `parse_with_gemini` | tier=`flash` 一次性 | **金额** |
| VAT 批量 OCR | `services/vat/vat_ocr_batch.py:110` `_ocr_batch` | tier=`flash` 一次性 | **金额** |

写法：`gemini_models.try_with_fallback(call, primary=<flash()/flash_lite()>, ok=<判结果可用的 predicate>, label=...)`，
`call` 内部按 `tier_for_model(model)` 调 `transport.multimodal_to_json`。升级目标自动 = `OCR_FALLBACK_MODEL`。

**不动**（非"看图读金额"，可选不做）：`vat_file_classifier.py`、`vat_ai_analyzer.py`(纯文字)、`importer/ai_mapping.py`(Excel列名)。
**禁止**：把 `OCR_FLASH_MODEL` 全局改成 3.5-flash —— 会让每张票首读都用贵的，违背"便宜首读+只兜底升级"。

---

## 约束（铁律，必须遵守）
- 整顿封锁期：本任务是**已授权**的 OCR 钱路径改动，方案已定（本文档）= 已"先报方案"。
- **改完必须真验证再 push；未验收不 push master**。push 即上线，注意 mrpilot 重启抖动（4 workers，几秒）。
- 每个改动文件配 **≥1 测试**（断言：首读返回空/不可用 → 升级被调用且用 fallback 模型）。
- Conventional Commits，提交署名 `Opus 4.8`。
- Part 1(env) 与 Part 2(code) 可分批；env 先上不依赖 code。

## 验证清单
- Part 1：附录 probe 打印 `control gemini-2.5-flash: (True,...)` + `test gemini-3.5-flash: (True,...)`；重启后服务 active；
  抽一张会触发确定性层的难票走线上，确认日志显示升级到 3.5-flash。
- Part 2：单测覆盖"主读空→升级触发→fallback 模型生效"；各取 1 张低质量真票（VAT 扫描 PDF、身份证）回归。

---

## 附录 · 生产可达性 probe（只读 + 一次最小调用，不改任何配置）
本机（Windows，ssh 别名已配）执行；脚本自动继承生产进程的完整环境（凭据/项目/区域）：
```python
# probe.py
import os, sys, glob, traceback
def load_app_env():
    for d in glob.glob("/proc/[0-9]*"):
        try: raw = open(d + "/environ", "rb").read()
        except Exception: continue
        if b"OCR_LLM_BACKEND" in raw and b"GOOGLE_APPLICATION_CREDENTIALS" in raw:
            for part in raw.split(b"\0"):
                if b"=" in part:
                    k, v = part.split(b"=", 1)
                    os.environ[k.decode("utf-8","replace")] = v.decode("utf-8","replace")
            return d
    return None
load_app_env(); sys.path.insert(0, "/opt/mrpilot")
from services.ai_gateway import transport as t
def probe(model):
    os.environ["OCR_FALLBACK_MODEL"] = model; os.environ["OCR_ESCALATE_MODEL"] = model
    try:
        r = t.text_to_json("Return a JSON object with one field named status whose value is the string ok", tier="fallback")
        return (getattr(r,"ok",None), getattr(r,"model",None), getattr(r,"error_kind",None))
    except Exception as e:
        return ("EXC", repr(e))
print("control gemini-2.5-flash:", probe("gemini-2.5-flash"))
print("test    gemini-3.5-flash:", probe("gemini-3.5-flash"))
```
运行（本机 git-bash）：
```
base64 -w0 probe.py | ssh -o BatchMode=yes pearnly 'base64 -d > /tmp/probe.py && cd /opt/mrpilot && /opt/mrpilot/venv/bin/python /tmp/probe.py'
```
预期：两行都 `(True, '<model>', None)` → 可达，安全。
