"""
kms_helper.py · v118.27.8.0
============================
Pearnly 内部对称加密工具 · 用于加密第三方 ERP 凭据(MR.ERP 用户名/密码等)

用法:
    from kms_helper import encrypt_str, decrypt_str
    cipher = encrypt_str("mypassword")     # 存数据库
    plain  = decrypt_str(cipher)           # 用前解密

环境变量:
    PEARNLY_KMS_KEY  Fernet key(44 字符 base64 · 必须 32 字节解码后)
                     生成方式:
                     python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
                     已在服务器 .env 配好(2026-05-10)

设计原则:
    - 所有 ERP 凭据 · 包括 MR.ERP / Xero refresh_token / FlowAccount API key 等
      都走这层 · 不许明文进 DB
    - key 永远只在 server-side env · 不在 git · 不在 client
    - 失败 fail-fast:env 缺失 → ImportError(让服务起不来 · 不要静默)
"""

import os
from cryptography.fernet import Fernet, InvalidToken

_KEY = os.environ.get("PEARNLY_KMS_KEY", "").strip()
if not _KEY:
    raise ImportError(
        "PEARNLY_KMS_KEY env 未设置 · 服务无法启动。"
        "服务器执行:python3 -c 'from cryptography.fernet import Fernet; "
        "print(Fernet.generate_key().decode())' · 写入 /opt/mrpilot/.env"
    )

try:
    _FERNET = Fernet(_KEY.encode() if isinstance(_KEY, str) else _KEY)
except Exception as e:
    raise ImportError(f"PEARNLY_KMS_KEY 格式无效(必须 Fernet generate_key 输出):{e}")


def encrypt_str(plaintext: str) -> str:
    """加密字符串 · 返回 base64 字符串(可直接存 TEXT 字段)"""
    if plaintext is None:
        return None
    if not isinstance(plaintext, str):
        plaintext = str(plaintext)
    return _FERNET.encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_str(ciphertext: str) -> str:
    """解密 · 失败抛 ValueError(不返回部分明文)"""
    if ciphertext is None:
        return None
    if not isinstance(ciphertext, str):
        ciphertext = str(ciphertext)
    try:
        return _FERNET.decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except InvalidToken as e:
        raise ValueError(f"凭据解密失败(可能 KMS_KEY 已轮换):{e}")


def is_encrypted(s: str) -> bool:
    """启发式判断字符串是否已加密(用于迁移老数据)"""
    if not isinstance(s, str) or len(s) < 60:
        return False
    return s.startswith("gAAAAA")  # Fernet token 固定前缀


if __name__ == "__main__":
    # 自测
    sample = "test01_password_!@#中文泰文สวัสดี"
    enc = encrypt_str(sample)
    dec = decrypt_str(enc)
    assert dec == sample, "加解密不一致!"
    print("✅ 自测通过")
    print(f"明文: {sample}")
    print(f"密文: {enc[:60]}...")
    print(f"解密: {dec}")
