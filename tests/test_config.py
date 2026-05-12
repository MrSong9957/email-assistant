import os
import sys
import pytest
from unittest.mock import patch

# Ensure email_cli is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# Ensure conftest helpers are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from conftest import make_config
from email_cli import get_config, list_accounts, decode_mime


class TestListAccounts:
    def test_reads_mail_accounts_env(self):
        with patch("email_cli._load_dotenv"):
            with patch.dict(os.environ, {
                "MAIL_ACCOUNTS": "qq,gmail",
                "QQ_MAIL_USER": "u@qq.com",
                "GMAIL_USER": "u@gmail.com",
            }, clear=True):
                accounts = list_accounts()
        assert len(accounts) == 2
        assert accounts[0] == {"name": "qq", "user": "u@qq.com"}
        assert accounts[1] == {"name": "gmail", "user": "u@gmail.com"}

    def test_backward_compat_no_mail_accounts(self):
        with patch("email_cli._load_dotenv"):
            with patch.dict(os.environ, {
                "QQ_MAIL_USER": "u@qq.com",
            }, clear=True):
                accounts = list_accounts()
        assert accounts == [{"name": "qq", "user": "u@qq.com"}]

    def test_empty_when_nothing_configured(self):
        with patch("email_cli._load_dotenv"):
            with patch.dict(os.environ, {}, clear=True):
                accounts = list_accounts()
        assert accounts == []

    def test_skips_unknown_provider(self):
        with patch("email_cli._load_dotenv"):
            with patch.dict(os.environ, {
                "MAIL_ACCOUNTS": "qq,unknown,gmail",
                "QQ_MAIL_USER": "u@qq.com",
                "GMAIL_USER": "u@gmail.com",
            }, clear=True):
                accounts = list_accounts()
        assert len(accounts) == 2
        assert [a["name"] for a in accounts] == ["qq", "gmail"]

    def test_skips_account_without_user(self):
        with patch("email_cli._load_dotenv"):
            with patch.dict(os.environ, {
                "MAIL_ACCOUNTS": "qq,gmail",
                "QQ_MAIL_USER": "u@qq.com",
            }, clear=True):
                accounts = list_accounts()
        assert [a["name"] for a in accounts] == ["qq"]


class TestGetConfigAccount:
    def test_default_account_first(self):
        with patch("email_cli._load_dotenv"):
            with patch.dict(os.environ, {
                "MAIL_ACCOUNTS": "qq,gmail",
                "QQ_MAIL_USER": "u@qq.com",
                "QQ_MAIL_APP_PASSWORD": "p1",
                "GMAIL_USER": "u@gmail.com",
                "GMAIL_APP_PASSWORD": "p2",
            }, clear=True):
                config = get_config()
        assert config["account"] == "qq"
        assert config["user"] == "u@qq.com"

    def test_explicit_account(self):
        with patch("email_cli._load_dotenv"):
            with patch.dict(os.environ, {
                "MAIL_ACCOUNTS": "qq,gmail",
                "QQ_MAIL_USER": "u@qq.com",
                "QQ_MAIL_APP_PASSWORD": "p1",
                "GMAIL_USER": "u@gmail.com",
                "GMAIL_APP_PASSWORD": "p2",
            }, clear=True):
                config = get_config("gmail")
        assert config["account"] == "gmail"
        assert config["user"] == "u@gmail.com"
        assert config["imap_host"] == "imap.gmail.com"
        assert config["smtp_host"] == "smtp.gmail.com"

    def test_account_not_found_exits(self):
        with patch("email_cli._load_dotenv"):
            with patch.dict(os.environ, {
                "MAIL_ACCOUNTS": "qq",
                "QQ_MAIL_USER": "u@qq.com",
                "QQ_MAIL_APP_PASSWORD": "p",
            }, clear=True):
                with pytest.raises(SystemExit) as exc:
                    get_config("gmail")
                assert exc.value.code == 1


class TestGetConfig:
    def test_reads_required_env_vars(self):
        with patch("email_cli._load_dotenv"):
            with patch.dict(os.environ, {
                "MAIL_ACCOUNTS": "qq",
                "QQ_MAIL_USER": "user@qq.com",
                "QQ_MAIL_APP_PASSWORD": "app_pass_123",
            }, clear=True):
                config = get_config()
        assert config["user"] == "user@qq.com"
        assert config["password"] == "app_pass_123"
        assert config["account"] == "qq"

    def test_reads_optional_env_vars_with_defaults(self):
        with patch("email_cli._load_dotenv"):
            with patch.dict(os.environ, {
                "MAIL_ACCOUNTS": "qq",
                "QQ_MAIL_USER": "u@q.com",
                "QQ_MAIL_APP_PASSWORD": "p",
            }, clear=True):
                config = get_config()
        assert config["imap_host"] == "imap.qq.com"
        assert config["imap_port"] == 993
        assert config["smtp_host"] == "smtp.qq.com"
        assert config["smtp_port"] == 465
        assert config["archive_folder"] == "Archives"

    def test_custom_host_and_port(self):
        with patch("email_cli._load_dotenv"):
            with patch.dict(os.environ, {
                "MAIL_ACCOUNTS": "qq",
                "QQ_MAIL_USER": "u@q.com",
                "QQ_MAIL_APP_PASSWORD": "p",
                "QQ_MAIL_IMAP_HOST": "custom.imap.com",
                "QQ_MAIL_IMAP_PORT": "143",
                "QQ_MAIL_SMTP_HOST": "custom.smtp.com",
                "QQ_MAIL_SMTP_PORT": "587",
                "QQ_MAIL_ARCHIVE_FOLDER": "MyArchive",
            }, clear=True):
                config = get_config()
        assert config["imap_host"] == "custom.imap.com"
        assert config["imap_port"] == 143
        assert config["smtp_host"] == "custom.smtp.com"
        assert config["smtp_port"] == 587
        assert config["archive_folder"] == "MyArchive"

    def test_exits_on_missing_user(self):
        with patch("email_cli._load_dotenv"):
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(SystemExit) as exc:
                    get_config()
                assert exc.value.code == 1

    def test_exits_on_missing_password(self):
        with patch("email_cli._load_dotenv"):
            with patch.dict(os.environ, {
                "MAIL_ACCOUNTS": "qq",
                "QQ_MAIL_USER": "u@q.com",
            }, clear=True):
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
