# -*- coding: utf-8 -*-
"""email_ingest · 密码 Fernet 加解密 + 可用性探测 leaf。

密钥从环境变量 EMAIL_ENCRYPTION_KEY 读。cryptography 是全仓硬依赖(requirements.txt·
core/kms_helper.py 同款前提)· 缺失直接 fail-fast(ENC-c · 同 kms_helper.py:27-33 纪律),
不再降级 base64 假加密——那只是给"看起来加密了"的错觉,任何拿到 DB 的人都能直接解开。
"""

import base64
import os
import logging
from typing import Optional

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError as e:
    raise ImportError(
        "email_ingest_crypto: cryptography 未安装 · 服务无法启动"
        "(邮箱抓取密码加解密强依赖,requirements.txt 已列 · 检查虚拟环境)。"
    ) from e

logger = logging.getLogger(__name__)

_FERNET = None
_FERNET_INIT_DONE = False

# 真 Fernet token 固定以此起(version byte 0x80 base64 后的前缀·同 core/kms_helper.is_encrypted
# 的判据),ENC-c 前 base64(plaintext) 降级行不会长这样 · 供 decrypt_password 区分两种失败原因。
_FERNET_TOKEN_PREFIX = b"gAAAAA"


def _get_fernet():
    """懒加载 Fernet · EMAIL_ENCRYPTION_KEY 未配置时返回 None(功能优雅禁用 · 非本批堵的洞——
    那是运维没配置密钥的合法状态,is_available() 会如实报不可用)。"""
    global _FERNET, _FERNET_INIT_DONE
    if _FERNET_INIT_DONE:
        return _FERNET
    _FERNET_INIT_DONE = True

    key = os.environ.get("EMAIL_ENCRYPTION_KEY", "").strip()
    if not key:
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
    """加密密码 · 返回 bytes(存 bytea 字段)。

    调用方须先过 is_available() 闸(routes/email_ingest_routes.py 已做);key 未配置时到这里
    是调用方没守闸,直接 raise ——绝不再假加密 base64 落库(ENC-c 堵洞)。
    """
    if not plaintext:
        return b""
    f = _get_fernet()
    if f is None:
        raise RuntimeError(
            "email_ingest: EMAIL_ENCRYPTION_KEY 未配置 · 拒绝落库(is_available 先查)"
        )
    return f.encrypt(plaintext.encode("utf-8"))


def decrypt_password(cipher: bytes) -> Optional[str]:
    """解密密码 · 返回明文或 None(解密失败/未配置密钥一律 None · 绝不猜/绝不吐部分明文)。"""
    if not cipher:
        return None
    f = _get_fernet()
    if f is None:
        logger.error("[email_ingest] 解密失败:EMAIL_ENCRYPTION_KEY 未配置")
        return None
    try:
        return f.decrypt(bytes(cipher)).decode("utf-8")
    except InvalidToken:
        if _looks_like_legacy_base64_downgrade(cipher):
            logger.error(
                "[email_ingest] 解密失败:该账号密码是 ENC-c 之前的 base64 降级数据"
                "(非真加密)· 已停止兼容 · 需用户重新绑定邮箱密码"
            )
        else:
            logger.error("[email_ingest] 解密失败:Fernet token 无效(密钥轮换或数据损坏)")
        return None
    except Exception as e:
        logger.error(f"[email_ingest] 解密异常: {e}")
        return None


def _looks_like_legacy_base64_downgrade(cipher: bytes) -> bool:
    """启发式识别『ENC-c 前 base64(plaintext) 假加密』行 · 区别于真 Fernet token 损坏/密钥轮换。

    不是 _FERNET_TOKEN_PREFIX 起头,又能被 base64 解出合法 utf-8 文本 → 判定是老 base64(plaintext)
    降级行(真 Fernet 密文经 base64 解码后是高熵二进制,几乎不可能恰好是合法 utf-8)。
    """
    if cipher.startswith(_FERNET_TOKEN_PREFIX):
        return False
    try:
        base64.b64decode(cipher, validate=True).decode("utf-8")
        return True
    except Exception:
        return False


def is_available() -> bool:
    """外部判断邮箱抓取是否可用"""
    return _get_fernet() is not None
