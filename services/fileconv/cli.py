# -*- coding: utf-8 -*-
"""命令行:python -m services.fileconv.cli <in.pdf|图片> <out.xlsx>

转换 + 守恒校验,写出 xlsx,并在 stdout 打印摘要(含不平行点名)。扫描件/图片走 OCR 桥。
退出码:0 = 转换成功且守恒全过;2 = 转换成功但有守恒 issue;3 = 拒绝(无文字层且 OCR
读不全/不可用);1 = 用法/IO 错误。
"""

import sys
from pathlib import Path

from services.fileconv.convert import convert_image, convert_pdf
from services.fileconv.model import REJECT_STATUSES
from services.fileconv.xlsx_out import build_xlsx

_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")


def _make_stdout_encoding_safe() -> None:
    """摘要含泰文/中文/特殊符号,而目标用户控制台编码不一(cp874/cp936/utf-8)。

    保留控制台原生编码(cp874 下泰文照常显示),编码不了的字符退化为 '?',
    绝不让成功路径因打印崩溃。
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")


def main(argv=None) -> int:
    _make_stdout_encoding_safe()
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("用法: python -m services.fileconv.cli <in.pdf> <out.xlsx>")
        return 1

    in_path, out_path = Path(argv[0]), Path(argv[1])
    if not in_path.is_file():
        print(f"输入文件不存在: {in_path}")
        return 1

    converter = convert_image if in_path.suffix.lower() in _IMAGE_EXTS else convert_pdf
    result = converter(in_path.read_bytes(), source_name=in_path.name)

    if result.status in REJECT_STATUSES:
        reason = result.stats.get("reason", "")
        print(f"[REJECT] {in_path.name}: {result.status} · {reason}")
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
