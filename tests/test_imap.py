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


class TestFilterEmails:
    def _make_email_data(self, subject="Test", from_addr="alice@test.com",
                         date="Fri, 09 May 2026 14:30:00 +0800"):
        msg = EmailMessage()
        msg["From"] = from_addr
        msg["Subject"] = subject
        msg["Date"] = date
        msg.set_content("body")
        return ("100", msg)

    def test_no_filters_returns_all(self):
        from email_cli import filter_emails
        emails = [self._make_email_data(), self._make_email_data()]
        result = filter_emails(emails)
        assert len(result) == 2

    def test_since_date(self):
        from email_cli import filter_emails
        emails = [
            self._make_email_data(date="Thu, 01 May 2026 10:00:00 +0800"),
            self._make_email_data(date="Fri, 09 May 2026 14:30:00 +0800"),
        ]
        result = filter_emails(emails, since="2026-05-08")
        assert len(result) == 1

    def test_before_date(self):
        from email_cli import filter_emails
        emails = [
            self._make_email_data(date="Thu, 01 May 2026 10:00:00 +0800"),
            self._make_email_data(date="Fri, 09 May 2026 14:30:00 +0800"),
        ]
        result = filter_emails(emails, before="2026-05-09")
        assert len(result) == 1

    def test_from_filter_case_insensitive(self):
        from email_cli import filter_emails
        emails = [
            self._make_email_data(from_addr="Zhang San <zhangsan@qq.com>"),
            self._make_email_data(from_addr="Li Si <lisi@qq.com>"),
        ]
        result = filter_emails(emails, from_addr="zhang")
        assert len(result) == 1

    def test_subject_filter_substring(self):
        from email_cli import filter_emails
        emails = [
            self._make_email_data(subject="周报提醒"),
            self._make_email_data(subject="会议通知"),
        ]
        result = filter_emails(emails, subject="周报")
        assert len(result) == 1

    def test_combined_filters(self):
        from email_cli import filter_emails
        emails = [
            self._make_email_data(subject="报告", from_addr="boss@co.com",
                                  date="Mon, 05 May 2026 10:00:00 +0800"),
            self._make_email_data(subject="报告", from_addr="hr@co.com",
                                  date="Thu, 08 May 2026 10:00:00 +0800"),
            self._make_email_data(subject="闲聊", from_addr="boss@co.com",
                                  date="Fri, 09 May 2026 10:00:00 +0800"),
        ]
        result = filter_emails(emails, since="2026-05-06", from_addr="boss", subject="报告")
        assert len(result) == 0

        result2 = filter_emails(emails, since="2026-05-04", from_addr="boss", subject="报告")
        assert len(result2) == 1


class TestFormatEmails:
    def test_formats_list_with_reindexed_headers(self):
        from email_cli import format_emails
        msg1 = EmailMessage()
        msg1["From"] = "a@b.com"
        msg1["Subject"] = "Hello"
        msg1["Date"] = "Fri, 09 May 2026 14:30:00 +0800"
        msg1.set_content("body")
        msg2 = EmailMessage()
        msg2["From"] = "c@d.com"
        msg2["Subject"] = "World"
        msg2["Date"] = "Fri, 09 May 2026 15:00:00 +0800"
        msg2.set_content("body2")

        result = format_emails([("100", msg1), ("200", msg2)])
        assert "未读邮件 (2封)" in result
        assert "[1]" in result
        assert "[2]" in result
        assert "UID: 100" in result
        assert "UID: 200" in result
        assert "Hello" in result
        assert "World" in result

    def test_empty_list(self):
        from email_cli import format_emails
        result = format_emails([])
        assert "0封" in result
