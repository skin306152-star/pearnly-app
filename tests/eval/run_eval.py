# -*- coding: utf-8 -*-
"""
v118.35.0.65 · 银行对账 OCR 评测集运行器(让每次改进都可量化 · 不再靠嘴说『提升了』)

用法:
    # 1) 准备样本(隐私 · 不进 git):把真实账单放到 _bank_samples/ 或用 --samples 指定目录
    # 2) 准备标准答案(隐私 · 不进 git):tests/eval/ground_truth_local/<名>.json
    #    格式见 tests/eval/ground_truth/example_synthetic.json + README.md
    # 3) 跑:
    python tests/eval/run_eval.py --samples "D:/Users/Skin/Desktop/账单"
    # 需要 Gemini key 时:set GEMINI_API_KEY=...(扫描件 PDF 才需要;xlsx 直读免费)

输出:
    - 每个文件:笔数召回/多读、期末是否吻合、(给了 expected_rows 时)逐行召回率
    - 汇总:整体行召回率 · 完整性检查命中情况
    - 写一份 JSON 到 tests/eval/_runs/<时间戳>.json(不进 git · 供回归对比)

设计原则:
    - 标准答案(真实金额)= 用户隐私 → ground_truth_local/(gitignored)
    - 本运行器 + 合成示例 + README = 进 git(无隐私)
    - 比对用 (date, 金额) 宽松匹配 · 容差 0.05 · 不强求描述逐字一致
"""
import argparse
import datetime as _dt
import glob
import json
import os
import sys

try:                       # Windows 控制台默认 GBK · 强制 UTF-8 防中文/符号崩
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from bank_recon_v2 import parse_bank_statement_pdf  # noqa: E402

_HERE = os.path.dirname(__file__)
_GT_DIRS = [os.path.join(_HERE, "ground_truth_local"),  # 真实(gitignored · 优先)
            os.path.join(_HERE, "ground_truth")]        # 合成示例(git)
_RUNS_DIR = os.path.join(_HERE, "_runs")
_TOL = 0.05


def _load_ground_truth():
    """读所有标准答案 · 同名以 _local 优先。返回 {name: gt_dict}。"""
    gts = {}
    for d in reversed(_GT_DIRS):   # 先读 git 示例 · 再用 local 覆盖
        for f in sorted(glob.glob(os.path.join(d, "*.json"))):
            try:
                gt = json.load(open(f, encoding="utf-8"))
                gts[gt.get("name") or os.path.basename(f)] = gt
            except Exception as e:
                print(f"  [skip] {f}: {e}")
    return gts


def _find_sample(samples_dir, gt):
    """按 gt['file'](文件名或子串)在样本目录里找真实文件。"""
    target = gt.get("file") or gt.get("name") or ""
    if not target:
        return None
    cand = os.path.join(samples_dir, target)
    if os.path.exists(cand):
        return cand
    for f in glob.glob(os.path.join(samples_dir, "*")):
        if target.lower() in os.path.basename(f).lower():
            return f
    return None


def _row_recall(extracted_rows, expected_rows):
    """逐行召回:expected 里每笔(date+金额)能否在 extracted 找到。返回 (命中, 总数, 漏的列表)。"""
    def key(r):
        amt = round(float(r.get("deposit") or 0) - float(r.get("withdrawal") or 0), 2) \
            if isinstance(r, dict) else round((r.deposit or 0) - (r.withdrawal or 0), 2)
        d = r.get("date") if isinstance(r, dict) else (r.date.isoformat() if r.date else None)
        return (str(d), amt)
    pool = {}
    for r in extracted_rows:
        pool.setdefault(key(r), 0)
        pool[key(r)] += 1
    hit, missed = 0, []
    for er in expected_rows:
        k = key(er)
        matched = False
        for pk in list(pool):
            if pk[0] == k[0] and abs(pk[1] - k[1]) <= _TOL and pool[pk] > 0:
                pool[pk] -= 1
                matched = True
                break
        if matched:
            hit += 1
        else:
            missed.append(k)
    return hit, len(expected_rows), missed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", required=True, help="真实账单目录(隐私 · 不进 git)")
    args = ap.parse_args()
    api = os.environ.get("GEMINI_API_KEY", "")

    gts = _load_ground_truth()
    if not gts:
        print("没有标准答案。请在 tests/eval/ground_truth_local/ 放 <名>.json(见 README)。")
        return 1
    print(f"加载 {len(gts)} 份标准答案 · api_key={'有' if api else '无(扫描件PDF会失败)'}\n")

    report = {"ts": _dt.datetime.now().isoformat(), "files": []}
    agg_hit = agg_total = 0
    for name, gt in gts.items():
        sample = _find_sample(args.samples, gt)
        if not sample:
            print(f"⊘ {name}: 样本文件未找到({gt.get('file')})· 跳过")
            continue
        res = parse_bank_statement_pdf(open(sample, "rb").read(), os.path.basename(sample), api)
        rows = res.get("rows") or []
        n_dep = sum(1 for r in rows if (r.deposit or 0) > 0)
        n_wd = sum(1 for r in rows if (r.withdrawal or 0) > 0)
        line = {"name": name, "extracted_rows": len(rows),
                "credit_count": n_dep, "debit_count": n_wd,
                "closing": res.get("closing")}
        flags = []
        if "credit_count" in gt and gt["credit_count"] != n_dep:
            flags.append(f"存款笔数 期望{gt['credit_count']}/实得{n_dep}")
        if "debit_count" in gt and gt["debit_count"] != n_wd:
            flags.append(f"取款笔数 期望{gt['debit_count']}/实得{n_wd}")
        if "closing" in gt and abs(float(gt["closing"]) - float(res.get("closing") or 0)) > 1.0:
            flags.append(f"期末 期望{gt['closing']}/实得{res.get('closing')}")
        if gt.get("expected_rows"):
            hit, total, missed = _row_recall(rows, gt["expected_rows"])
            line["row_recall"] = f"{hit}/{total}"
            line["missed"] = missed[:10]
            agg_hit += hit
            agg_total += total
            if hit < total:
                flags.append(f"逐行召回 {hit}/{total}")
        line["flags"] = flags
        report["files"].append(line)
        status = "✓" if not flags else "✗"
        print(f"{status} {name}: rows={len(rows)} dep={n_dep} wd={n_wd} closing={res.get('closing')}")
        for fl in flags:
            print(f"     ⚠ {fl}")

    if agg_total:
        print(f"\n=== 汇总 · 逐行召回率 {agg_hit}/{agg_total} = {agg_hit/agg_total*100:.1f}% ===")
    report["aggregate_row_recall"] = (f"{agg_hit}/{agg_total}" if agg_total else None)

    os.makedirs(_RUNS_DIR, exist_ok=True)
    out = os.path.join(_RUNS_DIR, _dt.datetime.now().strftime("%Y%m%d_%H%M%S") + ".json")
    json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n报告已写入 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
