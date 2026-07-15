"""
v114 · PDF 留底存储模块

本地文件系统存储 · 路径规则:
  {PDF_STORAGE_DIR}/{user_id_短8位}/{YYYY-MM}/{uuid}.pdf

设计要点:
- 不依赖外部对象存储 · 简单可靠 · 备份用 rsync
- 月份分目录 · 防止单目录文件过多 · 便于按月归档/清理
- user_id 短截断 · 平衡隐私与可调试性
- 失败不阻塞主流程 · OCR 不能因为留底失败而失败

环境变量:
  PDF_STORAGE_DIR (默认 /opt/mrpilot/storage/pdfs)
"""

import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from core import file_crypto

logger = logging.getLogger(__name__)

PDF_STORAGE_BASE = os.environ.get("PDF_STORAGE_DIR", "/opt/mrpilot/storage/pdfs")


def save_pdf(user_id: str, content: bytes) -> Tuple[Optional[str], int]:
    """保存 PDF 到本地文件系统(user_id 取前 8 位作目录)· 失败返回 (None, 0)。"""
    rel, size = save_bytes(user_id, content, ".pdf")
    if rel:
        logger.info(f"💾 PDF saved · path={rel} · size={size}B")
    return rel, size


def save_bytes(user_id: str, content: bytes, suffix: str = ".bin") -> Tuple[Optional[str], int]:
    """通用字节落盘(PDF 留底 / 进项票图等)· {user前8}/{YYYY-MM}/{uuid}{保留扩展名}。"""
    if not content:
        return None, 0
    try:
        user_short = str(user_id).replace("-", "")[:8]
        ym = datetime.now().strftime("%Y-%m")
        safe = suffix if (suffix.startswith(".") and 2 <= len(suffix) <= 6) else ".bin"
        rel = f"{user_short}/{ym}/{uuid.uuid4().hex}{safe}"
        abs_path = Path(PDF_STORAGE_BASE) / rel
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        # size 记明文长度(计费/展示口径不变),盘上按开关落密文。
        abs_path.write_bytes(file_crypto.maybe_seal(content))
        return rel, len(content)
    except Exception as e:
        logger.error(f"❌ save_bytes failed · user={user_id} · err={e}")
        return None, 0


def read_bytes(rel_path: str) -> Optional[bytes]:
    """按相对路径取留底原文(双轨解密):密文解回明文,存量明文原样返;缺失/越界返 None。
    票图打包/凭证外呼/归档导出等一切消费方经此取字节,不再裸 read_bytes 拿到密文。"""
    p = get_pdf_abs_path(rel_path)
    if not p or not p.exists():
        return None
    return file_crypto.unseal(p.read_bytes())


def get_pdf_abs_path(rel_path: str) -> Optional[Path]:
    """根据相对路径取绝对路径 · 文件不存在返回 None"""
    if not rel_path:
        return None
    try:
        # 防路径穿越攻击:rel_path 不能含 ..
        if ".." in rel_path or rel_path.startswith("/"):
            logger.warning(f"⚠️ blocked malicious path: {rel_path}")
            return None
        p = Path(PDF_STORAGE_BASE) / rel_path
        # 确认 p 真的在 PDF_STORAGE_BASE 之下
        if not str(p.resolve()).startswith(str(Path(PDF_STORAGE_BASE).resolve())):
            logger.warning(f"⚠️ path escape attempt: {rel_path}")
            return None
        return p if p.exists() else None
    except Exception as e:
        logger.error(f"❌ get_pdf_abs_path failed · path={rel_path} · err={e}")
        return None


def delete_pdf(rel_path: str) -> bool:
    """删除一个 PDF · 不存在视为成功(幂等)"""
    if not rel_path:
        return True
    try:
        p = get_pdf_abs_path(rel_path)
        if p and p.exists():
            p.unlink()
            logger.info(f"🗑️ PDF deleted · path={rel_path}")
        return True
    except Exception as e:
        logger.error(f"❌ PDF delete failed · path={rel_path} · err={e}")
        return False


def storage_health_check() -> dict:
    """启动检查 · 看存储目录可写"""
    base = Path(PDF_STORAGE_BASE)
    try:
        base.mkdir(parents=True, exist_ok=True)
        # 写一个测试文件
        test = base / ".health_check"
        test.write_text("ok")
        test.unlink()
        return {"ok": True, "path": str(base)}
    except Exception as e:
        return {"ok": False, "path": str(base), "err": str(e)}
