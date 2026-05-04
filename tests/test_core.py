"""Test core modules"""

import os
import time

import pytest

from botgateway.core.encryptor import (
    ApiKeyEncryptor,
    ClientApiKeyValidator,
)
from botgateway.core.router import CooldownTracker
from botgateway.core.retry import ErrorRetryHandler, RetryConfig


class TestClientApiKeyValidator:
    """Test ClientApiKeyValidator"""

    def test_hash_key_returns_hex_string(self):
        """正例: hash_key 返回十六进制字符串"""
        validator = ClientApiKeyValidator()
        hash1 = validator.hash_key("test-api-key")
        hash2 = validator.hash_key("test-api-key")
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA-256 哈希长度
        assert hash1 == hash2  # 相同输入产生相同哈希

    def test_hash_key_different_inputs_different_hashes(self):
        """边界值: 不同输入产生不同哈希"""
        validator = ClientApiKeyValidator()
        hash1 = validator.hash_key("key1")
        hash2 = validator.hash_key("key2")
        assert hash1 != hash2

    def test_verify_correct_key(self):
        """正例: 验证正确的密钥"""
        validator = ClientApiKeyValidator()
        api_key = "my-secret-key"
        hashed = validator.hash_key(api_key)
        assert validator.verify(api_key, hashed) is True

    def test_verify_incorrect_key(self):
        """反例: 验证错误的密钥"""
        validator = ClientApiKeyValidator()
        assert validator.verify("wrong-key", "somehash") is False

    def test_generate_api_key_v2_format(self):
        """正例: generate_api_key_v2 返回正确格式"""
        key = ClientApiKeyValidator.generate_api_key_v2(prefix="bgw", length=32)
        assert key.startswith("bgw_")
        assert len(key) == 4 + 32  # "bgw_" + 32 随机字符

    def test_generate_api_key_v2_uniqueness(self):
        """边界值: 每次生成不同的密钥"""
        keys = [ClientApiKeyValidator.generate_api_key_v2() for _ in range(10)]
        assert len(set(keys)) == 10  # 所有密钥唯一


class TestApiKeyEncryptor:
    """Test ApiKeyEncryptor - 需要 Master Key 环境变量"""

    def setup_method(self):
        """设置测试环境"""
        os.environ["BOTGATEWAY_MASTER_KEY"] = "test-master-key-32-bytes-long!!"

    def teardown_method(self):
        """清理测试环境"""
        ApiKeyEncryptor._instance = None  # type: ignore[attr-defined]
        if "BOTGATEWAY_MASTER_KEY" in os.environ:
            del os.environ["BOTGATEWAY_MASTER_KEY"]

    def test_encrypt_decrypt_roundtrip(self):
        """正例: 加密解密往返正确"""
        encryptor = ApiKeyEncryptor.get_instance()
        original = "my-secret-api-key-12345"
        ciphertext, nonce = encryptor.encrypt(original)
        decrypted = encryptor.decrypt(ciphertext, nonce)
        assert decrypted == original

    def test_encrypt_produces_different_outputs(self):
        """边界值: 每次加密产生不同输出（随机 nonce）"""
        encryptor = ApiKeyEncryptor.get_instance()
        original = "test-key"
        ciphertext1, nonce1 = encryptor.encrypt(original)
        ciphertext2, nonce2 = encryptor.encrypt(original)
        assert ciphertext1 != ciphertext2
        assert nonce1 != nonce2

    def test_encrypt_to_base64_roundtrip(self):
        """正例: Base64 加密解密往返正确"""
        encryptor = ApiKeyEncryptor.get_instance()
        original = "base64-test-key"
        ciphertext_b64, nonce_b64 = encryptor.encrypt_to_base64(original)
        decrypted = encryptor.decrypt_from_base64(ciphertext_b64, nonce_b64)
        assert decrypted == original

    def test_encrypt_to_base64_produces_strings(self):
        """正例: encrypt_to_base64 返回字符串"""
        encryptor = ApiKeyEncryptor.get_instance()
        ciphertext, nonce = encryptor.encrypt_to_base64("key")
        assert isinstance(ciphertext, str)
        assert isinstance(nonce, str)


class TestCooldownTracker:
    """Test CooldownTracker"""

    def test_record_error_and_is_in_cooldown(self):
        """正例: 记录错误后进入冷却期"""
        tracker = CooldownTracker()
        model_id = "model-1"
        timestamp = time.time()
        tracker.record_error(model_id, timestamp)
        assert tracker.is_in_cooldown(model_id, cooldown_period=60) is True

    def test_not_in_cooldown_before_record(self):
        """边界值: 记录前不在冷却期"""
        tracker = CooldownTracker()
        assert tracker.is_in_cooldown("model-x", cooldown_period=60) is False

    def test_cooldown_expires_after_period(self):
        """边界值: 冷却期过后不再冷却"""
        tracker = CooldownTracker()
        model_id = "model-1"
        old_timestamp = time.time() - 100  # 100 秒前
        tracker.record_error(model_id, old_timestamp)
        assert tracker.is_in_cooldown(model_id, cooldown_period=60) is False

    def test_clear_single_model(self):
        """正例: 清除单个模型的冷却状态"""
        tracker = CooldownTracker()
        tracker.record_error("model-1", time.time())
        tracker.clear("model-1")
        assert tracker.is_in_cooldown("model-1", cooldown_period=60) is False

    def test_clear_all(self):
        """正例: 清除所有冷却状态"""
        tracker = CooldownTracker()
        tracker.record_error("model-1", time.time())
        tracker.record_error("model-2", time.time())
        tracker.clear()
        assert tracker.is_in_cooldown("model-1", cooldown_period=60) is False
        assert tracker.is_in_cooldown("model-2", cooldown_period=60) is False


class TestErrorRetryHandler:
    """Test ErrorRetryHandler"""

    def test_record_error_increments_count(self):
        """正例: 记录错误增加计数"""
        handler = ErrorRetryHandler(RetryConfig(retry_count=3))
        handler.record_error("model-1")
        assert handler.should_retry("model-1") is True

    def test_should_retry_within_limit(self):
        """正例: 在重试次数内返回 True"""
        handler = ErrorRetryHandler(RetryConfig(retry_count=3))
        handler._retry_counts["model-1"] = 2
        assert handler.should_retry("model-1") is True

    def test_should_retry_at_limit(self):
        """边界值: 达到重试次数返回 False"""
        handler = ErrorRetryHandler(RetryConfig(retry_count=3))
        handler._retry_counts["model-1"] = 3
        assert handler.should_retry("model-1") is False

    def test_get_retry_delay_simple(self):
        """正例: 获取重试延迟（无指数退避）"""
        handler = ErrorRetryHandler(RetryConfig(retry_delay=1.0, exponential_backoff=False))
        assert handler.get_retry_delay(0) == 1.0
        assert handler.get_retry_delay(1) == 1.0

    def test_get_retry_delay_exponential(self):
        """边界值: 获取重试延迟（指数退避）"""
        handler = ErrorRetryHandler(RetryConfig(retry_delay=1.0, exponential_backoff=True))
        assert handler.get_retry_delay(0) == 1.0
        assert handler.get_retry_delay(1) == 2.0
        assert handler.get_retry_delay(2) == 4.0

    def test_reset_clears_counts_and_cooldown(self):
        """正例: reset 清除计数和冷却状态"""
        handler = ErrorRetryHandler()
        handler.record_error("model-1")
        handler.reset("model-1")
        assert handler.should_retry("model-1") is True
        assert handler.cooldown_tracker.is_in_cooldown("model-1", 60) is False

    def test_reset_all(self):
        """边界值: reset() 清除所有"""
        handler = ErrorRetryHandler()
        handler.record_error("model-1")
        handler.record_error("model-2")
        handler.reset()
        assert handler.should_retry("model-1") is True
        assert handler.should_retry("model-2") is True

    def test_from_model_group(self):
        """正例: from_model_group 正确转换"""
        from botgateway.db.models import ModelGroup
        group = ModelGroup.create(
            name="test",
            retry_count=5,
            retry_delay=2,
            cooldown_period=120
        )
        handler = ErrorRetryHandler.from_model_group(group)
        assert handler.config.retry_count == 5
        assert handler.config.retry_delay == 2.0
        assert handler.config.cooldown_period == 120

    def test_is_in_cooldown_delegates_to_tracker(self):
        """正例: is_in_cooldown 委托给追踪器"""
        handler = ErrorRetryHandler()
        handler.record_error("model-1")
        assert handler.cooldown_tracker.is_in_cooldown("model-1", 60) is True
