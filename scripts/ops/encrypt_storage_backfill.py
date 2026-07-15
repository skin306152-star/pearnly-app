# -*- coding: utf-8 -*-
"""存量文件加密回填(ENC-a · 动 prod 真文件,三道保险)。

把 workorders/pdfs/line_intake/vat_recon 已落盘的明文原地转成 file_crypto 信封密文。
三道保险(方案 §六):
  1. 幂等:已带 MAGIC 的文件跳过(重跑安全)。
  2. tmp 写 + 原子 rename:写坏不会替换掉原件。
  3. 解密回验:密文解回明文的 sha256 必须与原明文逐字节一致才 rename,否则点名停。

方向:
  默认        明文 → 密文(加密回填)
  --decrypt   密文 → 明文(完整回滚路径)
  --verify    只扫不改:报告 密文数 / 明文残留数 / 损坏数(rename 前后自检)

损坏(带 MAGIC 却解不开)= 立即点名,全批结束后 fail(非零退出),不静默略过。

需 PEARNLY_FILE_KMS_KEY(seal/unseal 都要 KEK);加密回填还需 FILE_ENC_MODE=on 或直接带 KEK 即可
(本脚本直接调 seal,不看 mode 开关)。
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core import file_crypto  # noqa: E402


class BackfillError(Exception):
    """回填过程中不可继续的错误(回验失败 / 损坏文件),带已处理计数。"""

    def __init__(self, message: str, report: dict):
        super().__init__(message)
        self.report = report


def _default_roots() -> list[Path]:
    """prod 默认落盘树(env 覆盖):workorders / pdfs / line_intake / vat_recon / slips。

    slips(ENC-b):存量搬家由 scripts/ops/migrate_slips_dir.py 一次性做(routes/static/slips
    → 本目录);搬完之后的常驻加密回填(FILE_ENC_MODE=on 时)走本工具同一套幂等逻辑。"""
    return [
        Path(os.environ.get("WORKORDER_STORAGE_DIR", "/opt/mrpilot/storage/workorders")),
        Path(os.environ.get("PDF_STORAGE_DIR", "/opt/mrpilot/storage/pdfs")),
        Path(os.environ.get("LINE_INTAKE_STORAGE_DIR", "/opt/mrpilot/storage/line_intake")),
        Path(os.environ.get("VAT_RECON_STORAGE_DIR", "/opt/mrpilot/uploads/vat_recon")),
        Path(os.environ.get("SLIPS_STORAGE_ROOT", "/opt/mrpilot/storage")) / "slips",
    ]


def _iter_files(roots: list[Path]):
    for root in roots:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            if p.is_file() and not p.name.endswith(".enc-tmp"):
                yield p


def _atomic_write(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".enc-tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def _encrypt_one(path: Path) -> str:
    data = path.read_bytes()
    if file_crypto.has_magic(data):
        file_crypto.unseal(data)  # 损坏(解不开)→ FileCryptoError 上抛,run_backfill 收作 corrupt
        return "skipped"  # 幂等:已密且完好
    plain_sha = hashlib.sha256(data).hexdigest()
    sealed = file_crypto.seal(data)
    if hashlib.sha256(file_crypto.unseal(sealed)).hexdigest() != plain_sha:
        raise BackfillError(f"回验失败(明文 sha256 漂移),已停:{path}", {})
    _atomic_write(path, sealed)
    return "converted"


def _decrypt_one(path: Path) -> str:
    data = path.read_bytes()
    if not file_crypto.has_magic(data):
        return "skipped"  # 已是明文
    plain = file_crypto.unseal(data)  # 损坏 → FileCryptoError 上抛
    _atomic_write(path, plain)
    return "converted"


def run_backfill(roots: list[Path], *, decrypt: bool = False) -> dict:
    """加密回填 / 反向解密。健康文件全部处理完,损坏文件收集后统一 fail(点名停)。"""
    report = {"converted": 0, "skipped": 0, "corrupt": []}
    op = _decrypt_one if decrypt else _encrypt_one
    for path in _iter_files(roots):
        try:
            outcome = op(path)
        except file_crypto.FileCryptoError:
            report["corrupt"].append(str(path))
            continue
        report[outcome] += 1
    if report["corrupt"]:
        raise BackfillError(
            f"发现 {len(report['corrupt'])} 个损坏文件(带 MAGIC 却解不开),点名停",
            report,
        )
    return report


def verify(roots: list[Path]) -> dict:
    """只扫不改:密文数 / 明文残留数 / 损坏数。"""
    report = {"ciphertext": 0, "plaintext": 0, "corrupt": []}
    for path in _iter_files(roots):
        data = path.read_bytes()
        if not file_crypto.has_magic(data):
            report["plaintext"] += 1
            continue
        try:
            file_crypto.unseal(data)
            report["ciphertext"] += 1
        except file_crypto.FileCryptoError:
            report["corrupt"].append(str(path))
    return report


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows cp874 控制台打中文不崩
    except (AttributeError, ValueError):
        pass
    decrypt = "--decrypt" in argv
    do_verify = "--verify" in argv
    roots = [Path(a) for a in argv if not a.startswith("--")] or _default_roots()

    if do_verify:
        rep = verify(roots)
        print(
            f"[verify] 密文={rep['ciphertext']} 明文残留={rep['plaintext']} "
            f"损坏={len(rep['corrupt'])}"
        )
        for c in rep["corrupt"]:
            print("  损坏:" + c)
        return 1 if rep["corrupt"] else 0

    try:
        rep = run_backfill(roots, decrypt=decrypt)
    except BackfillError as e:
        print(f"[backfill] 停:{e}")
        for c in e.report.get("corrupt", []):
            print("  损坏:" + c)
        return 1
    mode = "解密" if decrypt else "加密"
    print(f"[backfill·{mode}] 转换={rep['converted']} 跳过={rep['skipped']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
