# Email Assistant 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 QQ 邮箱 CLI 工具 + Claude Code Skill，实现邮件拉取、摘要展示、回复、转发、归档功能。

**Architecture:** Python CLI (`email_cli.py`) 通过 asyncio IMAP/SMTP 操作邮件，输出 Markdown 到 stdout。SKILL.md 指导 AI 编程工具如何调用 CLI 并向用户展示。Python 是无状态管道，AI 是有状态大脑。

**Tech Stack:** Python 3.11+, aioimaplib, aiosmtplib, argparse, pytest, pytest-asyncio

**Spec:** `docs/superpowers/specs/2026-05-09-email-assistant-design.md`

---

## File Structure

```
~/.claude/skills/email-assistant/
├── SKILL.md                    # Skill 定义（AI 编程工具读取）
├── email_cli.py                # Python CLI 工具（单文件）
├── requirements.txt            # Python 依赖
└── tests/
    ├── __init__.py
    ├── conftest.py             # 共享 fixtures
    ├── test_config.py          # Config + MIME 解码测试
    ├── test_formatter.py       # Markdown 格式化测试
    ├── test_imap.py            # IMAP 操作测试（mock）
    └── test_smtp.py            # SMTP 操作测试（mock）
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `~/.claude/skills/email-assistant/requirements.txt`
- Create: `~/.claude/skills/email-assistant/tests/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p ~/.claude/skills/email-assistant/tests
```

- [ ] **Step 2: Create requirements.txt**

```txt
aioimaplib>=1.0.0
aiosmtplib>=3.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

- [ ] **Step 3: Install dependencies**

```bash
pip install -r ~/.claude/skills/email-assistant/requirements.txt
```

- [ ] **Step 4: Verify installation**

```bash
python -c "import aioimaplib; import aiosmtplib; print('OK')"
python -c "import pytest; print(pytest.__version__)"
```

Expected: Both commands print without error.

- [ ] **Step 5: Create tests/__init__.py**

```python
```

(empty file)

- [ ] **Step 6: Commit**

```bash
cd ~/.claude/skills/email-assistant
git add -A && git commit -m "chore: scaffold email-assistant skill"
```

---

### Task 2: Config Module + MIME Decoder — TDD

**Files:**
- Create: `~/.claude/skills/email-assistant/email_cli.py`
- Create: `~/.claude/skills/email-assistant/tests/conftest.py`
- Create: `~/.claude/skills/email-assistant/tests/test_config.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/conftest.py
import os
from unittest.mock import patch


def make_config(**overrides):
    """Create a test config with sensible defaults."""
    base = {
        "user": "test@qq.com",
        "password": "testpass",
        "imap_host": "imap.qq.com",
        "imap_port": 993,
        "smtp_host": "smtp.qq.com",
        "smtp_port": 465,
        "archive_folder": "Archives",
    }
    base.update(overrides)
    return base
```

```python
# tests/test_config.py
import os
import pytest
from unittest.mock import patch
from conftest import make_config
import sys
sys.path.insert(0, os.path.expanduser("~/.claude/skills/email-assistant"))
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
        with patch.dict(os.environ, {"QQ_MAIL_APP_PASSWORD": "p"}, clear=True):
            with pytest.raises(SystemExit) as exc:
                get_config()
            assert exc.value.code == 1

    def test_exits_on_missing_password(self):
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
        # =?utf-8?b?5p2l5L+h?=
        assert decode_mime("=?utf-8?b?5p2l5L+h?=") == "学习"

    def test_mixed_encoded_and_plain(self):
        result = decode_mime("=?utf-8?b?5p2l5L+h?= Report")
        assert "学习" in result
        assert "Report" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/.claude/skills/email-assistant
python -m pytest tests/test_config.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'email_cli'`

- [ ] **Step 3: Write minimal implementation**

```python
# email_cli.py
"""QQ Mail CLI for Claude Code email-assistant skill."""

import argparse
import asyncio
import email as email_lib
import os
import re
import sys
from contextlib import asynccontextmanager
from email.header import decode_header
from email.mime.text import MIMEText

import aioimaplib
import aiosmtplib


# ── Config ──────────────────────────────────────

def get_config():
    """Read email configuration from environment variables."""
    user = os.environ.get("QQ_MAIL_USER", "")
    password = os.environ.get("QQ_MAIL_APP_PASSWORD", "")
    if not user or not password:
        print(
            "Error: QQ_MAIL_USER and QQ_MAIL_APP_PASSWORD required.\n"
            "Get app password: QQ Mail → Settings → Account → IMAP/SMTP → Generate code",
            file=sys.stderr,
        )
        sys.exit(1)
    return {
        "user": user,
        "password": password,
        "imap_host": os.environ.get("QQ_MAIL_IMAP_HOST", "imap.qq.com"),
        "imap_port": int(os.environ.get("QQ_MAIL_IMAP_PORT", "993")),
        "smtp_host": os.environ.get("QQ_MAIL_SMTP_HOST", "smtp.qq.com"),
        "smtp_port": int(os.environ.get("QQ_MAIL_SMTP_PORT", "465")),
        "archive_folder": os.environ.get("QQ_MAIL_ARCHIVE_FOLDER", "Archives"),
    }


def decode_mime(value):
    """Decode MIME-encoded header value to readable string."""
    if not value:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ~/.claude/skills/email-assistant
python -m pytest tests/test_config.py -v
```

Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/email-assistant
git add email_cli.py tests/ && git commit -m "feat: add config module and MIME decoder"
```

---

### Task 3: Email Body Extraction (User Contribution)

This is a design choice that shapes the user experience — how the terminal renders email content. The function decides: prefer plain text or HTML? How to handle charset? How to handle nested multipart?

I'll set up the surrounding code; you write the core extraction logic (5-10 lines).

**Files:**
- Modify: `~/.claude/skills/email-assistant/email_cli.py`

- [ ] **Step 1: Add function signatures to email_cli.py**

Add the following after `decode_mime()`:

```python
def strip_html(text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    import html as html_mod
    return html_mod.unescape(text).strip()


def extract_body(msg):
    """Extract readable text from an email message.

    TODO: Implement body extraction logic.

    Args:
        msg: email.message.Message object

    Returns:
        str: Readable text content of the email

    Consider:
    - text/plain → return as-is
    - text/html → strip tags via strip_html()
    - multipart/alternative → prefer text/plain, fallback to text/html
    - multipart/mixed → iterate parts, collect text
    - Nested multipart → recurse
    - Charset decoding → part.get_payload(decode=True) handles this
    """
    pass
```

- [ ] **Step 2: User implements extract_body()**

Guidance:
- `msg.get_content_type()` returns MIME type (e.g., `'text/plain'`, `'multipart/alternative'`)
- `msg.is_multipart()` returns True for multipart messages
- `msg.walk()` iterates all parts (depth-first), skipping the container
- `msg.get_payload(decode=True)` returns decoded bytes for leaf parts
- `msg.get_content_charset()` returns charset or None

Trade-offs:
- **Prefer text/plain**: Clean terminal display, but some HTML emails have no plain text part
- **Always show HTML-stripped**: More consistent, but tag stripping is lossy
- Recommended: prefer text/plain, fallback to stripped HTML

Write 5-10 lines at `~/.claude/skills/email-assistant/email_cli.py` in the `extract_body()` function.

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills/email-assistant
git add email_cli.py && git commit -m "feat: add email body extraction logic"
```

---

### Task 4: Markdown Formatter — TDD

**Files:**
- Modify: `~/.claude/skills/email-assistant/email_cli.py`
- Create: `~/.claude/skills/email-assistant/tests/test_formatter.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_formatter.py
import os
import sys
sys.path.insert(0, os.path.expanduser("~/.claude/skills/email-assistant"))
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
        msg = _make_email(subject="=?utf-8?b?5p2l5L+h?=")
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/.claude/skills/email-assistant
python -m pytest tests/test_formatter.py -v
```

Expected: FAIL — `ImportError: cannot import name 'format_email'`

- [ ] **Step 3: Write implementation**

Add to `email_cli.py` after `extract_body()`:

```python
def format_email(index, uid, msg):
    """Format a single email as Markdown."""
    from_addr = decode_mime(msg.get("From", "Unknown"))
    subject = decode_mime(msg.get("Subject", "(No Subject)"))
    date = msg.get("Date", "Unknown")

    lines = [
        f"## [{index}] UID: {uid} | {date}",
        f"**From:** {from_addr}",
        f"**Subject:** {subject}",
    ]

    attachments = []
    for part in msg.walk():
        cd = part.get("Content-Disposition", "")
        if "attachment" in cd:
            filename = decode_mime(part.get_filename() or "unnamed")
            payload = part.get_payload(decode=True)
            size = len(payload) if payload else 0
            if size >= 1024 * 1024:
                size_str = f"{size / 1024 / 1024:.1f}MB"
            elif size >= 1024:
                size_str = f"{size / 1024:.1f}KB"
            else:
                size_str = f"{size}B"
            attachments.append(f"{filename} ({size_str})")

    if attachments:
        lines.append(f"**Attachments:** {', '.join(attachments)}")

    lines.append("")
    body = extract_body(msg)
    lines.append(body if body else "(No readable content)")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests**

```bash
cd ~/.claude/skills/email-assistant
python -m pytest tests/test_formatter.py -v
```

Expected: All 6 tests PASS (assuming `extract_body()` is implemented; if it returns None, the "No readable content" fallback covers most tests except body content checks).

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/email-assistant
git add email_cli.py tests/test_formatter.py && git commit -m "feat: add Markdown formatter with attachment info"
```

---

### Task 5: IMAP Fetch — TDD

**Files:**
- Modify: `~/.claude/skills/email-assistant/email_cli.py`
- Create: `~/.claude/skills/email-assistant/tests/test_imap.py`

- [ ] **Step 1: Add IMAP context manager to email_cli.py**

Add after `get_config()`:

```python
@asynccontextmanager
async def imap_client(config):
    """Async context manager for IMAP connection."""
    client = aioimaplib.IMAP4_SSL(config["imap_host"], config["imap_port"])
    try:
        await client.wait_hello_from_server()
        await client.login(config["user"], config["password"])
        yield client
    except Exception as e:
        print(f"IMAP connection error: {e}", file=sys.stderr)
        sys.exit(2)
    finally:
        try:
            await client.logout()
        except Exception:
            pass
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_imap.py
import asyncio
import os
import sys
from email.message import EmailMessage
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.expanduser("~/.claude/skills/email-assistant"))
from conftest import make_config
from email_cli import fetch_emails, list_folders, archive_uids


def _make_raw_email(subject="Test", from_addr="alice@test.com", body="Hello"):
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["Subject"] = subject
    msg["Date"] = "Fri, 09 May 2026 14:30:00 +0800"
    msg.set_content(body)
    return msg.as_bytes()


class TestFetchEmails:
    @pytest.mark.asyncio
    async def test_returns_markdown_with_emails(self):
        raw1 = _make_raw_email(subject="Sub1", body="Body1")
        raw2 = _make_raw_email(subject="Sub2", body="Body2")

        mock_client = AsyncMock()
        mock_client.wait_hello_from_server = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.select = AsyncMock()
        mock_client.uid = AsyncMock(side_effect=[
            ("OK", [b"100 200"]),  # search
        ])
        mock_client.fetch = AsyncMock(side_effect=[
            ("OK", [(b"100 (RFC822 {size}", raw1), b")"]),
            ("OK", [(b"200 (RFC822 {size}", raw2), b")"]),
        ])
        mock_client.logout = AsyncMock()

        with patch("email_cli.aioimaplib.IMAP4_SSL", return_value=mock_client):
            result = await fetch_emails(make_config(), limit=10)

        assert "未读邮件" in result
        assert "Sub1" in result
        assert "Sub2" in result
        assert "UID: 100" in result
        assert "UID: 200" in result

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_unseen(self):
        mock_client = AsyncMock()
        mock_client.wait_hello_from_server = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.select = AsyncMock()
        mock_client.uid = AsyncMock(return_value=("OK", [b""]))
        mock_client.logout = AsyncMock()

        with patch("email_cli.aioimaplib.IMAP4_SSL", return_value=mock_client):
            result = await fetch_emails(make_config())

        assert "0封" in result

    @pytest.mark.asyncio
    async def test_respects_limit(self):
        raws = [_make_raw_email(subject=f"S{i}") for i in range(5)]
        mock_client = AsyncMock()
        mock_client.wait_hello_from_server = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.select = AsyncMock()
        mock_client.uid = AsyncMock(return_value=("OK", [b"1 2 3 4 5"]))
        mock_client.fetch = AsyncMock(side_effect=[
            ("OK", [(b"X", r), b")"]) for r in raws
        ])
        mock_client.logout = AsyncMock()

        with patch("email_cli.aioimaplib.IMAP4_SSL", return_value=mock_client):
            result = await fetch_emails(make_config(), limit=3)

        assert "3封" in result


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
        # First call (move) raises, forcing copy+delete fallback
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


import pytest
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd ~/.claude/skills/email-assistant
python -m pytest tests/test_imap.py -v
```

Expected: FAIL — `ImportError: cannot import name 'fetch_emails'`

- [ ] **Step 4: Write implementation**

Add to `email_cli.py` after `imap_client()`:

```python
async def fetch_emails(config, limit=10, folder="INBOX"):
    """Fetch unread emails and return as Markdown."""
    try:
        async with imap_client(config) as client:
            await client.select(folder)
            status, data = await client.uid("search", None, "UNSEEN")
            if status != "OK" or not data[0].strip():
                return "# 未读邮件 (0封)\n"

            uids = data[0].split()
            uids = uids[-limit:]

            results = []
            for i, uid_bytes in enumerate(uids, 1):
                uid_str = uid_bytes.decode()
                status, msg_data = await client.fetch(uid_str, "(RFC822)")
                if status != "OK":
                    continue
                raw_email = None
                for item in msg_data:
                    if isinstance(item, tuple):
                        raw_email = item[1]
                        break
                if raw_email is None:
                    continue
                msg = email_lib.message_from_bytes(raw_email)
                results.append(format_email(i, uid_str, msg))

            header = f"# 未读邮件 ({len(results)}封)\n\n"
            return header + "\n\n---\n\n".join(results)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error fetching emails: {e}", file=sys.stderr)
        sys.exit(2)


async def list_folders(config):
    """List available IMAP folders. Returns formatted string."""
    try:
        async with imap_client(config) as client:
            status, folders = await client.list()
            if status != "OK":
                return "Error listing folders"
            lines = []
            for folder in folders:
                if isinstance(folder, bytes):
                    lines.append(folder.decode(errors="replace"))
                else:
                    lines.append(str(folder))
            return "\n".join(lines)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error listing folders: {e}", file=sys.stderr)
        sys.exit(2)


async def archive_uids(config, uids):
    """Move emails to archive folder."""
    try:
        async with imap_client(config) as client:
            await client.select("INBOX")
            for uid in uids:
                try:
                    await client.uid("move", uid, config["archive_folder"])
                except Exception:
                    await client.uid("copy", uid, config["archive_folder"])
                    await client.uid("store", uid, "+FLAGS", "\\Deleted")
            await client.expunge()
            print(f"Archived {len(uids)} email(s)")
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error archiving: {e}", file=sys.stderr)
        sys.exit(2)
```

- [ ] **Step 5: Run tests**

```bash
cd ~/.claude/skills/email-assistant
python -m pytest tests/test_imap.py -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
cd ~/.claude/skills/email-assistant
git add email_cli.py tests/test_imap.py && git commit -m "feat: add IMAP fetch, list folders, archive"
```

---

### Task 6: SMTP Send — TDD

**Files:**
- Modify: `~/.claude/skills/email-assistant/email_cli.py`
- Create: `~/.claude/skills/email-assistant/tests/test_smtp.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_smtp.py
import os
import sys
from unittest.mock import AsyncMock, patch
from email.message import Message

sys.path.insert(0, os.path.expanduser("~/.claude/skills/email-assistant"))
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
        from email.message import EmailMessage
        msg = EmailMessage()
        msg["Message-ID"] = "<mid123@test.com>"
        msg["References"] = "<ref1@test.com>"
        raw = msg.as_bytes()

        mock_client = AsyncMock()
        mock_client.wait_hello_from_server = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.select = AsyncMock()
        mock_client.fetch = AsyncMock(return_value=(
            "OK", [(b"1 (RFC822 {size}", raw), b")"]
        ))
        mock_client.logout = AsyncMock()

        with patch("email_cli.aioimaplib.IMAP4_SSL", return_value=mock_client):
            mid, refs = await get_email_headers(make_config(), "100")

        assert mid == "<mid123@test.com>"
        assert refs == "<ref1@test.com>"

    @pytest.mark.asyncio
    async def test_uid_not_found_exits_3(self):
        mock_client = AsyncMock()
        mock_client.wait_hello_from_server = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.select = AsyncMock()
        mock_client.fetch = AsyncMock(return_value=("OK", []))
        mock_client.logout = AsyncMock()

        with patch("email_cli.aioimaplib.IMAP4_SSL", return_value=mock_client):
            with pytest.raises(SystemExit) as exc:
                await get_email_headers(make_config(), "99999")
            assert exc.value.code == 3
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/.claude/skills/email-assistant
python -m pytest tests/test_smtp.py -v
```

Expected: FAIL — `ImportError: cannot import name 'send_email'`

- [ ] **Step 3: Write implementation**

Add to `email_cli.py` after `archive_uids()`:

```python
async def get_email_headers(config, uid):
    """Fetch Message-ID and References for threading. Returns (message_id, references)."""
    try:
        async with imap_client(config) as client:
            await client.select("INBOX")
            status, msg_data = await client.fetch(uid, "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID REFERENCES FROM SUBJECT)])")
            if status != "OK":
                print(f"Email UID {uid} not found", file=sys.stderr)
                sys.exit(3)
            raw = None
            for item in msg_data:
                if isinstance(item, tuple):
                    raw = item[1]
                    break
            if raw is None:
                print(f"Email UID {uid} not found", file=sys.stderr)
                sys.exit(3)
            msg = email_lib.message_from_bytes(raw)
            return msg.get("Message-ID"), msg.get("References")
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error fetching email headers: {e}", file=sys.stderr)
        sys.exit(2)


async def get_email_full(config, uid):
    """Fetch full email by UID. Returns email.message.Message or exits."""
    try:
        async with imap_client(config) as client:
            await client.select("INBOX")
            status, msg_data = await client.fetch(uid, "(RFC822)")
            if status != "OK":
                print(f"Email UID {uid} not found", file=sys.stderr)
                sys.exit(3)
            raw = None
            for item in msg_data:
                if isinstance(item, tuple):
                    raw = item[1]
                    break
            if raw is None:
                print(f"Email UID {uid} not found", file=sys.stderr)
                sys.exit(3)
            return email_lib.message_from_bytes(raw)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error fetching email: {e}", file=sys.stderr)
        sys.exit(2)


async def send_email(config, to, subject, body, in_reply_to=None, references=None):
    """Send email via SMTP."""
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = config["user"]
    msg["To"] = to
    msg["Subject"] = subject
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references

    try:
        await aiosmtplib.send(
            msg,
            hostname=config["smtp_host"],
            port=config["smtp_port"],
            username=config["user"],
            password=config["password"],
            use_tls=True,
        )
        print(f"Sent to {to}")
    except Exception as e:
        print(f"Error sending email: {e}", file=sys.stderr)
        sys.exit(4)
```

- [ ] **Step 4: Run tests**

```bash
cd ~/.claude/skills/email-assistant
python -m pytest tests/test_smtp.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/email-assistant
git add email_cli.py tests/test_smtp.py && git commit -m "feat: add SMTP send and email header fetching"
```

---

### Task 7: CLI Argparse Wiring

**Files:**
- Modify: `~/.claude/skills/email-assistant/email_cli.py`

- [ ] **Step 1: Add CLI commands and main() to email_cli.py**

Append to `email_cli.py`:

```python
# ── CLI Commands ────────────────────────────────

def cmd_fetch(args):
    config = get_config()
    result = asyncio.run(fetch_emails(config, limit=args.limit, folder=args.folder))
    print(result)


def cmd_reply(args):
    config = get_config()
    orig = asyncio.run(get_email_full(config, args.uid))
    msg_id = orig.get("Message-ID")
    refs = orig.get("References")
    from_addr = orig.get("Reply-To") or orig.get("From", "")
    subject = decode_mime(orig.get("Subject", ""))
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    asyncio.run(send_email(
        config,
        to=args.to or from_addr,
        subject=subject,
        body=args.body,
        in_reply_to=msg_id,
        references=refs,
    ))


def cmd_forward(args):
    config = get_config()
    orig = asyncio.run(get_email_full(config, args.uid))
    subject = decode_mime(orig.get("Subject", ""))
    if not subject.lower().startswith("fwd:"):
        subject = f"Fwd: {subject}"
    orig_body = extract_body(orig)
    fwd_body = f"{args.note}\n\n---------- Forwarded message ----------\n{orig_body}" if args.note else f"---------- Forwarded message ----------\n{orig_body}"

    asyncio.run(send_email(
        config,
        to=args.to,
        subject=subject,
        body=fwd_body,
    ))


def cmd_send(args):
    config = get_config()
    asyncio.run(send_email(config, to=args.to, subject=args.subject, body=args.body))


def cmd_archive(args):
    config = get_config()
    uids = [u.strip() for u in args.uid.split(",")]
    asyncio.run(archive_uids(config, uids))


def cmd_folders(args):
    config = get_config()
    result = asyncio.run(list_folders(config))
    print(result)


def main():
    parser = argparse.ArgumentParser(description="QQ Mail CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("fetch", help="Fetch unread emails")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--folder", default="INBOX")
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("reply", help="Reply to an email by UID")
    p.add_argument("--uid", required=True, help="UID of the email to reply to")
    p.add_argument("--body", required=True, help="Reply body text")
    p.add_argument("--to", default=None, help="Override recipient (default: reply to sender)")
    p.set_defaults(func=cmd_reply)

    p = sub.add_parser("forward", help="Forward an email by UID")
    p.add_argument("--uid", required=True, help="UID of the email to forward")
    p.add_argument("--to", required=True, help="Forward recipient")
    p.add_argument("--note", default="", help="Optional note to prepend")
    p.set_defaults(func=cmd_forward)

    p = sub.add_parser("send", help="Send a new email")
    p.add_argument("--to", required=True)
    p.add_argument("--subject", required=True)
    p.add_argument("--body", required=True)
    p.set_defaults(func=cmd_send)

    p = sub.add_parser("archive", help="Archive emails by UID")
    p.add_argument("--uid", required=True, help="Comma-separated UIDs")
    p.set_defaults(func=cmd_archive)

    p = sub.add_parser("folders", help="List IMAP folders")
    p.set_defaults(func=cmd_folders)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify CLI help works**

```bash
cd ~/.claude/skills/email-assistant
python email_cli.py --help
python email_cli.py fetch --help
```

Expected: Help text displayed without error.

- [ ] **Step 3: Verify missing credentials exits with code 1**

```bash
unset QQ_MAIL_USER QQ_MAIL_APP_PASSWORD
python email_cli.py fetch 2>&1; echo "Exit code: $?"
```

Expected: stderr shows error message, exit code 1.

- [ ] **Step 4: Run all tests**

```bash
cd ~/.claude/skills/email-assistant
python -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/email-assistant
git add email_cli.py && git commit -m "feat: add CLI with all subcommands"
```

---

### Task 8: SKILL.md

**Files:**
- Create: `~/.claude/skills/email-assistant/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: email-assistant
description: |
  QQ 邮箱助手。当用户要求"查看邮件"、"未读邮件"、"回复邮件"、"转发邮件"、"发邮件"、"归档邮件"，
  或提到任何邮件相关操作时使用此技能。
  连接 QQ 邮箱（IMAP/SMTP），拉取未读邮件并展示，支持回复、转发、归档操作。
depends: []
---

# Email Assistant — QQ 邮箱助手

你是一个邮件助手，通过 Python CLI 工具管理 QQ 邮箱。你的职责是帮助用户高效处理邮件。

## 前置检查

每次操作前，先验证凭证是否已配置：

```bash
python ~/.claude/skills/email-assistant/email_cli.py fetch --limit 1
```

如果报错 `QQ_MAIL_USER and QQ_MAIL_APP_PASSWORD required`，引导用户：

1. 登录 QQ 邮箱 → 设置 → 账户 → POP3/IMAP/SMTP → 开启 IMAP
2. 生成授权码（非 QQ 密码）
3. 将授权码添加到 `docker/.env`：

```
QQ_MAIL_USER=你的QQ邮箱
QQ_MAIL_APP_PASSWORD=你的授权码
```

4. 重启容器使环境变量生效

## 操作流程

### 查看未读邮件

```bash
python ~/.claude/skills/email-assistant/email_cli.py fetch [--limit 10] [--folder INBOX]
```

将输出的 Markdown **原样展示**给用户，并根据内容提供简要摘要。
记住每封邮件的 UID 和发件人，后续操作需要用到。

### 回复邮件

当用户说"回复第N封"时：

1. 从上下文中取出对应邮件的 UID
2. 根据用户意图组织回复内容
3. **向用户展示将要发送的内容**并确认
4. 确认后执行：

```bash
python ~/.claude/skills/email-assistant/email_cli.py reply --uid <UID> --body "回复内容"
```

### 转发邮件

当用户说"转发第N封给xxx"时：

1. 从上下文中取出对应邮件的 UID
2. **向用户展示转发内容**并确认
3. 确认后执行：

```bash
python ~/.claude/skills/email-assistant/email_cli.py forward --uid <UID> --to "recipient@example.com" --note "备注（可选）"
```

### 发新邮件

当用户说"给xxx发邮件"时：

1. 确认收件人、主题、正文
2. **向用户展示完整邮件内容**并确认
3. 确认后执行：

```bash
python ~/.claude/skills/email-assistant/email_cli.py send --to "recipient@example.com" --subject "主题" --body "正文"
```

### 归档邮件

当用户说"归档第N封"时：

```bash
python ~/.claude/skills/email-assistant/email_cli.py archive --uid <UID>
```

多个邮件：`--uid 123,456,789`

### 列出文件夹

```bash
python ~/.claude/skills/email-assistant/email_cli.py folders
```

## 安全约束

1. **发送前必须确认** — 回复、转发、新邮件发送前，必须向用户展示完整内容并获确认
2. **不自动批量操作** — 每封邮件的操作需用户明确指示
3. **凭证不输出** — 只检查存在性，不打印密码

## 示例对话

### 示例 1：查看未读

用户：看看有什么新邮件

助手：正在查看未读邮件...
（执行 fetch 命令）
你有 3 封未读邮件：

**1.** 张三 `<zhangsan@work.com>` — 关于项目进度
   下周一的项目评审改到周三，请确认参加。

**2.** 李四 `<lisi@work.com>` — 周报提醒
   请在周五下班前提交本周周报。

**3.** 系统通知 `<noreply@github.com>` — [PR #42] New comment
   有人在你提交的 PR 上留了评论。

需要回复哪封？或者有其他操作？

### 示例 2：回复邮件

用户：回复第1封，告诉他周三没问题

助手：好的，准备回复张三。邮件内容如下：

> Re: 关于项目进度
>
> 张三你好，
> 周三的评审我可以参加，没问题。
>
> 此致

确认发送吗？

用户：确认

助手：（执行 reply 命令）已发送。

### 示例 3：归档

用户：把通知邮件归档

助手：（执行 archive 命令）已将第3封邮件归档。
```

- [ ] **Step 2: Verify skill file is accessible**

```bash
ls -la ~/.claude/skills/email-assistant/SKILL.md
head -5 ~/.claude/skills/email-assistant/SKILL.md
```

Expected: File exists with correct frontmatter.

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills/email-assistant
git add SKILL.md && git commit -m "feat: add SKILL.md for email-assistant"
```

---

### Task 9: Docker .env Template Update

**Files:**
- Modify: `docker/settings.json.template` (if needed)
- Reference: `docker/.env` (user manually adds values)

- [ ] **Step 1: Document new environment variables**

Update `docker/README.md` to include email assistant environment variables in the architecture section. Add after the existing environment variable documentation:

```markdown
### 邮件助手配置（可选）

| 变量 | 用途 |
|------|------|
| `QQ_MAIL_USER` | QQ 邮箱地址 |
| `QQ_MAIL_APP_PASSWORD` | QQ 邮箱授权码（非登录密码） |

获取授权码：QQ 邮箱 → 设置 → 账户 → POP3/IMAP/SMTP → 开启 IMAP → 生成授权码
```

- [ ] **Step 2: Verify .env template reference**

Ensure `docker/docker-compose.yml` passes the new env vars from `.env` into the container. Check if `env_file: - .env` already covers this (it does — all .env vars are injected).

No changes needed to docker-compose.yml since `env_file: - .env` already passes all variables.

- [ ] **Step 3: Commit**

```bash
git add docker/README.md && git commit -m "docs: add email assistant env vars to README"
```

---

### Task 10: Final Verification

- [ ] **Step 1: Run all tests**

```bash
cd ~/.claude/skills/email-assistant
python -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 2: Verify CLI help for all commands**

```bash
python ~/.claude/skills/email-assistant/email_cli.py --help
python ~/.claude/skills/email-assistant/email_cli.py fetch --help
python ~/.claude/skills/email-assistant/email_cli.py reply --help
python ~/.claude/skills/email-assistant/email_cli.py forward --help
python ~/.claude/skills/email-assistant/email_cli.py send --help
python ~/.claude/skills/email-assistant/email_cli.py archive --help
python ~/.claude/skills/email-assistant/email_cli.py folders --help
```

Expected: All commands show help without error.

- [ ] **Step 3: Verify SKILL.md syntax**

```bash
head -10 ~/.claude/skills/email-assistant/SKILL.md
```

Expected: Valid YAML frontmatter with name and description fields.

- [ ] **Step 4: Manual integration test** (requires real QQ mail credentials)

```bash
# Set credentials in environment
export QQ_MAIL_USER=your@qq.com
export QQ_MAIL_APP_PASSWORD=your_auth_code

# Test fetch
python ~/.claude/skills/email-assistant/email_cli.py fetch --limit 3

# Test folders
python ~/.claude/skills/email-assistant/email_cli.py folders
```

Expected: Real email data returned without error (or clear error messages if credentials are wrong).
