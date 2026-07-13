# -*- coding: utf-8 -*-
"""命令行:python -m services.payroll.cli <in.xlsx> <outdir>

吃任意工资 Excel → 自动猜列 → 五校验 → 写三产出(ใบแนบ 扁平 pipe / 键入底稿 xlsx /
官方 FORMAT กลาง txt)到 <outdir>,stdout 打印猜列结果 + Σ + 逐行 issue 点名。
退出码:0 = 全过;2 = 有校验 issue;1 = 用法/IO 错误。
"""

from __future__ import annotations

import sys
from pathlib import Path

from core.console import make_stdout_encoding_safe
from services.payroll import guess, intake, keying_sheet, validate
from services.tax import pnd1_attach, rdprep_pnd1


def main(argv=None) -> int:
    make_stdout_encoding_safe()
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("用法: python -m services.payroll.cli <in.xlsx> <outdir>")
        return 1

    in_path, out_dir = Path(argv[0]), Path(argv[1])
    if not in_path.is_file():
        print(f"输入文件不存在: {in_path}")
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)

    header, raw_rows = intake.read_workbook(in_path.read_bytes())
    candidates = guess.guess_columns(header, raw_rows)
    column_map = {field_key: cand.column for field_key, cand in candidates.items()}
    payer_col = guess.find_constant_id_column(header, raw_rows)
    all_rows = intake.build_rows(header, raw_rows, column_map)
    rows, declared_total = intake.partition_rows(all_rows)

    period = _infer_period(rows)
    issues = validate.validate_rows(rows, period=period, declared_total=declared_total)
    total = validate.total_paid(rows)

    _print_summary(in_path, candidates, payer_col, rows, period, total, issues)
    _write_outputs(out_dir, rows, payer_col, raw_rows, period)
    return 0 if not issues else 2


def _infer_period(rows: list):
    for row in rows:
        if row.paid_date is not None:
            return f"{row.paid_date.year + 543:04d}-{row.paid_date.month:02d}"
    return None


def _print_summary(in_path, candidates, payer_col, rows, period, total, issues) -> None:
    print(f"[进料] {in_path.name} → {len(rows)} 行 · 期 {period or '未知'}")
    print("  猜列:")
    for field_key, cand in candidates.items():
        print(f"    {field_key:14s} ← 列 {cand.column} [{cand.confidence}] {cand.reason}")
    print(
        f"    payer_id       ← 列 {payer_col}(付款方税号·全表同值)"
        if payer_col is not None
        else "    payer_id       ← 未识别"
    )
    print(f"  Σ支付金额: {total}")
    print(f"  issues: {len(issues)}")
    for issue in issues[:30]:
        loc = f"行{issue.row_no}" if issue.row_no else "整表"
        print(f"    - [{issue.kind}] {loc} {issue.field}: {issue.message} {issue.value}")
    if len(issues) > 30:
        print(f"    ... 另有 {len(issues) - 30} 条")


def _write_outputs(out_dir: Path, rows: list, payer_col, raw_rows: list, period) -> None:
    # 写字节而非 write_text:Windows 文本模式会把 "\r\n" 二次翻译成 "\r\r\n",破坏上传件的
    # 精确 CR/LF(官方 §8)——上传件必须字节精确。
    (out_dir / "pnd1_attach.txt").write_bytes(pnd1_attach.build_attachment(rows).encode("utf-8"))
    (out_dir / "pnd1_keying.xlsx").write_bytes(keying_sheet.build_workbook(rows))

    nid = _payer_id(payer_col, raw_rows)
    tax_year, tax_month = _year_month(period)
    central = rdprep_pnd1.build_file(
        {
            "SENDER_NID": nid,
            "NID": nid,
            "SENDER_ROLE": "1",
            "BRANCH_NO": "000000",
            "DEPT_NAME": "สำนักงานใหญ่",
            "LTO": "0",
            "TAX_MONTH": tax_month,
            "TAX_YEAR": tax_year,
            "FORM_TYPE": "00",
            "USER_ID": "",
            "FORM_FLAG": "2",
        },
        rows,
        branch_no="000000",
    )
    (out_dir / "pnd1_central.txt").write_bytes(central.encode("utf-8"))
    print(f"  写出: pnd1_attach.txt · pnd1_keying.xlsx · pnd1_central.txt → {out_dir}")
    print("  注:中央格式地址字段(อำเภอ/จังหวัด/รหัสไปรษณีย์)无数据源留空(诚实降级,见 rdprep_pnd1)")


def _payer_id(payer_col, raw_rows: list) -> str:
    if payer_col is None:
        return ""
    for raw in raw_rows:
        if payer_col < len(raw) and raw[payer_col] is not None:
            return intake.coerce_id(raw[payer_col])
    return ""


def _year_month(period) -> tuple:
    if not period:
        return "", ""
    year, month = period.split("-")
    return year, month


if __name__ == "__main__":
    sys.exit(main())
