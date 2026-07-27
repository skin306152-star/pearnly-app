#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""管家文案 E2E 定值的取数脚本 → tests/e2e/_fixtures_steward_copy.json。

E2E 里那些错误句、卡面标题、参数行必须是真 copy 层现产的,不是在 spec 里手抄一份 ——
手抄的那份与产品一起漂,验的就成了「我编的字长这样」(见 verify-target-must-be-real-content)。

用法:PYTHONUTF8=1 python scripts/_steward_copy_fixtures.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.steward import copy, registry  # noqa: E402  (先补 sys.path 才 import 得到)

OUT = ROOT / "tests" / "e2e" / "_fixtures_steward_copy.json"

_PUSH_ARGS = {
    "invoice_no": "INV-2569-0042",
    "seller_name": "Sister Trading",
    "direction": "sales",
    "posting_kind": "stock",
    "total_amount": "128400.00",
    "history_id": "6f1c-uuid",
}


def build() -> dict:
    out = {}
    for lang in ("zh", "th"):
        out[lang] = {
            "bridge_offline": copy.error("steward.bridge_offline", {"account_set": "69EXP"}, lang),
            "already_pushed": copy.error(
                "steward.erp_already_pushed",
                {
                    "invoice_no": "RR581231-002",
                    "pushed_at": "2026-07-26 11:20",
                    "account_set": "69EXP",
                },
                lang,
            ),
            "card_title": copy.authz_title(
                registry.ERP_PUSH, {"doc_count": 3, "account_set": "69EXP"}, lang
            ),
            "arg_rows": copy.authz_arg_rows(registry.ERP_PUSH, _PUSH_ARGS, lang),
        }
    return out


if __name__ == "__main__":
    # CRLF + 末尾换行:仓库里的 json 走 prettier 的口径,重跑一次脚本不该产生整文件 diff。
    with io.open(OUT, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write(json.dumps(build(), ensure_ascii=False, indent=2) + "\n")
    print(f"✅ {OUT}")
