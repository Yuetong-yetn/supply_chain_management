"""密码哈希工具 — 使用 PBKDF2-SHA256。

与 schema/seed.sql 中的哈希格式兼容。
哈希格式: $pbkdf2-sha256$iterations$salt_b64$hash_b64
"""

import base64
import hashlib
import secrets

ALGORITHM = "pbkdf2-sha256"
DEFAULT_ITERATIONS = 29000
SALT_BYTES = 16


def hash_password(password: str, iterations: int = DEFAULT_ITERATIONS) -> str:
    """对密码进行 PBKDF2-SHA256 哈希，返回标准格式字符串。"""
    salt = secrets.token_bytes(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    salt_b64 = _b64encode(salt)
    hash_b64 = _b64encode(dk)
    return f"${ALGORITHM}${iterations}${salt_b64}${hash_b64}"


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码是否与存储的哈希匹配。"""
    if not password_hash or not password_hash.startswith("$"):
        return False
    parts = password_hash.split("$")
    if len(parts) != 5:
        return False
    _, algo, iterations_str, salt_b64, hash_b64 = parts
    if algo != ALGORITHM:
        return False
    try:
        iterations = int(iterations_str)
        salt = _b64decode(salt_b64)
        expected_hash = _b64decode(hash_b64)
    except (ValueError, Exception):
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return dk == expected_hash


def _b64encode(data: bytes) -> str:
    """Base64 编码（使用与 seed.sql 兼容的格式）。"""
    return base64.b64encode(data).decode("ascii").rstrip("=")


def _b64decode(data: str) -> bytes:
    """Base64 解码，补全缺失的填充。"""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.b64decode(data)
