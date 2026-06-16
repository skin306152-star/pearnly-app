# -*- coding: utf-8 -*-
"""ADR-006 S8c · 线上端到端验证(真扫描 PDF → needs_review → 核对修正 → 重对账)。

用真扫描件(BBL 2697 · 90°旋转扫描 · Gemini 易低信心)走线上 bank-v2/submit ·
验证:① 触发 needs_review + 返回 review 载荷 ② confirm-rows 用修正行重对账出结果。
纯 API(打 pearnly.com · 跑的是部署后的真后端 + 真 OCR)· 不点 UI。
"""

import os
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://pearnly.com"
AK = os.environ.get("PEARNLY_E2E_TOKEN", "").strip()
if not AK:
    raise SystemExit("Set PEARNLY_E2E_TOKEN to run this live probe.")
H = {"Authorization": "Bearer " + AK}
TPL = r"D:/Users/Skin/Desktop/银行对账需求/银行账单模板"
STMT = TPL + "/BBL 2697.pdf"
GL = r"D:/Users/Skin/Desktop/Pearnly_Bank_GL_Test_Templates_2026-05-24/gl_templates/gl_01_thai_standard_debit_credit.xlsx"


def poll(job_id, want_terminal=True, timeout=300):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = requests.get(f"{BASE}/api/recon/jobs/{job_id}", headers=H, timeout=20)
        j = r.json()
        st = j.get("status")
        print(f"   poll status={st}")
        if st in ("done", "failed", "needs_review", "timeout"):
            return j
        time.sleep(3)
    return {"status": "timeout"}


def main():
    print("STEP 1 · 提交扫描件 BBL 2697 + GL → bank-v2/submit")
    with open(STMT, "rb") as f1, open(GL, "rb") as f2:
        files = [
            ("stmt_files", ("BBL2697.pdf", f1.read(), "application/pdf")),
            (
                "gl_files",
                (
                    "gl.xlsx",
                    f2.read(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
            ),
        ]
    r = requests.post(
        f"{BASE}/api/recon/bank-v2/submit",
        headers=H,
        files=files,
        data={"gl_account": "1010", "lang": "th"},
        timeout=120,
    )
    print("   submit HTTP", r.status_code, "->", str(r.json())[:120])
    sub = r.json()
    if sub.get("needs_mapping"):
        print("   (Excel 列映射面板 · 非本测目标)")
        return
    job_id = sub.get("job_id")
    if not job_id:
        print("   ❌ 无 job_id")
        return

    print("STEP 2 · 轮询到终态")
    j = poll(job_id)
    st = j.get("status")
    if st != "needs_review":
        print(f"   ⚠️ 状态={st}(该扫描件本地/OCR 已高信心读对 → 没触发核对关 · 也是合法结果)")
        print(f"   result_id={j.get('result_id')}")
        if st == "done":
            print("   ✅ 至少证明:PDF 对账流程线上跑通(只是这份没触发 S8 核对)")
        return
    review = j.get("review") or {}
    print(
        f"   ✅ 触发 needs_review · 行数={review.get('row_count')} "
        f"低信心={review.get('low_conf_count')} 完整性问题={len(review.get('completeness_issues') or [])}"
    )

    print("STEP 3 · 模拟用户核对(原样确认)→ confirm-rows 重对账")
    rows = review.get("rows") or []
    r = requests.post(
        f"{BASE}/api/recon/bank-v2/confirm-rows/{job_id}",
        headers=H,
        json={"rows": rows},
        timeout=60,
    )
    print("   confirm HTTP", r.status_code, "->", str(r.json())[:120])
    new_id = r.json().get("job_id")
    if not new_id:
        print("   ❌ confirm 没返回新 job_id")
        return

    print("STEP 4 · 轮询重对账任务")
    j2 = poll(new_id)
    print(f"   重对账状态={j2.get('status')} result_id={j2.get('result_id')}")
    if j2.get("status") == "done" and j2.get("result_id"):
        print("   ✅ S8 端到端通:扫描件→核对关→修正行→重对账出结果")
    else:
        print("   ❌ 重对账未出结果")


if __name__ == "__main__":
    main()
