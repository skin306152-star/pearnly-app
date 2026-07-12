# -*- coding: utf-8 -*-
"""命令行:python -m services.fileconv.cli <in.pdf> <out.xlsx>

转换 + 守恒校验,写出 xlsx,并在 stdout 打印摘要(含不平行点名)。
退出码:0 = 转换成功且守恒全过;2 = 转换成功但有守恒 issue;3 = 无文字层拒绝;1 = 用法/IO 错误。
"""

import sys
from pathlib import Path

from services.fileconv.convert import convert_pdf
from services.fileconv.model import STATUS_NO_TEXT_LAYER
from services.fileconv.xlsx_out import build_xlsx


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("用法: python -m services.fileconv.cli <in.pdf> <out.xlsx>")
        return 1

    in_path, out_path = Path(argv[0]), Path(argv[1])
    if not in_path.is_file():
        print(f"输入文件不存在: {in_path}")
        return 1

    result = convert_pdf(in_path.read_bytes(), source_name=in_path.name)

    if result.status == STATUS_NO_TEXT_LAYER:
        print(f"[REJECT] {in_path.name}: no_text_layer(疑扫描件)· 本引擎不做 OCR")
        Path(out_path).write_bytes(build_xlsx(result))
        return 3

    Path(out_path).write_bytes(build_xlsx(result))

    print(f"[OK] {in_path.name} → {out_path.name}")
    print(f"  doc_type : {result.doc_type}")
    for key, value in result.stats.items():
        shown = ", ".join(value) if isinstance(value, list) else value
        print(f"  {key:14s}: {shown}")
    print(f"  issues   : {len(result.issues)}")
    for issue in result.issues[:20]:
        print(
            f"    - [{issue.kind}] line {issue.line_no} {issue.account} "
            f"expected {issue.expected} actual {issue.actual} · {issue.message}"
        )
    if len(result.issues) > 20:
        print(f"    ... 另有 {len(result.issues) - 20} 条")
    return 0 if result.conserved else 2


if __name__ == "__main__":
    sys.exit(main())
