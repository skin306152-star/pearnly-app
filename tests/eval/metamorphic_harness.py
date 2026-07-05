# -*- coding: utf-8 -*-
"""变形测试 harness(造错机器 P4 · prod 跑·需 /opt/mrpilot OCR 栈 + Vertex 凭据)。

同一张票做「不该改变答案」的扰动,答案变了就是 bug —— 规则本身当裁判,零真值:
  · 旋转 ±2° / 平移 / JPEG 重压 / 调暗 → 总额、票号必须与基线读数一致
  · 逐档模糊 → 找第几档开始崩 = 崩溃阈值地图(指导「提示用户重拍」阈值)
  · 同图连打 3 遍 → 结果必须一致(确定性/温度漂移)

判定三态:ok(不变量保持)/ review(读数变了但诚实转人工·可接受)/
SILENT(读数变了还放行 = 真 bug,钱面归零指标)。

用法: SEEDS=<语料目录 images/> N_SEEDS=20 ./venv/bin/python tests/eval/metamorphic_harness.py
输出: /tmp/metamorphic_results.json + 崩溃阈值地图汇总。
"""

import glob
import io
import json
import os
import sys

sys.path.insert(0, "/opt/mrpilot")

from PIL import Image, ImageEnhance, ImageFilter

BLUR_LADDER = (0.8, 1.4, 2.0, 2.8)


def _jpeg(img: Image.Image, quality: int = 90) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def perturbations(raw: bytes) -> dict:
    """扰动族:名字 → 变换后的 jpeg bytes。全部确定性(无随机),同输入同输出。"""
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = img.size
    out = {
        "rot+2": _jpeg(img.rotate(2, expand=True, fillcolor="white")),
        "rot-2": _jpeg(img.rotate(-2, expand=True, fillcolor="white")),
        "shift": _jpeg(img.crop((12, 12, w, h))),
        "jpeg60": _jpeg(img, quality=60),
        "dim": _jpeg(ImageEnhance.Brightness(img).enhance(0.7)),
    }
    for r in BLUR_LADDER:
        out[f"blur{r}"] = _jpeg(img.filter(ImageFilter.GaussianBlur(r)))
    return out


def money_eq(a, b, tol: float = 0.01) -> bool:
    """两读数视为同一金额;都空也算一致(读不出是种稳定状态)。"""
    try:
        return abs(float(str(a).replace(",", "")) - float(str(b).replace(",", ""))) <= tol
    except (TypeError, ValueError):
        return (a in (None, "")) == (b in (None, ""))


def verdict(base: dict, got: dict, review: bool) -> str:
    """不变量:total_amount + invoice_number 相对基线读数不变。
    变了且 review=False → SILENT(真 bug);变了但转人工 → review(诚实)。"""
    same_total = money_eq(base.get("total_amount"), got.get("total_amount"))
    same_no = str(base.get("invoice_number") or "") == str(got.get("invoice_number") or "")
    if same_total and same_no:
        return "ok"
    return "review" if review else "SILENT"


def _read(raw: bytes, fn: str) -> tuple:
    from services.ocr.entrypoints import run_pipeline_for_file
    from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict

    res = run_pipeline_for_file(raw, fn, api_key=None, max_pages=5, document_type="invoice")
    leg = pipeline_result_to_legacy_dict(res)
    fields = ((leg.get("pages") or [{}])[0] or {}).get("fields") or {}
    review = any(getattr(p, "needs_manual_review", False) for p in res.pages or [])
    return fields, review


def main() -> None:
    seeds_dir = os.environ.get("SEEDS", "/tmp/inv_fire/v1/images")
    n_seeds = int(os.environ.get("N_SEEDS", "20"))
    seeds = sorted(glob.glob(os.path.join(seeds_dir, "*.jpg")))[:n_seeds]
    rows, crash_map = [], {}

    for path in seeds:
        name = os.path.basename(path).rsplit(".", 1)[0]
        raw = open(path, "rb").read()
        base, base_review = _read(raw, name + ".jpg")
        if not base.get("total_amount"):
            rows.append({"seed": name, "perturb": "baseline", "verdict": "skip_no_total"})
            continue

        # 确定性:同图再打 2 遍
        for i in (2, 3):
            got, review = _read(raw, name + ".jpg")
            rows.append(
                {"seed": name, "perturb": f"repeat{i}", "verdict": verdict(base, got, review)}
            )

        crash_at = None
        for pname, praw in perturbations(raw).items():
            got, review = _read(praw, f"{name}_{pname}.jpg")
            v = verdict(base, got, review)
            rows.append(
                {
                    "seed": name,
                    "perturb": pname,
                    "verdict": v,
                    "base_total": base.get("total_amount"),
                    "got_total": got.get("total_amount"),
                }
            )
            if pname.startswith("blur") and v != "ok" and crash_at is None:
                crash_at = pname
        crash_map[name] = crash_at or "survived_all"
        print(f"{name}: crash_at={crash_map[name]}", flush=True)

    silent = [r for r in rows if r["verdict"] == "SILENT"]
    summary = {
        "seeds": len(seeds),
        "runs": len(rows),
        "silent": len(silent),
        "silent_rows": silent,
        "review": sum(1 for r in rows if r["verdict"] == "review"),
        "crash_map": crash_map,
    }
    json.dump(
        {"rows": rows, "summary": summary},
        open("/tmp/metamorphic_results.json", "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=1,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
