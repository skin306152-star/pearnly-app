# -*- coding: utf-8 -*-
"""P1 造错机器第一轮实弹:陷阱语料从真门(prod /api/ocr/recognize)过全管线并打分。

一次性 live-fire 工具(下划线前缀,不进 CI):
  - 语料 = vision_ablation v1(91 发票)+ v2(90 发票·Augraphy 拍照级),图在桌面语料库;
  - 真门 = 登录 pearnly_e2e_1 → Bearer → multipart 上传,与真实用户完全同路;
  - 裁判 = tests/eval/invoice_scorer.score_invoice(与消融同一把尺);
  - 附 3 个入口怪文件探针(0字节/扩展名骗人/纯白图):考"死得体面",非 500 即过;
  - 产出 = scratchpad JSONL 逐张 + 终端汇总,失败样本进桌面台账由人工归因。

凭据只从桌面 pearnly_test_accounts.txt 读,不打印不落盘。识别走 staged 草稿不进正式列表。
"""

from __future__ import annotations

import argparse
import io
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

from invoice_scorer import score_invoice  # noqa: E402

BASE = os.environ.get("P1_BASE", "https://pearnly.com")
ACCOUNTS_TXT = Path(r"C:/Users/skin3/Desktop/pearnly_test_accounts.txt")
E2E_USER = "pearnly_e2e_1"


def _read_password() -> str:
    for line in ACCOUNTS_TXT.read_text(encoding="utf-8-sig").splitlines():
        if E2E_USER in line:
            m = re.search(r"password:\s*(\S+)", line)
            if m:
                return m.group(1)
    raise SystemExit(f"password for {E2E_USER} not found in accounts txt")


def _login(sess: requests.Session) -> None:
    r = sess.post(
        f"{BASE}/api/login",
        json={"username": E2E_USER, "password": _read_password()},
        timeout=30,
    )
    r.raise_for_status()
    sess.headers["Authorization"] = f"Bearer {r.json()['token']}"


def _load_items():
    items = []
    v1 = ROOT / "tests" / "eval" / "vision_ablation"
    for line in (v1 / "manifest.jsonl").read_text(encoding="utf-8").splitlines():
        m = json.loads(line)
        items.append(
            {
                "id": m["id"],
                "corpus": "v1",
                "img": v1 / m["file"],  # 仓库内=重新生成后的最新图(税号已过 mod-11)
                "gt": json.loads((v1 / m["gt"]).read_text(encoding="utf-8")),
                "scenario": m.get("scenario", ""),
            }
        )
    v2 = ROOT / "tests" / "eval" / "vision_ablation_v2"
    for line in (v2 / "manifest.jsonl").read_text(encoding="utf-8").splitlines():
        m = json.loads(line)
        if m.get("type") != "invoice":
            continue
        items.append(
            {
                "id": m["id"],
                "corpus": "v2",
                "img": v2 / m["image"],
                "gt": json.loads((v2 / m["ground_truth"]).read_text(encoding="utf-8")),
                "scenario": m.get("trap", ""),
            }
        )
    return items


def _recognize(sess: requests.Session, filename: str, data: bytes):
    for attempt in (1, 2):
        try:
            r = sess.post(
                f"{BASE}/api/ocr/recognize",
                files={"file": (filename, data, "application/octet-stream")},
                timeout=180,
            )
            if r.status_code >= 500 and attempt == 1:
                time.sleep(3)
                continue
            return r
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(3)


def _expect_decoy(item) -> bool:
    gt = item["gt"]
    return bool(gt.get("is_not_invoice")) or "non_invoice" in item["id"] or "decoy" in item["id"]


def _fire_one(sess, item):
    data = item["img"].read_bytes()
    t0 = time.time()
    r = _recognize(sess, item["img"].name, data)
    ms = int((time.time() - t0) * 1000)
    row = {
        "id": item["id"],
        "corpus": item["corpus"],
        "scenario": item["scenario"],
        "status": r.status_code,
        "ms": ms,
    }
    if r.status_code == 400 and "not_invoice" in r.text:
        row["outcome"] = "pass_decoy" if _expect_decoy(item) else "fail_false_reject"
        return row
    if _expect_decoy(item):
        row["outcome"] = "fail_decoy_accepted" if r.status_code == 200 else "pass_decoy"
        return row
    if r.status_code != 200:
        row["outcome"] = "fail_http"
        row["body"] = r.text[:300]
        return row
    body = r.json()
    invs = body.get("invoices") or []
    fields = (invs[0].get("fields") if invs else None) or (
        (body.get("pages") or [{}])[0].get("fields") or {}
    )
    s = score_invoice(item["gt"], fields)
    row["score"] = s.get("weighted_score") or 0.0
    row["money_exact"] = s.get("money_exact")
    row["critical_misses"] = s.get("critical_misses")
    row["fields"] = {
        k: {"expected": v["expected"], "actual": v["actual"]}
        for k, v in (s.get("fields") or {}).items()
        if not v.get("match")
    }
    row["invoice_count"] = body.get("invoice_count")
    row["outcome"] = "scored"
    return row


def _img(color="white", size=(800, 1000), fmt="PNG") -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format=fmt)
    return buf.getvalue()


def _noise_jpg(size=(900, 1200)) -> bytes:
    import random

    from PIL import Image

    rnd = random.Random(20260706)
    img = Image.new("RGB", size)
    img.putdata([(rnd.randrange(256),) * 3 for _ in range(size[0] * size[1])])
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


def _probes() -> list:
    """入口怪文件层(P3):每个真实用户可能真传的怪东西。考「死得体面」=
    非 500 + 结构化人话码 + 零扣费,不考读得准。全部运行时生成,零外部依赖。"""
    jpg = _img(fmt="JPEG")
    return [
        ("empty.jpg", b""),
        ("fake_ext.pdf", b"\xff\xd8\xff\xe0" + b"\x00" * 400),  # jpg 头字节但扩展名 .pdf
        ("fake_ext2.jpg", b"%PDF-1.4\n" + b"0" * 400),  # pdf 头字节但扩展名 .jpg
        ("blank.png", _img()),
        ("black.jpg", _img("black", fmt="JPEG")),
        ("tiny.jpg", _img(size=(8, 8), fmt="JPEG")),
        ("panorama.jpg", _img(size=(400, 8000), fmt="JPEG")),  # 竖幅全景长图
        ("noise_photo.jpg", _noise_jpg()),  # 口袋里误拍的噪点图
        ("corrupt.pdf", b"%PDF-1.4\n1 0 obj\n<<garbage" + os.urandom(600)),
        ("truncated.jpg", jpg[: len(jpg) // 3]),  # 上传断流截半
        ("no_ext", jpg),  # 无扩展名
        ("weird_name_ใบเสร็จ #1 (copy).jpg", jpg),
        ("script.exe.jpg", jpg),  # 双扩展名
        ("garbage.csv", "\x00\x01\x02,,,\nnot,a,table".encode()),  # 表格直读门
        ("bom_utf16.csv", "﻿a,b,c\n1,2,3".encode("utf-16")),
    ]


def _credits(sess) -> float:
    try:
        r = sess.get(f"{BASE}/api/me/credits", timeout=15)
        d = r.json()
        return float(d.get("balance_thb") or d.get("balance") or 0)
    except Exception:  # noqa: BLE001
        return -1.0


def _fire_probes(sess, out):
    bal0 = _credits(sess)
    n_fail = n_accepted = 0
    for name, payload in _probes():
        try:
            r = _recognize(sess, name, payload)
            graceful = r.status_code < 500
            n_accepted += r.status_code == 200
            row = {
                "id": f"probe:{name}",
                "status": r.status_code,
                "outcome": "pass_graceful" if graceful else "fail_500",
                "body": r.text[:200],
            }
        except Exception as e:  # noqa: BLE001
            row = {"id": f"probe:{name}", "outcome": "fail_raise", "body": str(e)[:200]}
        n_fail += row["outcome"] != "pass_graceful"
        out.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(row["id"], row["outcome"], row.get("status"))
    bal1 = _credits(sess)
    # 成功处理(200)扣费合法;全被拒收却掉余额 = 拒收还扣费,违规
    charged_on_reject = bal0 >= 0 and bal1 < bal0 and n_accepted == 0
    print(
        f"probes: {n_fail} 不体面 · {n_accepted} 张被正常收案 · 余额 {bal0} → {bal1} · "
        + ("❌ 拒收还扣费" if charged_on_reject else "扣费面 ✓")
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--probes-only", action="store_true", help="只打入口怪文件层,不跑语料")
    ap.add_argument("--out", default=os.environ.get("P1_OUT", "p1_results.jsonl"))
    args = ap.parse_args()

    sess = requests.Session()
    _login(sess)
    items = [] if args.probes_only else _load_items()
    if args.limit:
        items = items[: args.limit]
    print(f"corpus items: {len(items)} → {BASE}")

    stats = {"scored": 0, "pass_decoy": 0}
    fails = []
    score_sum = 0.0
    with open(args.out, "w", encoding="utf-8") as out:
        _fire_probes(sess, out)
        for i, item in enumerate(items, 1):
            try:
                row = _fire_one(sess, item)
            except Exception as e:  # noqa: BLE001
                row = {"id": item["id"], "outcome": "fail_raise", "body": str(e)[:200]}
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            oc = row["outcome"]
            stats[oc] = stats.get(oc, 0) + 1
            if oc == "scored":
                score_sum += row["score"]
                if row["fields"]:
                    fails.append(row)
            elif oc.startswith("fail"):
                fails.append(row)
            if i % 10 == 0:
                done = stats.get("scored", 0)
                avg = score_sum / done if done else 0
                print(f"[{i}/{len(items)}] avg_score={avg:.3f} outcomes={stats}")
            time.sleep(0.4)

    done = stats.get("scored", 0)
    print("\n===== P1 汇总 =====")
    print("outcomes:", stats)
    if done:
        print(f"avg score: {score_sum / done:.4f} over {done} scored")
    print(f"带失配字段/失败样本: {len(fails)}(详见 {args.out})")


if __name__ == "__main__":
    main()
