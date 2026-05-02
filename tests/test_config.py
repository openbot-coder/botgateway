"""Test config module"""

import json
import tempfile
import os
from pathlib import Path

import pytest
from unittest.mock import MagicMock, patch

from botgateway.config import (
    DEFAULT_CONFIG,
    load_config,
    save_config,
    generate_token,
    get_default_config_path,
)


class TestDefaultConfig:
    """Test DEFAULT_CONFIG values"""

    def test_default_config_has_required_keys(self):
        """正例: 默认配置包含所有必需键"""
        assert "host" in DEFAULT_CONFIG
        assert "port" in DEFAULT_CONFIG
        assert "management_token" in DEFAULT_CONFIG

    def test_default_port_is_8000(self):
        """正例: 默认端口是 8000"""
        assert DEFAULT_CONFIG["port"] == 8000

    def test_default_host_is_localhost(self):
        """正例: 默认主机是 127.0.0.1"""
        assert DEFAULT_CONFIG["host"] == "127.0.0.1"

    def test_default_token_is_empty(self):
        """正例: 默认 token 为空"""
        assert DEFAULT_CONFIG["management_token"] == ""


class TestGetDefaultConfigPath:
    """Test get_default_config_path function"""

    def test_returns_path_in_home_directory(self):
        """正例: 返回用户主目录下的路径"""
        path = get_default_config_path()
        assert ".botgateway" in str(path)
        assert "config.json" in str(path)

    def test_returns_path_object(self):
        """正例: 返回 Path 对象"""
        path = get_default_config_path()
        assert isinstance(path, Path)


class TestLoadConfig:
    """Test load_config function"""

    def test_load_config_with_nonexistent_file(self):
        """反例: 配置文件不存在时返回默认配置"""
        result = load_config("/nonexistent/path/config.json")
        assert result == DEFAULT_CONFIG

    def test_load_config_returns_dict(self):
        """正例: 返回字典类型"""
        result = load_config()
        assert isinstance(result, dict)

    def test_load_config_merges_with_defaults(self):
        """边界值: 部分配置与默认配置合并"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"port": 9000}, f)
            temp_path = f.name

        try:
            result = load_config(temp_path)
            assert result["port"] == 9000
            assert result["host"] == DEFAULT_CONFIG["host"]
        finally:
            os.unlink(temp_path)

    def test_load_config_with_invalid_json(self):
        """反例: JSON 格式错误时返回默认配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json {")
            temp_path = f.name

        try:
            result = load_config(temp_path)
            assert result == DEFAULT_CONFIG
        finally:
            os.unlink(temp_path)


class TestSaveConfig:
    """Test save_config function"""

    def test_save_config_creates_directory(self):
        """正例: 保存配置时创建目录"""
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, "subdir", "config.json")

        config = {"host": "0.0.0.0", "port": 9000, "management_token": "test"}
        save_config(config, temp_path)

        assert os.path.exists(os.path.dirname(temp_path))
        os.unlink(temp_path)
        os.rmdir(os.path.dirname(temp_path))
        os.rmdir(temp_dir)

    def test_save_config_writes_json(self):
        """正例: 正确写入 JSON 文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        config = {"host": "0.0.0.0", "port": 9000, "management_token": "test"}
        save_config(config, temp_path)

        with open(temp_path, 'r') as f:
            saved = json.load(f)

        assert saved["host"] == "0.0.0.0"
        assert saved["port"] == 9000
        os.unlink(temp_path)

    def test_save_config_uses_default_path(self):
        """边界值: config_path 为 None 时使用默认路径"""
        with patch('botgateway.config.get_default_config_path') as mock_get_path:
            mock_path = MagicMock()
            mock_path.parent = MagicMock()
            mock_get_path.return_value = mock_path

            config = {"host": "0.0.0.0", "port": 9000, "management_token": "test"}
            save_config(config, None)

            mock_get_path.assert_called_once()
            mock_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestGenerateToken:
    """Test generate_token function"""

    def test_generate_token_returns_string(self):
        """正例: 返回字符串类型"""
        token = generate_token()
        assert isinstance(token, str)

    def test_generate_token_default_length(self):
        """正例: 默认生成 32 字符的 token"""
        token = generate_token()
        assert len(token) == 32

    def test_generate_token_custom_length(self):
        """边界值: 自定义长度的 token"""
        token = generate_token(length=16)
        assert len(token) == 16

    def test_generate_token_is_alphanumeric(self):
        """正例: token 仅包含字母和数字"""
        token = generate_token()
        assert token.isalnum()

    def test_generate_token_unique(self):
        """正例: 每次生成的 token 不同"""
        token1 = generate_token()
        token2 = generate_token()
        assert token1 != token2