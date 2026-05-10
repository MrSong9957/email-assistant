import os
import sys
from unittest.mock import AsyncMock, patch
from email.message import EmailMessage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from conftest import make_config
from email_cli import send_email, get_email_headers, cmd_forward
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytest


class TestSendEmail:
    @pytest.mark.asyncio
    async def test_sends_plain_email(self):
        with patch("email_cli.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await send_email(
                make_config(),
                to="bob@example.com",
                subject="Hello",
                body="World",
            )

        mock_send.assert_called_once()
        msg = mock_send.call_args[0][0]
        assert msg["To"] == "bob@example.com"
        assert msg["Subject"] == "Hello"
        assert msg["From"] == "test@qq.com"

    @pytest.mark.asyncio
    async def test_reply_headers(self):
        with patch("email_cli.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await send_email(
                make_config(),
                to="bob@example.com",
                subject="Re: Hello",
                body="Reply",
                in_reply_to="<msg123@test.com>",
                references="<msg123@test.com>",
            )

        msg = mock_send.call_args[0][0]
        assert msg["In-Reply-To"] == "<msg123@test.com>"
        assert msg["References"] == "<msg123@test.com>"

    @pytest.mark.asyncio
    async def test_sends_html_email(self):
        with patch("email_cli.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await send_email(
                make_config(),
                to="bob@example.com",
                subject="HTML Test",
                body="plain fallback",
                html_body="<b>bold</b>",
            )

        mock_send.assert_called_once()
        msg = mock_send.call_args[0][0]
        assert msg.get_content_type() == "multipart/alternative"

    @pytest.mark.asyncio
    async def test_html_email_contains_both_parts(self):
        with patch("email_cli.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await send_email(
                make_config(),
                to="bob@example.com",
                subject="Both",
                body="plain text",
                html_body="<p>html</p>",
            )

        msg = mock_send.call_args[0][0]
        parts = list(msg.walk())
        payload_parts = [p for p in parts if p.get_content_type() in ("text/plain", "text/html")]
        types = {p.get_content_type() for p in payload_parts}
        assert "text/plain" in types
        assert "text/html" in types

    @pytest.mark.asyncio
    async def test_no_html_body_keeps_plain_only(self):
        with patch("email_cli.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await send_email(
                make_config(),
                to="bob@example.com",
                subject="Plain",
                body="just text",
            )

        msg = mock_send.call_args[0][0]
        assert msg.get_content_type() == "text/plain"

    @pytest.mark.asyncio
    async def test_smtp_failure_exits_4(self):
        with patch("email_cli.aiosmtplib.send", new_callable=AsyncMock, side_effect=Exception("Connection refused")):
            with pytest.raises(SystemExit) as exc:
                await send_email(
                    make_config(),
                    to="bob@example.com",
                    subject="X",
                    body="Y",
                )
            assert exc.value.code == 4


class TestGetEmailHeaders:
    @pytest.mark.asyncio
    async def test_fetches_message_id(self):
        msg = EmailMessage()
        msg["Message-ID"] = "<mid123@test.com>"
        msg["References"] = "<ref1@test.com>"
        raw = msg.as_bytes()

        mock_client = AsyncMock()
        mock_client.wait_hello_from_server = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.select = AsyncMock()
        mock_client.uid = AsyncMock(return_value=(
            "OK", [b"1 (UID 100)", raw, b")"]
        ))
        mock_client.logout = AsyncMock()

        with patch("email_cli.aioimaplib.IMAP4_SSL", return_value=mock_client):
            mid, refs = await get_email_headers(make_config(), "100")

        mock_client.uid.assert_called_with("fetch", "100", "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID REFERENCES FROM SUBJECT)])")
        assert mid == "<mid123@test.com>"
        assert refs == "<ref1@test.com>"

    @pytest.mark.asyncio
    async def test_uid_not_found_exits_3(self):
        mock_client = AsyncMock()
        mock_client.wait_hello_from_server = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.select = AsyncMock()
        mock_client.uid = AsyncMock(return_value=("OK", []))
        mock_client.logout = AsyncMock()

        with patch("email_cli.aioimaplib.IMAP4_SSL", return_value=mock_client):
            with pytest.raises(SystemExit) as exc:
                await get_email_headers(make_config(), "99999")
            assert exc.value.code == 3


class TestCmdForward:
    def _make_html_orig(self):
        """Create a multipart HTML email to forward."""
        msg = MIMEMultipart("alternative")
        msg["From"] = "alice@test.com"
        msg["Subject"] = "Report"
        msg["Date"] = "Fri, 09 May 2026 14:30:00 +0800"
        msg.attach(MIMEText("plain body", "plain", "utf-8"))
        msg.attach(MIMEText("<b>bold</b>", "html", "utf-8"))
        return msg

    def test_forward_passes_html_body(self):
        orig = self._make_html_orig()
        with patch("email_cli.get_email_full", AsyncMock(return_value=orig)), \
             patch("email_cli.send_email", AsyncMock()) as mock_send_fn, \
             patch("email_cli.get_config", return_value=make_config()):
            import argparse
            args = argparse.Namespace(uid="100", to="charlie@test.com", note="")
            cmd_forward(args)

        call_kwargs = mock_send_fn.call_args
        assert call_kwargs[1].get("html_body") or (len(call_kwargs[0]) > 4 and call_kwargs[0][4])

    def test_forward_plain_only_no_html(self):
        """Forwarding plain-only email should not pass html_body."""
        msg = EmailMessage()
        msg["From"] = "alice@test.com"
        msg["Subject"] = "Plain"
        msg["Date"] = "Fri, 09 May 2026 14:30:00 +0800"
        msg.set_content("just text")

        with patch("email_cli.get_email_full", AsyncMock(return_value=msg)), \
             patch("email_cli.send_email", AsyncMock()) as mock_send_fn, \
             patch("email_cli.get_config", return_value=make_config()):
            import argparse
            args = argparse.Namespace(uid="100", to="charlie@test.com", note="")
            cmd_forward(args)

        call_kwargs = mock_send_fn.call_args
        html_val = call_kwargs[1].get("html_body") if call_kwargs[1] else None
        assert html_val is None or html_val == ""
