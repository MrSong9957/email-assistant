import os
from unittest.mock import patch


def make_config(**overrides):
    """Create a test config with sensible defaults."""
    base = {
        "account": "qq",
        "user": "test@qq.com",
        "password": "testpass",
        "imap_host": "imap.qq.com",
        "imap_port": 993,
        "smtp_host": "smtp.qq.com",
        "smtp_port": 465,
        "archive_folder": "Archives",
        "sent_folder": "Sent Messages",
    }
    base.update(overrides)
    return base
