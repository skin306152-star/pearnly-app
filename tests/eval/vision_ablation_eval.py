"""Vision 消融 A/B 评测 harness(prod 跑·需 /opt/mrpilot OCR 栈 + Vertex 凭据)。
  A=现管线(Vision→3.1-lite文字→L3) · B=砍Vision图直喂3.1-lite多模态。
  用法: CORPUS=<语料目录> ./venv/bin/python vision_ablation_eval.py
  语料图片存 Desktop/单据/_vision_ablation_corpus/{v1,v2}(seed可复现·不进仓库)。
  发票用项目 invoice_scorer 全字段打分;对账三类用勾稽汇总打分。
  语料结构:<CORPUS>/{images,ground_truth}(发票) + <CORPUS>/{bank,gl,vat}/{images,ground_truth}
"""
import os, sys, json, glob, time, mimetypes
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FT

sys.path.insert(0, "/opt/mrpilot")
os.environ["OCR_ENGINE_MODE"] = "economy"

from services.ocr.entrypoints import run_pipeline_for_file
from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
from services.ocr import pipeline as pipe, cost as costmod
from services.ocr.engine_policy import engine_context
from services.ai_gateway.providers import vertex
from services.ocr.layer2_prompts import (
    _SYSTEM_PROMPT, _BANK_STATEMENT_SYSTEM_PROMPT, _GL_SYSTEM_PROMPT, _VAT_REPORT_SYSTEM_PROMPT,
)
sys.path.insert(0, "/opt/mrpilot/tests/eval")
from invoice_scorer import score_invoice  # 复用项目发票打分器

CORPUS = os.environ.get("CORPUS", "/tmp/vision_ablation")
_POOL = ThreadPoolExecutor(max_workers=3)
def timed(fn, *a, timeout=120, **k):
    f = _POOL.submit(fn, *a, **k)
    try: return f.result(timeout=timeout)
    except FT: return None

# gt doc_type → (pipeline document_type, B组 system prompt, 类别)
DOC_MAP = {
    "tax_invoice": ("invoice", _SYSTEM_PROMPT, "invoice"),
    "simplified_tax_invoice": ("invoice", _SYSTEM_PROMPT, "invoice"),
    "receipt": ("invoice", _SYSTEM_PROMPT, "invoice"),
    "purchase_order": ("invoice", _SYSTEM_PROMPT, "invoice"),
    "quotation": ("invoice", _SYSTEM_PROMPT, "invoice"),
    "delivery_note": ("invoice", _SYSTEM_PROMPT, "invoice"),
    "bank_statement": ("bank_statement", _BANK_STATEMENT_SYSTEM_PROMPT, "bank"),
    "general_ledger": ("general_ledger", _GL_SYSTEM_PROMPT, "gl"),
    "vat_report": ("vat_report", _VAT_REPORT_SYSTEM_PROMPT, "vat"),
}
IMG_PROMPT_HINT = "\n\n(This is a scanned/photographed document image — read it directly.)\n"

def _num(x):
    try: return float(str(x).replace(",", "").replace("−", "-"))
    except Exception: return None

def _money_close(a, b, tol=0.01):
    na, nb = _num(a), _num(b)
    if na is None or nb is None: return a in (None, "") and b in (None, "")
    return abs(na - nb) <= max(tol, abs(nb) * 0.001)

RECON_KEYS = {
    "bank": ["opening_balance", "closing_balance", "entry_count", "total_deposit", "total_withdrawal"],
    "gl": ["opening_balance", "closing_balance", "entry_count", "total_debit", "total_credit"],
    "vat": ["row_count", "total_pre_vat", "total_vat", "total_amount"],
}

def score_recon(cat, gt, actual):
    """对账勾稽汇总打分:逐字段 close 命中率 + 明细行数比。"""
    keys = RECON_KEYS[cat]
    hits, n, miss = 0, 0, []
    for k in keys:
        if k not in gt or gt.get(k) in (None, ""): continue
        n += 1
        av = actual.get(k)
        if k.endswith("count"):
            ok = str(gt[k]) == str(av)
        else:
            ok = _money_close(gt[k], av)
        hits += int(ok)
        if not ok: miss.append("%s(gt=%s/got=%s)" % (k, gt[k], av))
    return {"score": round(hits / n, 3) if n else None, "n": n, "miss": miss}

def modeA(raw, fn, pdt, cat):
    t0 = time.time()
    res = run_pipeline_for_file(raw, fn, api_key=None, max_pages=50, document_type=pdt)
    ms = int((time.time() - t0) * 1000)
    cost = float(getattr(res, "estimated_cost_thb", 0) or 0)
    leg = pipeline_result_to_legacy_dict(res)
    pages = getattr(res, "pages", []) or []
    chain = getattr(pages[0], "layer_chain", None) if pages else None
    l3 = bool(chain and any("L3" in str(x) or "3.5" in str(x) for x in chain))
    if cat == "invoice":
        actual = ((leg.get("pages") or [{}])[0] or {}).get("fields") or {}
    else:
        actual = _recon_agg(cat, _merge_docs(leg.get("pages") or []))
    return {"actual": actual, "cost": cost, "ms": ms, "l3": l3}

def modeB(raw, fn, prompt, cat):
    is_pdf = fn.lower().endswith(".pdf")
    if is_pdf:
        imgb, mime = raw, "application/pdf"
    else:
        imgb = pipe.downscale_image_bytes(raw, pipe.OCR_IMG_MAX_LONG_EDGE)
        mime = mimetypes.guess_type(fn)[0] or "image/jpeg"
    t0 = time.time()
    with engine_context("invoice"):  # economy → flash_lite=3.1-lite 覆写生效
        o = timed(vertex.multimodal_to_json, prompt + IMG_PROMPT_HINT, [(imgb, mime)],
                  tier="flash_lite", temperature=0.0, max_tokens=8192, timeout=120)
    ms = int((time.time() - t0) * 1000)
    if o is None or not o.ok or not isinstance(o.data, dict):
        return {"actual": {}, "cost": 0, "ms": ms, "err": (o.error_kind if o else "timeout")}
    in_usd, out_usd = costmod.price_per_m_usd("gemini-3.1-flash-lite")
    cost = ((o.input_tokens or 0)/1e6*in_usd + (o.output_tokens or 0)/1e6*out_usd)*35.5
    actual = _recon_agg(cat, o.data) if cat != "invoice" else _flatten_inv(o.data)
    return {"actual": actual, "cost": cost, "ms": ms}

def _flatten_inv(d):
    """B组发票 JSON → invoice_scorer 认的字段 dict(容错不同键名)。"""
    if not isinstance(d, dict): return {}
    if "items" in d and "total_amount" in d: return d
    inv = d.get("invoice") or d
    return inv if isinstance(inv, dict) else {}

def _sum(entries, key):
    tot, seen = Decimal(0), False
    for e in entries or []:
        v = (e or {}).get(key)
        if v in (None, ""): continue
        try: tot += Decimal(str(v).replace(",", "").replace("−", "-")); seen = True
        except Exception: pass
    return format(tot, "f") if seen else None

def _merge_docs(pages):
    """多页 → 单 recon doc(entries 拼接·opening 取首页·closing 取末个非空)。"""
    docs = [(p or {}).get("document") for p in pages
            if isinstance(p, dict) and isinstance(p.get("document"), dict)]
    if not docs: return {}
    base = dict(docs[0]); ents = []
    for d in docs: ents += (d.get("entries") or d.get("rows") or [])
    base["entries"] = ents
    for d in docs:
        if d.get("closing_balance") not in (None, ""): base["closing_balance"] = d["closing_balance"]
    return base

def _recon_agg(cat, doc):
    """结构化 doc(A组 page['document'] / B组 多模态 JSON)→ 勾稽汇总字段(GT 键名对齐)。"""
    if not isinstance(doc, dict): return {}
    ents = doc.get("entries") or doc.get("rows") or []
    out = {"entry_count": len(ents), "row_count": len(ents),
           "opening_balance": doc.get("opening_balance"), "closing_balance": doc.get("closing_balance")}
    if cat == "bank":
        out["total_deposit"] = _sum(ents, "deposit"); out["total_withdrawal"] = _sum(ents, "withdrawal")
    elif cat == "gl":
        out["total_debit"] = _sum(ents, "debit"); out["total_credit"] = _sum(ents, "credit")
    elif cat == "vat":
        out["total_pre_vat"] = doc.get("total_subtotal") or _sum(ents, "subtotal")
        out["total_vat"] = doc.get("total_vat") or _sum(ents, "vat")
        out["total_amount"] = doc.get("total_total") or _sum(ents, "total")
    return out

def load(cat, imgdir, gtdir):
    rows = []
    for gp in sorted(glob.glob(gtdir + "/*.json")):
        gt = json.load(open(gp, encoding="utf-8"))
        f = gt.get("file") or gt.get("name")
        base = os.path.basename(f) if f else os.path.splitext(os.path.basename(gp))[0]
        cand = glob.glob(imgdir + "/" + os.path.splitext(base)[0] + ".*")
        if not cand: continue
        rows.append((cand[0], gt, cat))
    return rows

def main():
    corpus = []
    corpus += load("invoice", CORPUS + "/images", CORPUS + "/ground_truth")
    for sub in ("bank", "gl", "vat"):
        corpus += load(sub, "%s/%s/images" % (CORPUS, sub), "%s/%s/ground_truth" % (CORPUS, sub))
    print("corpus: %d files" % len(corpus), flush=True)
    out = []
    for i, (path, gt, cat) in enumerate(corpus, 1):
        fn = os.path.basename(path); raw = open(path, "rb").read()
        if cat == "invoice":
            dt = gt.get("document_type") or "receipt"
        else:
            dt = {"bank": "bank_statement", "gl": "general_ledger", "vat": "vat_report"}[cat]
        pdt, bprompt, _c = DOC_MAP.get(dt, ("auto", _SYSTEM_PROMPT, cat))
        try: A = modeA(raw, fn, pdt, cat)
        except Exception as e: A = {"actual": {}, "cost": 0, "ms": 0, "l3": False, "err": str(e)[:40]}
        try: B = modeB(raw, fn, bprompt, cat)
        except Exception as e: B = {"actual": {}, "cost": 0, "ms": 0, "err": str(e)[:40]}
        if cat == "invoice":
            sA = score_invoice(gt, A["actual"]); sB = score_invoice(gt, B["actual"])
            scoreA = sA.get("weighted_score"); scoreB = sB.get("weighted_score")
            missA = sA.get("critical_misses"); missB = sB.get("critical_misses")
        else:
            gt_agg = {**gt, **_recon_agg(cat, gt)}  # GT 也派生汇总键(与抽取同算法)
            sA = score_recon(cat, gt_agg, A["actual"]); sB = score_recon(cat, gt_agg, B["actual"])
            scoreA, scoreB = sA["score"], sB["score"]; missA, missB = sA["miss"], sB["miss"]
        row = {"n": i, "file": fn[:24], "cat": cat, "dt": dt,
               "scenario": gt.get("scenario"), "traps": gt.get("traps"), "deg": gt.get("degradation"),
               "A_score": scoreA, "B_score": scoreB, "A_cost": round(A["cost"],4), "B_cost": round(B["cost"],4),
               "A_ms": A["ms"], "B_ms": B["ms"], "A_l3": A.get("l3"),
               "A_miss": missA, "B_miss": missB, "A_err": A.get("err"), "B_err": B.get("err")}
        out.append(row); print(json.dumps(row, ensure_ascii=False), flush=True)
    json.dump(out, open("/tmp/vision_ablation_results.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)

    # 分层汇总
    def agg(rows, label):
        va=[r["A_score"] for r in rows if r["A_score"] is not None]
        vb=[r["B_score"] for r in rows if r["B_score"] is not None]
        cA=sum(r["A_cost"] for r in rows); cB=sum(r["B_cost"] for r in rows)
        print("  %-28s n=%-3d A=%.3f B=%.3f | ฿A=%.2f ฿B=%.2f" % (
            label, len(rows), sum(va)/max(1,len(va)), sum(vb)/max(1,len(vb)), cA, cB), flush=True)
    print("\n===== 分层结果 A(Vision) vs B(砍Vision) =====", flush=True)
    for cat in ("invoice","bank","gl","vat"):
        rows=[r for r in out if r["cat"]==cat]
        if rows: agg(rows, "cat="+cat)
    # 按退化档
    print("--- 按退化档 ---", flush=True)
    degs=set()
    for r in out:
        for d in (r.get("deg") or ["sharp"]): degs.add(d)
    for d in sorted(degs):
        rows=[r for r in out if d in (r.get("deg") or ["sharp"])]
        if rows: agg(rows, "deg="+d)
    print("--- 按陷阱 ---", flush=True)
    traps=set()
    for r in out:
        for t in (r.get("traps") or []): traps.add(t)
    for t in sorted(traps):
        rows=[r for r in out if t in (r.get("traps") or [])]
        if rows: agg(rows, "trap="+t)
    _POOL.shutdown(wait=False)

main()
