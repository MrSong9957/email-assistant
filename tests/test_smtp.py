import os
import sys
from unittest.mock import AsyncMock, patch
from email.message import EmailMessage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from conftest import make_config
from email_cli import send_email, get_email_headers

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
