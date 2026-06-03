# -*- coding: utf-8 -*-
"""email_ingest · 密码 Fernet 加解密 + 可用性探测 leaf。

密钥从环境变量 EMAIL_ENCRYPTION_KEY 读 · cryptography 未装则回退 base64 警告模式。
"""

import os
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_FERNET = None
_FERNET_INIT_DONE = False


def _get_fernet():
    """懒加载 Fernet · 失败不炸 · 降级 base64 + 警告"""
    global _FERNET, _FERNET_INIT_DONE
    if _FERNET_INIT_DONE:
        return _FERNET
    _FERNET_INIT_DONE = True
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        logger.error(
            "[email_ingest] cryptography 未安装 · 密码将降级 base64 明文存储(不安全 · 仅开发用)"
        )
        return None

    key = os.environ.get("EMAIL_ENCRYPTION_KEY", "").strip()
    if not key:
        # 首次生成一个提示给部署者
        generated = Fernet.generate_key().decode()
        logger.error("=" * 60)
        logger.error("[email_ingest] EMAIL_ENCRYPTION_KEY 未配置!")
        logger.error("请在 HF Space Secrets 中添加:")
        logger.error(f"  EMAIL_ENCRYPTION_KEY = {generated}")
        logger.error("未配置前邮箱抓取功能将禁用")
        logger.error("=" * 60)
        return None

    try:
        _FERNET = Fernet(key.encode() if isinstance(key, str) else key)
        logger.info("[email_ingest] Fernet 加密已就绪")
        return _FERNET
    except Exception as e:
        logger.error(f"[email_ingest] Fernet 初始化失败: {e}")
        return None


def encrypt_password(plaintext: str) -> bytes:
    """加密密码 · 返回 bytes(存 bytea 字段)"""
    f = _get_fernet()
    if not plaintext:
        return b""
    if f is None:
        # 降级模式 · 至少不是明文(但不是真的加密)
        return base64.b64encode(plaintext.encode("utf-8"))
    return f.encrypt(plaintext.encode("utf-8"))


def decrypt_password(cipher: bytes) -> Optional[str]:
    """解密密码 · 返回明文或 None"""
    if not cipher:
        return None
    f = _get_fernet()
    if f is None:
        try:
            return base64.b64decode(cipher).decode("utf-8")
        except Exception:
            return None
    try:
        return f.decrypt(bytes(cipher)).decode("utf-8")
    except Exception as e:
        logger.error(f"[email_ingest] 解密失败: {e}")
        return None


def is_available() -> bool:
    """外部判断邮箱抓取是否可用"""
    return _get_fernet() is not None
