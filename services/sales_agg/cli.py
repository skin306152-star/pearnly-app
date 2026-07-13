# -*- coding: utf-8 -*-
"""命令行:python -m services.sales_agg.cli <input.json> [out.json]

input.json = {"edc_settlement": [...], "bank_credit": [...], "sales_doc": [...]}
(三键均可省;行字段见 model.py 契约)。JSON 小数以 Decimal 解析,钱路零 float。
stdout 打印月合计与冲突/缺口点名摘要;给了 out.json 则落完整聚合报告。

退出码:0 = 无冲突无缺口;2 = 有 conflicts/gaps(结果照常产出,交人裁);1 = 用法/IO 错误。
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

from core.console import make_stdout_encoding_safe
from services.sales_agg.aggregate import aggregate_month

_PREVIEW = 20


def main(argv=None) -> int:
    make_stdout_encoding_safe()
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) not in (1, 2):
        print("用法: python -m services.sales_agg.cli <input.json> [out.json]")
        return 1
    in_path = Path(argv[0])
    if not in_path.is_file():
        print(f"输入文件不存在: {in_path}")
        return 1
    try:
        data = json.loads(in_path.read_text(encoding="utf-8"), parse_float=Decimal)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"输入不是合法 JSON: {exc}")
        return 1

    report = aggregate_month(
        data.get("edc_settlement") or [],
        data.get("bank_credit") or [],
        data.get("sales_doc") or [],
    )
    if len(argv) == 2:
        Path(argv[1]).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    total = report["month_total"]
    print(f"[SA-1] {in_path.name} · 天数 {len(report['daily'])}")
    print(f"  毛额合计   : {total['gross']}")
    print(f"  销售额     : {total['sales_amount']}")
    print(f"  销项税     : {total['output_vat']}(先加总再拆;逐笔口径差 {total['vat_method_diff']})")
    for name, ch in report["by_channel"].items():
        print(
            f"  {name:15s}: 收 {ch['count']} 计 {ch['included_count']} 重 {len(ch['duplicates'])}"
        )
    print(
        f"  关联 {len(report['links'])} · 冲突 {len(report['conflicts'])} · 缺口 {len(report['gaps'])}"
    )
    for c in report["conflicts"][:_PREVIEW]:
        print(f"    - [{c['kind']}] {','.join(c['refs'])} {c.get('detail', '')}")
    for g in report["gaps"][:_PREVIEW]:
        print(f"    - [{g['kind']}] {g['date']} {','.join(g['refs'])}")
    for note in report["notes"]:
        print(f"    * {note}")
    return 2 if (report["conflicts"] or report["gaps"]) else 0


if __name__ == "__main__":
    sys.exit(main())
