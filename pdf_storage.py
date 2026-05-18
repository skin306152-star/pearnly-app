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

logger = logging.getLogger(__name__)

PDF_STORAGE_BASE = os.environ.get("PDF_STORAGE_DIR", "/opt/mrpilot/storage/pdfs")


def save_pdf(user_id: str, content: bytes) -> Tuple[Optional[str], int]:
    """
    保存 PDF 到本地文件系统。
    
    Args:
        user_id: 用户 UUID(我们只用前 8 位作为目录名)
        content: PDF 字节流
    
    Returns:
        (相对路径, 字节数) · 失败返回 (None, 0)
    """
    if not content:
        return None, 0
    try:
        user_short = str(user_id).replace("-", "")[:8]
        ym = datetime.now().strftime("%Y-%m")
        fname = f"{uuid.uuid4().hex}.pdf"
        rel = f"{user_short}/{ym}/{fname}"
        abs_path = Path(PDF_STORAGE_BASE) / rel
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(content)
        size = len(content)
        logger.info(f"💾 PDF saved · user={user_short} · path={rel} · size={size}B")
        return rel, size
    except Exception as e:
        logger.error(f"❌ PDF save failed · user={user_id} · err={e}")
        return None, 0


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
