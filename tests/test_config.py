import os
import sys
import pytest
from unittest.mock import patch

# Ensure email_cli is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# Ensure conftest helpers are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from conftest import make_config
from email_cli import get_config, decode_mime


class TestGetConfig:
    def test_reads_required_env_vars(self):
        with patch.dict(os.environ, {
            "QQ_MAIL_USER": "user@qq.com",
            "QQ_MAIL_APP_PASSWORD": "app_pass_123",
        }):
            config = get_config()
        assert config["user"] == "user@qq.com"
        assert config["password"] == "app_pass_123"

    def test_reads_optional_env_vars_with_defaults(self):
        with patch.dict(os.environ, {
            "QQ_MAIL_USER": "u@q.com",
            "QQ_MAIL_APP_PASSWORD": "p",
        }):
            config = get_config()
        assert config["imap_host"] == "imap.qq.com"
        assert config["imap_port"] == 993
        assert config["smtp_host"] == "smtp.qq.com"
        assert config["smtp_port"] == 465
        assert config["archive_folder"] == "Archives"

    def test_custom_host_and_port(self):
        with patch.dict(os.environ, {
            "QQ_MAIL_USER": "u@q.com",
            "QQ_MAIL_APP_PASSWORD": "p",
            "QQ_MAIL_IMAP_HOST": "custom.imap.com",
            "QQ_MAIL_IMAP_PORT": "143",
            "QQ_MAIL_SMTP_HOST": "custom.smtp.com",
            "QQ_MAIL_SMTP_PORT": "587",
            "QQ_MAIL_ARCHIVE_FOLDER": "MyArchive",
        }):
            config = get_config()
        assert config["imap_host"] == "custom.imap.com"
        assert config["imap_port"] == 143
        assert config["smtp_host"] == "custom.smtp.com"
        assert config["smtp_port"] == 587
        assert config["archive_folder"] == "MyArchive"

    def test_exits_on_missing_user(self):
        with patch("email_cli._load_dotenv"):
            with patch.dict(os.environ, {"QQ_MAIL_APP_PASSWORD": "p"}, clear=True):
                with pytest.raises(SystemExit) as exc:
                    get_config()
                assert exc.value.code == 1

    def test_exits_on_missing_password(self):
        with patch("email_cli._load_dotenv"):
            with patch.dict(os.environ, {"QQ_MAIL_USER": "u@q.com"}, clear=True):
                with pytest.raises(SystemExit) as exc:
                    get_config()
                assert exc.value.code == 1


class TestDecodeMime:
    def test_plain_ascii(self):
        assert decode_mime("Hello World") == "Hello World"

    def test_empty_string(self):
        assert decode_mime("") == ""
        assert decode_mime(None) == ""

    def test_encoded_utf8(self):
        # base64 of "学习" is 5a2m5Lmg
        assert decode_mime("=?utf-8?b?5a2m5Lmg?=") == "学习"

    def test_mixed_encoded_and_plain(self):
        result = decode_mime("=?utf-8?b?5a2m5Lmg?= Report")
        assert "学习" in result
        assert "Report" in result
