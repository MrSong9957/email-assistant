import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from email_cli import format_email


def _make_email(subject="Test", from_addr="Alice <alice@example.com>",
                date="Fri, 09 May 2026 14:30:00 +0800", body="Hello world"):
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["Subject"] = subject
    msg["Date"] = date
    msg.set_content(body)
    return msg


class TestFormatEmail:
    def test_basic_fields(self):
        msg = _make_email()
        result = format_email(1, "12345", msg)
        assert "UID: 12345" in result
        assert "alice@example.com" in result
        assert "Test" in result
        assert "Hello world" in result

    def test_index_number(self):
        msg = _make_email()
        result = format_email(3, "99999", msg)
        assert "[3]" in result

    def test_no_subject(self):
        msg = EmailMessage()
        msg["From"] = "bob@test.com"
        msg["Date"] = "Fri, 09 May 2026 14:30:00 +0800"
        msg.set_content("body")
        result = format_email(1, "1", msg)
        assert "No Subject" in result

    def test_encoded_subject(self):
        msg = _make_email(subject="=?utf-8?b?5a2m5Lmg?=")
        result = format_email(1, "1", msg)
        assert "学习" in result

    def test_attachment_info(self):
        msg = MIMEMultipart()
        msg["From"] = "a@b.com"
        msg["Subject"] = "Sub"
        msg["Date"] = "Fri, 09 May 2026 14:30:00 +0800"
        msg.attach(MIMEText("body"))

        attachment = MIMEBase("application", "pdf")
        payload = b"x" * 2048
        attachment.set_payload(payload)
        encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition", "attachment", filename="report.pdf")
        msg.attach(attachment)

        result = format_email(1, "1", msg)
        assert "report.pdf" in result
        assert "KB" in result

    def test_no_attachments(self):
        msg = _make_email()
        result = format_email(1, "1", msg)
        assert "Attachments" not in result
