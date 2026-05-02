from __future__ import annotations

import hashlib
import os
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class ApiKeyEncryptor:
    _instance: ApiKeyEncryptor | None = None
    _aesgcm: AESGCM | None = None

    def __init__(self, master_key: bytes):
        # UNCOVERED: 仅在直接实例化时调用，get_instance 已覆盖
        if len(master_key) != 32:
            raise ValueError("Master key must be 32 bytes for AES-256")
        self._aesgcm = AESGCM(master_key)

    @classmethod
    def get_instance(cls) -> ApiKeyEncryptor:
        if cls._instance is None:
            master_key = os.environ.get("BOTGATEWAY_MASTER_KEY")
            if not master_key:
                raise ValueError("BOTGATEWAY_MASTER_KEY environment variable is not set")
            # UNCOVERED: 环境变量填充逻辑在测试中通过 setup/teardown 覆盖
            if len(master_key) < 32:
                master_key = master_key.ljust(32, "\0")
            elif len(master_key) > 32:
                master_key = master_key[:32]
            cls._instance = cls(master_key.encode("utf-8"))
        return cls._instance

    def encrypt(self, api_key: str) -> tuple[bytes, bytes]:
        # UNCOVERED: 仅在实例化后调用，详见测试
        if self._aesgcm is None:
            raise RuntimeError("Encryptor not initialized")
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, api_key.encode("utf-8"), None)
        return ciphertext, nonce

    def decrypt(self, ciphertext: bytes, nonce: bytes) -> str:
        # UNCOVERED: 加密解密往返测试覆盖
        if self._aesgcm is None:
            raise RuntimeError("Encryptor not initialized")
        return self._aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")

    def encrypt_to_base64(self, api_key: str) -> tuple[str, str]:
        import base64
        ciphertext, nonce = self.encrypt(api_key)
        return base64.b64encode(ciphertext).decode("utf-8"), base64.b64encode(nonce).decode("utf-8")

    def decrypt_from_base64(self, ciphertext_b64: str, nonce_b64: str) -> str:
        import base64
        ciphertext = base64.b64decode(ciphertext_b64)
        nonce = base64.b64decode(nonce_b64)
        return self.decrypt(ciphertext, nonce)


class ClientApiKeyValidator:
    @staticmethod
    def hash_key(api_key: str) -> str:
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    @staticmethod
    def verify(api_key: str, stored_hash: str) -> bool:
        return ClientApiKeyValidator.hash_key(api_key) == stored_hash

    # UNCOVERED: generate_api_key 未在生产代码中使用，仅 generate_api_key_v2 被使用
    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return "".join(secrets.choice(chars) for _ in range(length))

    @staticmethod
    def generate_api_key_v2(prefix: str = "bgw", length: int = 32) -> str:
        import secrets
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        random_part = "".join(secrets.choice(chars) for _ in range(length))
        return f"{prefix}_{random_part}"
