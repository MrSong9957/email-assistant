import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from email_cli import build_web_link, format_email, format_emails


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

    def test_sent_mode_shows_to(self):
        msg = _make_email()
        msg["To"] = "bob@example.com"
        result = format_email(1, "100", msg, sent=True)
        assert "To:" in result
        assert "bob@example.com" in result
        assert "From:" not in result

    def test_sent_mode_default_shows_from(self):
        msg = _make_email()
        result = format_email(1, "100", msg, sent=False)
        assert "From:" in result
        assert "To:" not in result


class TestFormatEmailsSentMode:
    def test_sent_header(self):
        msg = EmailMessage()
        msg["From"] = "me@qq.com"
        msg["To"] = "bob@example.com"
        msg["Subject"] = "Hello"
        msg["Date"] = "Fri, 09 May 2026 14:30:00 +0800"
        msg.set_content("body")

        result = format_emails([("100", msg)], sent=True)
        assert "已发送邮件 (1封)" in result
        assert "To:" in result

    def test_default_header_is_inbox(self):
        msg = EmailMessage()
        msg["From"] = "a@b.com"
        msg["Subject"] = "X"
        msg["Date"] = "Fri, 09 May 2026 14:30:00 +0800"
        msg.set_content("body")

        result = format_emails([("1", msg)], sent=False)
        assert "未读邮件" in result


class TestBuildWebLink:
    def test_gmail_with_message_id(self):
        msg = _make_email()
        msg["Message-ID"] = "<abc123@gmail.com>"
        config = {"account": "gmail", "user": "test@gmail.com"}
        link = build_web_link(config, msg)
        assert link == "https://mail.google.com/"

    def test_gmail_without_message_id(self):
        msg = _make_email()
        config = {"account": "gmail", "user": "test@gmail.com"}
        link = build_web_link(config, msg)
        assert link == "https://mail.google.com/"

    def test_qq_mail(self):
        msg = _make_email()
        msg["Message-ID"] = "<xyz@qq.com>"
        config = {"account": "qq", "user": "test@qq.com"}
        link = build_web_link(config, msg)
        assert link == "https://mail.qq.com/"

    def test_unknown_provider(self):
        msg = _make_email()
        config = {"account": "outlook", "user": "test@outlook.com"}
        link = build_web_link(config, msg)
        assert link is None


class TestFormatEmailLink:
    def test_link_with_config(self):
        msg = _make_email()
        msg["Message-ID"] = "<abc@gmail.com>"
        config = {"account": "gmail", "user": "test@gmail.com"}
        result = format_email(1, "100", msg, config=config)
        assert "**Link:**" in result
        assert "mail.google.com" in result

    def test_no_link_without_config(self):
        msg = _make_email()
        result = format_email(1, "100", msg)
        assert "**Link:**" not in result

    def test_no_link_for_unknown_provider(self):
        msg = _make_email()
        config = {"account": "outlook", "user": "test@outlook.com"}
        result = format_email(1, "100", msg, config=config)
        assert "**Link:**" not in result
