# -*- coding: utf-8 -*-
"""P3 定向补料实弹:重折痕 decoy / 找零加倍 / 身份证 从真门过全管线并打分。

一次性 live-fire(下划线前缀,不进 CI)。三批语料走两个真门:
  - 发票类(pretx decoy 20 + cash_change 60)→ /api/ocr/recognize → invoice_scorer
  - 身份证(40)→ /api/dms/id-card/recognize → id_card_scorer

凭据只从桌面 pearnly_test_accounts.txt 读,不打印不落盘。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "eval"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from id_card_scorer import score_id_card  # noqa: E402
from invoice_scorer import score_invoice  # noqa: E402

BASE = os.environ.get("P3_BASE", "https://pearnly.com")
ACCOUNTS_TXT = Path(r"C:/Users/skin3/Desktop/pearnly_test_accounts.txt")
E2E_USER = "pearnly_e2e_1"
P3 = ROOT / "tests" / "eval" / "vision_ablation_p3"


def _read_password() -> str:
    for line in ACCOUNTS_TXT.read_text(encoding="utf-8-sig").splitlines():
        if E2E_USER in line:
            m = re.search(r"password:\s*(\S+)", line)
            if m:
                return m.group(1)
    raise SystemExit(f"password for {E2E_USER} not found")


def _login(sess: requests.Session) -> None:
    r = sess.post(
        f"{BASE}/api/login",
        json={"username": E2E_USER, "password": _read_password()},
        timeout=30,
    )
    r.raise_for_status()
    sess.headers["Authorization"] = f"Bearer {r.json()['token']}"


def _post(sess, url, filename, data, timeout=180):
    for attempt in (1, 2):
        try:
            r = sess.post(
                url,
                files={"file": (filename, data, "application/octet-stream")},
                timeout=timeout,
            )
            if r.status_code >= 500 and attempt == 1:
                time.sleep(3)
                continue
            return r
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(3)


def _load_invoices():
    items = []
    for line in (P3 / "manifest.jsonl").read_text(encoding="utf-8").splitlines():
        m = json.loads(line)
        if m.get("scenario", "").startswith("id_card"):
            continue
        items.append(
            {
                "id": m["id"],
                "scenario": m["scenario"],
                "img": P3 / m["file"],
                "gt": json.loads((P3 / m["gt"]).read_text(encoding="utf-8")),
            }
        )
    return items


def _load_id_cards():
    items = []
    for line in (P3 / "manifest.jsonl").read_text(encoding="utf-8").splitlines():
        m = json.loads(line)
        if not m.get("scenario", "").startswith("id_card"):
            continue
        items.append(
            {
                "id": m["id"],
                "scenario": m["scenario"],
                "img": P3 / m["file"],
                "gt": json.loads((P3 / m["gt"]).read_text(encoding="utf-8")),
            }
        )
    return items


def _expect_decoy(gt) -> bool:
    return bool(gt.get("is_not_invoice"))


def _fire_invoice(sess, item):
    r = _post(sess, f"{BASE}/api/ocr/recognize", item["img"].name, item["img"].read_bytes())
    row = {"id": item["id"], "scenario": item["scenario"], "status": r.status_code}
    is_decoy = _expect_decoy(item["gt"])
    if r.status_code == 400 and "not_invoice" in r.text:
        row["outcome"] = "pass_decoy" if is_decoy else "fail_false_reject"
        return row
    if is_decoy:
        # decoy 应被拒;被 200 收案 = 漏网(任务1 的核心失败模式)
        row["outcome"] = "fail_decoy_accepted" if r.status_code == 200 else "pass_decoy"
        return row
    if r.status_code != 200:
        row["outcome"] = "fail_http"
        row["body"] = r.text[:200]
        return row
    body = r.json()
    invs = body.get("invoices") or []
    fields = (invs[0].get("fields") if invs else None) or (
        (body.get("pages") or [{}])[0].get("fields") or {}
    )
    s = score_invoice(item["gt"], fields)
    row["outcome"] = "scored"
    row["score"] = s.get("weighted_score") or 0.0
    row["money_exact"] = s.get("money_exact")
    row["critical_misses"] = s.get("critical_misses")
    row["total_gt"] = item["gt"].get("total_amount")
    row["total_read"] = fields.get("total_amount")
    return row


def _fire_id_card(sess, item):
    r = _post(sess, f"{BASE}/api/dms/id-card/recognize", item["img"].name, item["img"].read_bytes())
    row = {"id": item["id"], "scenario": item["scenario"], "status": r.status_code}
    if r.status_code != 200:
        # 400 dms.no_endpoint = e2e 账号没挂 DMS 端点(前置条件没满足)
        row["outcome"] = "fail_http"
        row["body"] = r.text[:200]
        return row
    body = r.json()
    ic = body.get("id_card") or {}
    s = score_id_card(item["gt"], ic)
    row["outcome"] = "scored"
    row["score"] = s.get("weighted_score") or 0.0
    row["id_valid_gt"] = s.get("id_valid")
    row["critical_misses"] = s.get("critical_misses")
    row["pid_gt"] = item["gt"].get("people_id")
    row["pid_read"] = ic.get("people_id")
    row["name_gt"] = f"{item['gt'].get('first_name', '')} {item['gt'].get('last_name', '')}".strip()
    row["name_read"] = f"{ic.get('first_name', '')} {ic.get('last_name', '')}".strip()
    row["needs_review"] = body.get("needs_review")
    return row


def _summ(rows, label):
    scored = [r for r in rows if r.get("outcome") == "scored"]
    avg = sum(r["score"] for r in scored) / len(scored) if scored else 0
    oc = {}
    for r in rows:
        oc[r["outcome"]] = oc.get(r["outcome"], 0) + 1
    print(f"\n== {label} == n={len(rows)} scored_avg={avg:.4f} outcomes={oc}")
    return {"label": label, "n": len(rows), "avg": round(avg, 4), "outcomes": oc}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["invoice", "id_card"], default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=os.environ.get("P3_OUT", "p3_results.jsonl"))
    args = ap.parse_args()

    sess = requests.Session()
    _login(sess)

    invoices = [] if args.only == "id_card" else _load_invoices()
    id_cards = [] if args.only == "invoice" else _load_id_cards()
    if args.limit:
        invoices, id_cards = invoices[: args.limit], id_cards[: args.limit]
    print(f"invoices={len(invoices)} id_cards={len(id_cards)} → {BASE}")

    with open(args.out, "w", encoding="utf-8") as out:
        inv_rows, idc_rows = [], []
        for i, item in enumerate(invoices, 1):
            try:
                row = _fire_invoice(sess, item)
            except Exception as e:  # noqa: BLE001
                row = {"id": item["id"], "outcome": "fail_raise", "body": str(e)[:200]}
            inv_rows.append(row)
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            if i % 10 == 0:
                print(f"[inv {i}/{len(invoices)}]")
            time.sleep(0.4)
        for i, item in enumerate(id_cards, 1):
            try:
                row = _fire_id_card(sess, item)
            except Exception as e:  # noqa: BLE001
                row = {"id": item["id"], "outcome": "fail_raise", "body": str(e)[:200]}
            idc_rows.append(row)
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            if i % 10 == 0:
                print(f"[idc {i}/{len(id_cards)}]")
            time.sleep(0.4)

    print("\n===== P3 汇总 =====")
    if inv_rows:
        _summ([r for r in inv_rows if "decoy" in r.get("scenario", "")], "task1 重折痕decoy")
        _summ([r for r in inv_rows if r.get("scenario") == "cash_change_trap"], "task2 找零")
    if idc_rows:
        _summ(idc_rows, "task3 身份证(数字半·名字blocked)")


if __name__ == "__main__":
    main()
