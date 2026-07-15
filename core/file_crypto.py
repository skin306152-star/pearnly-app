# -*- coding: utf-8 -*-
"""文件信封加密层(ENC-a · 落盘即密)。

对落盘的客户资料(工单来料/交付物/OCR 留底/知识库/LINE 收料/对账产物)做静态加密。
和 kms_helper(ERP 凭据 Fernet)是两把独立密钥:ERP 凭据泄露不连坐文件,反之亦然。

信封格式(每个文件一把随机 DEK,KEK 只包 DEK 不碰明文,为将来只换 KEK 不重写密文留位):

    MAGIC"PENC1"(5B) + ver(1B) + wrappedDEK 长度(2B,大端) + Fernet(KEK).encrypt(DEK)
    + nonce(12B) + AESGCM(DEK).encrypt(nonce, plaintext)

双轨读常驻:读侧嗅探 MAGIC,有则解包解密,无则按存量明文原样返回——迁移中断/明密混布
全程可读。

开关:
    FILE_ENC_MODE=off|on  默认 off,off 时 maybe_seal 不加密 = 行为与今天逐字节一致。
    PEARNLY_FILE_KMS_KEY  Fernet key(kms_helper 同款生成方式)。
    on 且 KEK 缺失 → 启动 fail-fast(照 kms_helper 先例),绝不静默明文。

sha256 语义不变(命门):dedupe_key / freeze_manifest / image_sha256 全部是明文哈希——
加密前算、解密后验,业务身份与查重零变化。
"""

from __future__ import annotations

import os
import struct

from cryptography.exceptions import InvalidTag
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"PENC1"
_VERSION = 1
_NONCE_LEN = 12
_LEN_FIELD = 2  # wrappedDEK 长度前缀(大端 uint16),单文件 DEK 恒 32B 远小于 64KB
_ENV_MODE = "FILE_ENC_MODE"
_ENV_KEY = "PEARNLY_FILE_KMS_KEY"


class FileCryptoError(Exception):
    """解密失败(KEK 不符 / 密文被篡改 / 信封损坏)。绝不返回部分明文。"""


def is_enabled() -> bool:
    """写侧是否加密。动态读 env(默认 off),不缓存——测试可按模式切换。"""
    return os.environ.get(_ENV_MODE, "off").strip().lower() == "on"


def _load_fernet():
    raw = os.environ.get(_ENV_KEY, "").strip()
    if not raw:
        return None
    try:
        return Fernet(raw.encode())
    except Exception as e:  # noqa: BLE001 - key 格式错要点名,不静默
        raise ImportError(f"{_ENV_KEY} 格式无效(必须 Fernet generate_key 输出):{e}")


_FERNET = _load_fernet()

# 启动 fail-fast:开了加密却没配 KEK = 会静默把客户资料写成明文,宁可起不来。
if is_enabled() and _FERNET is None:
    raise ImportError(
        f"{_ENV_MODE}=on 但 {_ENV_KEY} 未设置 · 文件加密无密钥,服务拒绝启动。"
        f"生成:python3 -c 'from cryptography.fernet import Fernet; "
        f"print(Fernet.generate_key().decode())' · 写入 .env"
    )


def _kek() -> Fernet:
    global _FERNET
    if _FERNET is None:
        _FERNET = _load_fernet()  # 延迟兜取:import 早于 env 配置时仍能加解密
    if _FERNET is None:
        raise FileCryptoError(f"{_ENV_KEY} 未设置,无法加解密文件")
    return _FERNET


def has_magic(data: bytes) -> bool:
    """字节流是否为本层密文(嗅探 MAGIC 头)。"""
    return data[: len(MAGIC)] == MAGIC


def seal(plaintext: bytes) -> bytes:
    """明文 → 信封密文(随机 DEK,KEK 包 DEK)。KEK 缺失抛错,不静默降级明文。"""
    dek = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(_NONCE_LEN)
    ciphertext = AESGCM(dek).encrypt(nonce, plaintext, None)
    wrapped = _kek().encrypt(dek)
    return (
        MAGIC + bytes([_VERSION]) + struct.pack(">H", len(wrapped)) + wrapped + nonce + ciphertext
    )


def unseal(data: bytes) -> bytes:
    """密文 → 明文;非本层格式(无 MAGIC)= 存量明文,原样返回(双轨读)。

    密文被篡改任一字节 → AESGCM 认证失败 → FileCryptoError(不吞、不返回部分明文)。
    """
    if not has_magic(data):
        return data
    try:
        off = len(MAGIC) + 1  # 跳过 MAGIC + ver
        (wrapped_len,) = struct.unpack(">H", data[off : off + _LEN_FIELD])
        off += _LEN_FIELD
        wrapped = data[off : off + wrapped_len]
        off += wrapped_len
        nonce = data[off : off + _NONCE_LEN]
        ciphertext = data[off + _NONCE_LEN :]
        dek = _kek().decrypt(wrapped)
        return AESGCM(dek).decrypt(nonce, ciphertext, None)
    except (InvalidToken, InvalidTag, struct.error, IndexError) as e:
        raise FileCryptoError(f"文件解密失败(密钥不符 / 密文损坏 / 被篡改):{e}") from e


def maybe_seal(plaintext: bytes) -> bytes:
    """写侧统一入口:开则加密,关则原样(off 态逐字节等同今天)。"""
    return seal(plaintext) if is_enabled() else plaintext
