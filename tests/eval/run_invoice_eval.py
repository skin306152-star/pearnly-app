# -*- coding: utf-8 -*-
"""发票字段级评测运行器(银行侧 run_eval.py 的发票镜像)。

让发票识别的每次改动(换模型 / 改 prompt / 补确定性闸)都能用**逐字段硬数字**
证明是真提升还是按下葫芦浮起瓢 —— 不再靠肉眼比对 before/after。

两种模式:
    # A) 线上跑:对样本目录里的发票真跑 pipeline(需 GEMINI_API_KEY)
    python tests/eval/run_invoice_eval.py --samples "D:/path/to/invoices"

    # B) 离线打分:已有抽取结果(另一窗口跑出的 JSON)直接对真值打分(免 API)
    #    extracted.json 形如 {"<真值name>": {<ThaiInvoice fields>}, ...}
    python tests/eval/run_invoice_eval.py --extracted runs/before.json
    python tests/eval/run_invoice_eval.py --extracted runs/after.json   # 再跑一次比对

真值放:
    tests/eval/ground_truth/invoices/<名>.json          # 合成/脱敏 · 进 git
    tests/eval/ground_truth_local/invoices/<名>.json     # 真票真值 · gitignored

真值格式见 README「发票字段级 eval」段 + ground_truth/invoices/example_invoice_synthetic.json。
"""

import argparse
import datetime as _dt
import glob
import json
import os
import sys

try:  # Windows 控制台默认 GBK · 强制 UTF-8 防中文/符号崩
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(__file__))

import invoice_scorer as sc  # noqa: E402

_HERE = os.path.dirname(__file__)
_GT_DIRS = [
    os.path.join(_HERE, "ground_truth_local", "invoices"),  # 真票真值(gitignored · 优先)
    os.path.join(_HERE, "ground_truth", "invoices"),  # 合成示例(git)
]
_RUNS_DIR = os.path.join(_HERE, "_runs")
# 真值里这些键不是发票字段,是定位/元信息,不喂打分器。
_META_KEYS = {"name", "file", "_comment", "pages", "notes"}


def _load_ground_truth():
    """读所有发票真值 · 同名 _local 优先。返回 {name: gt_dict}。"""
    gts = {}
    for d in reversed(_GT_DIRS):  # 先读 git 示例 · 再用 local 覆盖同名
        for f in sorted(glob.glob(os.path.join(d, "*.json"))):
            try:
                gt = json.load(open(f, encoding="utf-8"))
                gts[gt.get("name") or os.path.basename(f)] = gt
            except Exception as e:
                print(f"  [skip] {f}: {e}")
    return gts


def _expected_fields(gt: dict) -> dict:
    """剥掉元信息键,留纯发票字段真值喂打分器。"""
    return {k: v for k, v in gt.items() if k not in _META_KEYS}


def _find_sample(sample_files, gt):
    """在【预缓存的】样本文件名里按 gt['file'] 精确/子串匹配(目录只 glob 一次·非每条 gt)。"""
    target = gt.get("file") or gt.get("name") or ""
    if not target:
        return None
    for f in sample_files:
        if os.path.basename(f) == target:
            return f
    tl = target.lower()
    for f in sample_files:
        if tl in os.path.basename(f).lower():
            return f
    return None


def _extract_live(sample_path: str, api_key: str) -> dict:
    """真跑 pipeline → 取主票 fields(同页多票只评主票 · additional 由 items/Rule7 另测)。"""
    from services.ocr.entrypoints import run_pipeline_for_file
    from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict

    data = open(sample_path, "rb").read()
    pr = run_pipeline_for_file(data, os.path.basename(sample_path), api_key=api_key, max_pages=50)
    legacy = pipeline_result_to_legacy_dict(pr)
    pages = legacy.get("pages") or []
    return (pages[0].get("fields") or {}) if pages else {}


def _print_misses(name: str, result: dict):
    miss = [f for f, d in result["fields"].items() if not d["match"]]
    status = "✓" if not miss else "✗"
    print(
        f"{status} {name}: score={result['weighted_score']} money={result['money_exact']} "
        f"critical={result['critical_misses'] or '无'}"
    )
    for f in miss:
        d = result["fields"][f]
        print(f"     ⚠ {f}: 期望 {d['expected']!r} / 实得 {d['actual']!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", help="发票样本目录(隐私 · 不进 git)· 线上模式用")
    ap.add_argument("--extracted", help="离线模式:抽取结果 JSON {name: fields} · 免 API")
    args = ap.parse_args()

    if not args.samples and not args.extracted:
        print("需 --samples(线上跑 pipeline)或 --extracted(离线打分已有结果)其一。")
        return 2

    gts = _load_ground_truth()
    if not gts:
        print(
            "没有发票真值。请在 tests/eval/ground_truth_local/invoices/ 放 <名>.json(见 README)。"
        )
        return 1

    extracted_map = {}
    if args.extracted:
        extracted_map = json.load(open(args.extracted, encoding="utf-8"))
        print(f"离线模式 · 加载 {len(extracted_map)} 份抽取结果")
    api = os.environ.get("GEMINI_API_KEY", "")
    # 样本目录只 glob 一次(线上模式),避免对每条真值重复扫盘。
    sample_files = glob.glob(os.path.join(args.samples, "*")) if args.samples else []
    print(f"加载 {len(gts)} 份发票真值 · 模式={'离线' if args.extracted else '线上'}\n")

    report = {
        "ts": _dt.datetime.now().isoformat(),
        "mode": "offline" if args.extracted else "live",
        "invoices": [],
    }
    results = []
    for name, gt in gts.items():
        expected = _expected_fields(gt)
        if args.extracted:
            if name not in extracted_map:
                print(f"⊘ {name}: 抽取结果里无此名 · 跳过")
                continue
            actual = extracted_map[name]
        else:
            sample = _find_sample(sample_files, gt)
            if not sample:
                print(f"⊘ {name}: 样本文件未找到({gt.get('file')})· 跳过")
                continue
            try:
                actual = _extract_live(sample, api)
            except Exception as e:
                print(f"✗ {name}: pipeline 失败 · {type(e).__name__}: {e}")
                continue

        result = sc.score_invoice(expected, actual)
        results.append(result)
        report["invoices"].append({"name": name, **result})
        _print_misses(name, result)

    agg = sc.aggregate(results)
    print(
        f"\n=== 汇总 · 张数 {agg['n']} · 平均加权分 {agg['avg_weighted_score']} · "
        f"钱字段精确 {agg['money_exact']} · 关键漏判合计 {agg['critical_miss_total']} ==="
    )
    report["aggregate"] = agg

    os.makedirs(_RUNS_DIR, exist_ok=True)
    out = os.path.join(
        _RUNS_DIR, "invoice_" + _dt.datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
    )
    json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n报告已写入 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
