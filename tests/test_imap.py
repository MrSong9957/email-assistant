import asyncio
import os
import sys
from email.message import EmailMessage
from unittest.mock import AsyncMock, patch, MagicMock, call

# Ensure email_cli is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# Ensure conftest helpers are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from conftest import make_config
from email_cli import fetch_emails, list_folders, archive_uids, mark_read_uids

import pytest


def _make_raw_email(subject="Test", from_addr="alice@test.com", body="Hello"):
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["Subject"] = subject
    msg["Date"] = "Fri, 09 May 2026 14:30:00 +0800"
    msg.set_content(body)
    return msg.as_bytes()


class TestFetchEmails:
    @pytest.mark.asyncio
    async def test_returns_list_of_emails(self):
        raw1 = _make_raw_email(subject="Sub1", body="Body1")
        raw2 = _make_raw_email(subject="Sub2", body="Body2")

        mock_client = AsyncMock()
        mock_client.wait_hello_from_server = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.select = AsyncMock()
        mock_client.search = AsyncMock(return_value=("OK", [b"100 200"]))
        mock_client.fetch = AsyncMock(side_effect=[
            ("OK", [b"1 (UID 100)", raw1]),
            ("OK", [b"2 (UID 200)", raw2]),
        ])
        mock_client.logout = AsyncMock()

        with patch("email_cli.aioimaplib.IMAP4_SSL", return_value=mock_client):
            result = await fetch_emails(make_config(), limit=10)

        assert len(result) == 2
        uid1, msg1 = result[0]
        uid2, msg2 = result[1]
        assert uid1 == "100"
        assert uid2 == "200"
        assert "Sub1" in msg1["Subject"]
        assert "Sub2" in msg2["Subject"]

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_unseen(self):
        mock_client = AsyncMock()
        mock_client.wait_hello_from_server = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.select = AsyncMock()
        mock_client.search = AsyncMock(return_value=("OK", [b""]))
        mock_client.logout = AsyncMock()

        with patch("email_cli.aioimaplib.IMAP4_SSL", return_value=mock_client):
            result = await fetch_emails(make_config())

        assert result == []

    @pytest.mark.asyncio
    async def test_respects_limit(self):
        raws = [_make_raw_email(subject=f"S{i}") for i in range(5)]
        mock_client = AsyncMock()
        mock_client.wait_hello_from_server = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.select = AsyncMock()
        mock_client.search = AsyncMock(return_value=("OK", [b"1 2 3 4 5"]))
        mock_client.fetch = AsyncMock(side_effect=[
            ("OK", [b"3 (UID 3)", raws[2]]),
            ("OK", [b"4 (UID 4)", raws[3]]),
            ("OK", [b"5 (UID 5)", raws[4]]),
        ])
        mock_client.logout = AsyncMock()

        with patch("email_cli.aioimaplib.IMAP4_SSL", return_value=mock_client):
            result = await fetch_emails(make_config(), limit=3)

        assert len(result) == 3


class TestListFolders:
    @pytest.mark.asyncio
    async def test_lists_folders(self):
        mock_client = AsyncMock()
        mock_client.wait_hello_from_server = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.list = AsyncMock(return_value=(
            "OK", [b'(\\HasNoChildren) "/" "INBOX"', b'(\\HasNoChildren) "/" "Sent"']
        ))
        mock_client.logout = AsyncMock()

        with patch("email_cli.aioimaplib.IMAP4_SSL", return_value=mock_client):
            result = await list_folders(make_config())

        assert "INBOX" in result
        assert "Sent" in result


class TestArchiveUids:
    @pytest.mark.asyncio
    async def test_moves_to_archive(self):
        mock_client = AsyncMock()
        mock_client.wait_hello_from_server = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.select = AsyncMock()
        mock_client.uid = AsyncMock(return_value=("OK", [b"OK"]))
        mock_client.expunge = AsyncMock()
        mock_client.logout = AsyncMock()

        with patch("email_cli.aioimaplib.IMAP4_SSL", return_value=mock_client):
            await archive_uids(make_config(), ["100", "200"])

        assert mock_client.uid.call_count == 2

    @pytest.mark.asyncio
    async def test_fallback_to_copy_delete(self):
        mock_client = AsyncMock()
        mock_client.wait_hello_from_server = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.select = AsyncMock()
        call_count = 0
        async def uid_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and args[0] == "move":
                raise Exception("MOVE not supported")
            return ("OK", [b"OK"])
        mock_client.uid = AsyncMock(side_effect=uid_side_effect)
        mock_client.expunge = AsyncMock()
        mock_client.logout = AsyncMock()

        with patch("email_cli.aioimaplib.IMAP4_SSL", return_value=mock_client):
            await archive_uids(make_config(), ["100"])

        assert call_count == 3  # move(fail) + copy + store


class TestMarkReadUids:
    @pytest.mark.asyncio
    async def test_marks_seen_flag(self):
        mock_client = AsyncMock()
        mock_client.wait_hello_from_server = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.select = AsyncMock()
        mock_client.uid = AsyncMock(return_value=("OK", [b"OK"]))
        mock_client.logout = AsyncMock()

        with patch("email_cli.aioimaplib.IMAP4_SSL", return_value=mock_client):
            await mark_read_uids(make_config(), ["100"])

        mock_client.uid.assert_called_once_with("store", "100", "+FLAGS", "\\Seen")

    @pytest.mark.asyncio
    async def test_multiple_uids(self):
        mock_client = AsyncMock()
        mock_client.wait_hello_from_server = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.select = AsyncMock()
        mock_client.uid = AsyncMock(return_value=("OK", [b"OK"]))
        mock_client.logout = AsyncMock()

        with patch("email_cli.aioimaplib.IMAP4_SSL", return_value=mock_client):
            await mark_read_uids(make_config(), ["100", "200", "300"])

        assert mock_client.uid.call_count == 3
        calls = mock_client.uid.call_args_list
        assert calls[0] == call("store", "100", "+FLAGS", "\\Seen")
        assert calls[1] == call("store", "200", "+FLAGS", "\\Seen")
        assert calls[2] == call("store", "300", "+FLAGS", "\\Seen")
