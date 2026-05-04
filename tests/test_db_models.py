"""Test db models"""

import pytest

from botgateway.db.models import (
    ApiKey,
    Model,
    ModelGroup,
    ModelGroupMember,
    Provider,
    generate_id,
    now_iso,
)


class TestProvider:
    """Test Provider model"""

    def test_create_generates_id_and_timestamps(self):
        """正例: create 方法生成 id 和时间戳"""
        provider = Provider.create(name="openai", api_type="openai")
        assert provider.id is not None
        assert provider.name == "openai"
        assert provider.api_type == "openai"
        assert provider.is_active is True
        assert provider.created_at is not None
        assert provider.updated_at is not None

    def test_create_with_base_url(self):
        """正例: create 方法支持 base_url"""
        provider = Provider.create(
            name="custom",
            api_type="openai",
            base_url="https://api.example.com"
        )
        assert provider.base_url == "https://api.example.com"

    def test_to_dict_contains_required_fields(self):
        """正例: to_dict 返回所有必需字段"""
        provider = Provider.create(name="test", api_type="openai")
        data = provider.to_dict()
        assert "id" in data
        assert "name" in data
        assert "api_type" in data
        assert "is_active" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_to_dict_excludes_sensitive_fields(self):
        """正例: to_dict 不返回加密字段"""
        provider = Provider.create(name="test", api_type="openai")
        provider.api_key_encrypted = "secret"  # type: ignore[attr-defined]
        provider.key_nonce = "nonce"  # type: ignore[attr-defined]
        data = provider.to_dict()
        assert "api_key_encrypted" not in data
        assert "key_nonce" not in data

    def test_from_dict_creates_valid_instance(self):
        """正例: from_dict 创建有效实例"""
        data = {
            "id": "test-id",
            "name": "test-provider",
            "api_type": "anthropic",
            "base_url": "https://api.anthropic.com",
            "is_active": 1,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        provider = Provider.from_dict(data)
        assert provider.id == "test-id"
        assert provider.name == "test-provider"
        assert provider.api_type == "anthropic"
        assert provider.base_url == "https://api.anthropic.com"
        assert provider.is_active is True

    def test_from_dict_with_defaults(self):
        """边界值: from_dict 使用默认值"""
        data = {
            "id": "test-id",
            "name": "test",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        provider = Provider.from_dict(data)
        assert provider.api_type == "openai"
        assert provider.base_url is None
        assert provider.is_active is True  # 0 默认值转为 True


class TestModel:
    """Test Model model"""

    def test_create_generates_all_fields(self):
        """正例: create 方法生成所有字段"""
        model = Model.create(
            provider_id="provider-1",
            name="gpt-4",
            model_type="chat",
            max_tokens=4096,
            temperature=0.8,
            top_p=0.9,
            timeout=120,
            extra_params={"presence_penalty": 0.5}
        )
        assert model.id is not None
        assert model.provider_id == "provider-1"
        assert model.name == "gpt-4"
        assert model.model_type == "chat"
        assert model.max_tokens == 4096
        assert model.temperature == 0.8
        assert model.top_p == 0.9
        assert model.timeout == 120
        assert model.extra_params is not None

    def test_create_with_defaults(self):
        """边界值: create 使用默认值"""
        model = Model.create(provider_id="p1", name="test")
        assert model.model_type == "chat"
        assert model.temperature == 0.7
        assert model.top_p == 1.0
        assert model.timeout == 60
        assert model.is_active is True

    def test_get_extra_params_returns_dict(self):
        """正例: get_extra_params 返回字典"""
        model = Model.create(
            provider_id="p1",
            name="test",
            extra_params={"key": "value"}
        )
        params = model.get_extra_params()
        assert params == {"key": "value"}

    def test_get_extra_params_returns_none_when_empty(self):
        """边界值: get_extra_params 返回 None"""
        model = Model.create(provider_id="p1", name="test")
        params = model.get_extra_params()
        assert params is None

    def test_to_dict(self):
        """正例: to_dict 返回所有字段"""
        model = Model.create(
            provider_id="p1",
            name="test",
            extra_params={"key": "value"}
        )
        data = model.to_dict()
        assert "id" in data
        assert "provider_id" in data
        assert "name" in data
        assert "extra_params" in data
        assert data["extra_params"] == {"key": "value"}

    def test_from_dict(self):
        """正例: from_dict 创建有效实例"""
        data = {
            "id": "model-1",
            "provider_id": "provider-1",
            "name": "claude-3",
            "model_type": "chat",
            "max_tokens": 8192,
            "temperature": 0.5,
            "top_p": 0.8,
            "timeout": 60,
            "extra_params": '{"key": "value"}',
            "is_active": 1,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        model = Model.from_dict(data)
        assert model.id == "model-1"
        assert model.max_tokens == 8192


class TestModelGroup:
    """Test ModelGroup model"""

    def test_create_generates_all_fields(self):
        """正例: create 方法生成所有字段"""
        group = ModelGroup.create(
            name="my-group",
            description="Test group",
            routing_strategy="weight_random",
            retry_count=5,
            retry_delay=2,
            cooldown_period=120,
        )
        assert group.id is not None
        assert group.name == "my-group"
        assert group.description == "Test group"
        assert group.routing_strategy == "weight_random"
        assert group.retry_count == 5
        assert group.retry_delay == 2
        assert group.cooldown_period == 120
        assert group.is_active is True

    def test_create_with_defaults(self):
        """边界值: create 使用默认值"""
        group = ModelGroup.create(name="default-group")
        assert group.routing_strategy == "fallback"
        assert group.retry_count == 3
        assert group.retry_delay == 1
        assert group.cooldown_period == 60

    def test_to_dict(self):
        """正例: to_dict 返回所有字段"""
        group = ModelGroup.create(name="test")
        data = group.to_dict()
        assert "id" in data
        assert "name" in data
        assert "routing_strategy" in data
        assert "retry_count" in data

    def test_from_dict(self):
        """正例: from_dict 创建有效实例"""
        data = {
            "id": "group-1",
            "name": "production",
            "description": "Production models",
            "routing_strategy": "fallback",
            "retry_count": 3,
            "retry_delay": 1,
            "cooldown_period": 60,
            "is_active": 1,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        group = ModelGroup.from_dict(data)
        assert group.name == "production"
        assert group.routing_strategy == "fallback"


class TestModelGroupMember:
    """Test ModelGroupMember model"""

    def test_create_generates_all_fields(self):
        """正例: create 方法生成所有字段"""
        member = ModelGroupMember.create(
            group_id="group-1",
            model_id="model-1",
            priority=1,
            weight=10,
        )
        assert member.id is not None
        assert member.group_id == "group-1"
        assert member.model_id == "model-1"
        assert member.priority == 1
        assert member.weight == 10

    def test_create_with_defaults(self):
        """边界值: create 使用默认值"""
        member = ModelGroupMember.create(group_id="g1", model_id="m1")
        assert member.priority == 0
        assert member.weight == 1

    def test_to_dict(self):
        """正例: to_dict 返回所有字段"""
        member = ModelGroupMember.create(group_id="g1", model_id="m1")
        data = member.to_dict()
        assert "id" in data
        assert "group_id" in data
        assert "model_id" in data
        assert "priority" in data
        assert "weight" in data

    def test_from_dict(self):
        """正例: from_dict 创建有效实例"""
        data = {
            "id": "member-1",
            "group_id": "group-1",
            "model_id": "model-1",
            "priority": 2,
            "weight": 20,
            "created_at": "2024-01-01T00:00:00",
        }
        member = ModelGroupMember.from_dict(data)
        assert member.priority == 2
        assert member.weight == 20


class TestApiKey:
    """Test ApiKey model"""

    def test_create_generates_all_fields(self):
        """正例: create 方法生成所有字段"""
        api_key = ApiKey.create(
            name="test-key",
            api_key_hash="abc123hash",
        )
        assert api_key.id is not None
        assert api_key.name == "test-key"
        assert api_key.api_key_hash == "abc123hash"
        assert api_key.is_active is True
        assert api_key.created_at is not None
        assert api_key.updated_at is not None

    def test_to_dict_contains_required_fields(self):
        """正例: to_dict 返回所有字段"""
        api_key = ApiKey.create(name="test", api_key_hash="hash")
        data = api_key.to_dict()
        assert "id" in data
        assert "name" in data
        assert "api_key_hash" in data
        assert "is_active" in data

    def test_from_dict(self):
        """正例: from_dict 创建有效实例"""
        data = {
            "id": "key-1",
            "name": "production-key",
            "api_key_hash": "hash456",
            "is_active": 1,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        api_key = ApiKey.from_dict(data)
        assert api_key.name == "production-key"
        assert api_key.is_active is True


class TestHelperFunctions:
    """Test helper functions"""

    def test_generate_id_returns_uuid_string(self):
        """正例: generate_id 返回 UUID 字符串"""
        id1 = generate_id()
        id2 = generate_id()
        assert isinstance(id1, str)
        assert len(id1) == 36  # UUID 格式
        assert id1 != id2  # 每次生成不同 ID

    def test_now_iso_returns_iso_format(self):
        """正例: now_iso 返回 ISO 格式时间"""
        timestamp = now_iso()
        assert isinstance(timestamp, str)
        assert "T" in timestamp  # ISO 格式包含 T
        assert "Z" not in timestamp  # 不包含 Z（utcnow 返回的不带 Z）
