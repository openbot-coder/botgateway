"""Test botcli module"""

import json
import pytest
from unittest.mock import MagicMock, patch
from io import StringIO

from botgateway.cli.botcli import cmd_health, cmd_status


class TestCmdHealth:
    """Test cmd_health function"""

    def test_health_without_token_exits_with_error(self):
        """反例: 无 token 时退出并报错"""
        args = MagicMock()
        args.server = "http://localhost:8000"
        args.token = None

        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(SystemExit) as exc_info:
                cmd_health(args)
            assert exc_info.value.code == 1

    def test_health_with_token_success(self):
        """正例: 有效 token 时成功获取健康信息"""
        args = MagicMock()
        args.server = "http://localhost:8000"
        args.token = "valid-token"

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "status": "healthy",
            "server_time": "2026-05-02T00:00:00Z"
        }).encode()

        mock_urlopen = MagicMock()
        mock_urlopen.__enter__ = MagicMock(return_value=mock_response)
        mock_urlopen.__exit__ = MagicMock(return_value=False)

        with patch('botgateway.cli.botcli.urlopen', return_value=mock_urlopen):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                cmd_health(args)
                output = fake_out.getvalue()
                assert "healthy" in output

    def test_health_with_404_response(self):
        """反例: 服务返回 404 时显示 Not Found"""
        args = MagicMock()
        args.server = "http://localhost:8000"
        args.token = "wrong-token"

        from urllib.error import HTTPError
        mock_response = MagicMock()
        mock_response.code = 404
        mock_response.read.return_value = b"{}"

        mock_error = HTTPError(
            "http://localhost:8000/health",
            404,
            "Not Found",
            {},
            mock_response
        )

        with patch('botgateway.cli.botcli.urlopen', side_effect=mock_error):
            with patch('sys.stderr', new=StringIO()) as fake_err:
                with pytest.raises(SystemExit) as exc_info:
                    cmd_health(args)
                assert exc_info.value.code == 1
                assert "Not Found" in fake_err.getvalue()


class TestCmdStatus:
    """Test cmd_status function"""

    def test_status_without_token_exits_with_error(self):
        """反例: 无 token 时退出并报错"""
        args = MagicMock()
        args.server = "http://localhost:8000"
        args.token = None

        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(SystemExit) as exc_info:
                cmd_status(args)
            assert exc_info.value.code == 1

    def test_status_with_token_success(self):
        """正例: 有效 token 时成功获取状态"""
        args = MagicMock()
        args.server = "http://localhost:8000"
        args.token = "valid-token"

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "status": "healthy",
            "server_time": "2026-05-02T00:00:00Z"
        }).encode()

        mock_urlopen = MagicMock()
        mock_urlopen.__enter__ = MagicMock(return_value=mock_response)
        mock_urlopen.__exit__ = MagicMock(return_value=False)

        with patch('botgateway.cli.botcli.urlopen', return_value=mock_urlopen):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                cmd_status(args)
                output = fake_out.getvalue()
                assert "Status: healthy" in output

    def test_status_with_404_response(self):
        """反例: 服务返回 404 时显示 Not Found"""
        args = MagicMock()
        args.server = "http://localhost:8000"
        args.token = "wrong-token"

        from urllib.error import HTTPError
        mock_response = MagicMock()
        mock_response.code = 404
        mock_response.read.return_value = b"{}"

        mock_error = HTTPError(
            "http://localhost:8000/health",
            404,
            "Not Found",
            {},
            mock_response
        )

        with patch('botgateway.cli.botcli.urlopen', side_effect=mock_error):
            with patch('sys.stderr', new=StringIO()) as fake_err:
                with pytest.raises(SystemExit) as exc_info:
                    cmd_status(args)
                assert exc_info.value.code == 1
                assert "Not Found" in fake_err.getvalue()

    def test_health_with_network_error(self):
        """反例: 网络错误时显示错误信息"""
        args = MagicMock()
        args.server = "http://localhost:8000"
        args.token = "valid-token"

        from urllib.error import URLError
        mock_error = URLError("Connection refused")

        with patch('botgateway.cli.botcli.urlopen', side_effect=mock_error):
            with patch('sys.stderr', new=StringIO()) as fake_err:
                with pytest.raises(SystemExit) as exc_info:
                    cmd_health(args)
                assert exc_info.value.code == 1

    def test_status_with_network_error(self):
        """反例: 网络错误时显示不可达"""
        args = MagicMock()
        args.server = "http://localhost:8000"
        args.token = "valid-token"

        from urllib.error import URLError
        mock_error = URLError("Connection refused")

        with patch('botgateway.cli.botcli.urlopen', side_effect=mock_error):
            with patch('sys.stderr', new=StringIO()) as fake_err:
                with pytest.raises(SystemExit) as exc_info:
                    cmd_status(args)
                assert exc_info.value.code == 1
                assert "Unreachable" in fake_err.getvalue()

    def test_health_with_env_token(self):
        """正例: 使用环境变量中的 token"""
        args = MagicMock()
        args.server = "http://localhost:8000"
        args.token = None

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "status": "healthy"
        }).encode()

        mock_urlopen = MagicMock()
        mock_urlopen.__enter__ = MagicMock(return_value=mock_response)
        mock_urlopen.__exit__ = MagicMock(return_value=False)

        with patch.dict('os.environ', {'BOTGATEWAY_TOKEN': 'env-token'}):
            with patch('botgateway.cli.botcli.urlopen', return_value=mock_urlopen):
                with patch('sys.stdout', new=StringIO()):
                    cmd_health(args)