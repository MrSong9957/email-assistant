"""QQ Mail CLI for Claude Code email-assistant skill."""

import argparse
import asyncio
import datetime
import email as email_lib
import json
import os
import re
import socket as socket_mod
import ssl
import sys
from contextlib import asynccontextmanager
from email.header import decode_header
from email.utils import parsedate_to_datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aioimaplib
import aiosmtplib


# ── Provider Defaults ────────────────────────────

PROVIDER_DEFAULTS = {
    "qq": {
        "env_prefix": "QQ_MAIL",
        "imap_host": "imap.qq.com",
        "imap_port": 993,
        "smtp_host": "smtp.qq.com",
        "smtp_port": 465,
        "archive_folder": "Archives",
        "sent_folder": "Sent Messages",
    },
    "gmail": {
        "env_prefix": "GMAIL",
        "imap_host": "imap.gmail.com",
        "imap_port": 993,
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 465,
        "archive_folder": "[Gmail]/All Mail",
        "sent_folder": "[Gmail]/Sent Mail",
        "needs_proxy": True,
    },
    "163": {
        "env_prefix": "MAIL163",
        "imap_host": "imap.163.com",
        "imap_port": 993,
        "smtp_host": "smtp.163.com",
        "smtp_port": 465,
        "archive_folder": "Archives",
        "sent_folder": "Sent Messages",
        "needs_id": True,
    },
    "outlook": {
        "env_prefix": "OUTLOOK",
        "imap_host": "outlook.office365.com",
        "imap_port": 993,
        "smtp_host": "smtp.office365.com",
        "smtp_port": 587,
        "smtp_starttls": True,
        "archive_folder": "Archive",
        "sent_folder": "Sent",
        "needs_proxy": True,
    },
    "139": {
        "env_prefix": "MAIL139",
        "imap_host": "imap.139.com",
        "imap_port": 993,
        "smtp_host": "smtp.139.com",
        "smtp_port": 465,
        "archive_folder": "Archives",
        "sent_folder": "Sent Messages",
    },
}


# ── Persona & Style Config ──────────────────────

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))

PERSONAS = {
    "sarcastic": {
        "name": "阴阳损友",
        "instruction": "尖酸刻薄、反讽互损、用梗密集，但不含真正攻击性",
        "example": "你可真行，三天不回消息还活着呢？我还以为你被外星人绑架了",
    },
    "workplace": {
        "name": "职场沟通",
        "instruction": "逻辑清晰、用词精简、结论先行，不带废话",
        "example": "方案B数据更完整，建议周四前确定，我这边同步排期",
    },
    "customer": {
        "name": "客户回复",
        "instruction": "热情专业、解答精准，热情但不啰嗦",
        "example": "收到，这个问题我查了一下，原因是X，解决方案是Y，您试试看，有问题随时找我",
    },
    "romantic": {
        "name": "情侣互动",
        "instruction": "温暖肉麻、带鼓励、亲昵称呼自然",
        "example": "宝你今天辛苦了，早点休息，明天的事明天再说，我陪你",
    },
}

DEFAULT_PERSONA_SETTINGS = {
    "sarcastic": {"use_style_profile": True},
    "workplace": {"use_style_profile": False},
    "customer": {"use_style_profile": False},
    "romantic": {"use_style_profile": True},
}


def load_persona_mapping():
    """Load persona-mapping.json. Returns default structure if not found."""
    path = os.path.join(SKILL_DIR, "persona-mapping.json")
    if not os.path.isfile(path):
        return {
            "default_persona": "workplace",
            "recipients": {},
            "persona_settings": json.loads(json.dumps(DEFAULT_PERSONA_SETTINGS)),
        }
    with open(path) as f:
        data = json.load(f)
    if "persona_settings" not in data:
        data["persona_settings"] = json.loads(json.dumps(DEFAULT_PERSONA_SETTINGS))
    return data


def save_persona_mapping(mapping):
    """Save persona-mapping.json."""
    path = os.path.join(SKILL_DIR, "persona-mapping.json")
    with open(path, "w") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_style_profile():
    """Load style-profile.json. Returns None if not found."""
    path = os.path.join(SKILL_DIR, "style-profile.json")
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_style_profile(summary, scenarios, source_files=None, catchphrases=None):
    """Save style-profile.json."""
    path = os.path.join(SKILL_DIR, "style-profile.json")
    profile = {
        "version": 1,
        "created": datetime.date.today().isoformat(),
        "source_files": source_files or [],
        "summary": summary,
        "scenarios": scenarios,
        "catchphrases": catchphrases or [],
    }
    with open(path, "w") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
        f.write("\n")


def clear_style_profile():
    """Delete style-profile.json."""
    path = os.path.join(SKILL_DIR, "style-profile.json")
    if os.path.isfile(path):
        os.remove(path)


# ── SOCKS5 Proxy ───────────────────────────────

async def _sock_recv_exact(loop, sock, n):
    """Read exactly n bytes from a non-blocking socket."""
    buf = b""
    while len(buf) < n:
        chunk = await loop.sock_recv(sock, n - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed during SOCKS5 handshake")
        buf += chunk
    return buf


async def _socks5_open(dest_host, dest_port, proxy_host, proxy_port):
    """Connect to dest_host:dest_port through a SOCKS5 proxy. Returns socket."""
    sock = socket_mod.socket(socket_mod.AF_INET, socket_mod.SOCK_STREAM)
    sock.setblocking(False)
    loop = asyncio.get_event_loop()
    await loop.sock_connect(sock, (proxy_host, proxy_port))

    # Greeting: version 5, 1 method, no-auth (0x00)
    await loop.sock_sendall(sock, b"\x05\x01\x00")
    await _sock_recv_exact(loop, sock, 2)

    # Connect request with domain name
    host_bytes = dest_host.encode()
    await loop.sock_sendall(
        sock,
        b"\x05\x01\x00\x03"
        + bytes([len(host_bytes)]) + host_bytes
        + dest_port.to_bytes(2, "big"),
    )
    resp = await _sock_recv_exact(loop, sock, 4)
    if resp[1] != 0:
        sock.close()
        raise ConnectionError(f"SOCKS5 proxy refused: status {resp[1]}")

    # Skip bound address
    if resp[3] == 1:
        await _sock_recv_exact(loop, sock, 6)
    elif resp[3] == 3:
        n = (await _sock_recv_exact(loop, sock, 1))[0]
        await _sock_recv_exact(loop, sock, n + 2)
    elif resp[3] == 4:
        await _sock_recv_exact(loop, sock, 18)

    return sock


class _ProxiedIMAP4_SSL(aioimaplib.IMAP4_SSL):
    """IMAP4_SSL that tunnels through a SOCKS5 proxy."""

    def __init__(self, host, port, proxy_host, proxy_port, **kwargs):
        self._proxy_host = proxy_host
        self._proxy_port = proxy_port
        super().__init__(host, port, **kwargs)

    def create_client(self, host, port, loop, conn_lost_cb=None, ssl_context=None):
        if ssl_context is None:
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        local_loop = loop or asyncio.get_event_loop()
        self.protocol = aioimaplib.aioimaplib.IMAP4ClientProtocol(local_loop, conn_lost_cb)

        async def _connect():
            sock = await _socks5_open(host, port, self._proxy_host, self._proxy_port)
            await local_loop.create_connection(
                lambda: self.protocol, sock=sock,
                ssl=ssl_context, server_hostname=host,
            )

        self._client_task = local_loop.create_task(_connect())


# ── Config ──────────────────────────────────────

def _load_dotenv():
    """Load .env from script directory, then project root as fallback."""
    env_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        os.path.join("/home/app/project", ".env"),
    ]
    for env_path in env_paths:
        if not os.path.isfile(env_path):
            continue
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip().strip("'\"")
                os.environ.setdefault(key, value)


def list_accounts():
    """List configured email accounts from environment."""
    _load_dotenv()
    raw = os.environ.get("MAIL_ACCOUNTS", "")
    if raw:
        names = [n.strip() for n in raw.split(",") if n.strip()]
    elif os.environ.get("QQ_MAIL_USER"):
        names = ["qq"]
    else:
        names = []
    accounts = []
    for name in names:
        provider = PROVIDER_DEFAULTS.get(name)
        if not provider:
            continue
        user = os.environ.get(f"{provider['env_prefix']}_USER", "")
        if user:
            accounts.append({"name": name, "user": user})
    return accounts


def get_config(account=None):
    """Read email configuration for a specific account."""
    _load_dotenv()
    accounts = list_accounts()
    if not accounts:
        print("Error: No email accounts configured.", file=sys.stderr)
        sys.exit(1)
    if account:
        matched = [a for a in accounts if a["name"] == account]
        if not matched:
            names = ", ".join(a["name"] for a in accounts)
            print(f"Error: Account '{account}' not found. Available: {names}", file=sys.stderr)
            sys.exit(1)
        target = matched[0]
    else:
        target = accounts[0]
    name = target["name"]
    provider = PROVIDER_DEFAULTS[name]
    prefix = provider["env_prefix"]
    user = os.environ.get(f"{prefix}_USER", "")
    password = os.environ.get(f"{prefix}_APP_PASSWORD", "")
    if not user or not password:
        print(
            f"Error: {prefix}_USER and {prefix}_APP_PASSWORD required.\n"
            "Get app password from your email provider's settings",
            file=sys.stderr,
        )
        sys.exit(1)
    return {
        "account": name,
        "user": user,
        "password": password,
        "imap_host": os.environ.get(f"{prefix}_IMAP_HOST", provider["imap_host"]),
        "imap_port": int(os.environ.get(f"{prefix}_IMAP_PORT", str(provider["imap_port"]))),
        "smtp_host": os.environ.get(f"{prefix}_SMTP_HOST", provider["smtp_host"]),
        "smtp_port": int(os.environ.get(f"{prefix}_SMTP_PORT", str(provider["smtp_port"]))),
        "archive_folder": os.environ.get(f"{prefix}_ARCHIVE_FOLDER", provider["archive_folder"]),
        "sent_folder": os.environ.get(f"{prefix}_SENT_FOLDER", provider.get("sent_folder", "Sent Messages")),
        "smtp_starttls": provider.get("smtp_starttls", False),
        "needs_id": provider.get("needs_id", False),
        "needs_proxy": provider.get("needs_proxy", False),
        "proxy_host": os.environ.get("SOCKS5_PROXY_HOST", ""),
        "proxy_port": int(os.environ.get("SOCKS5_PROXY_PORT", "0")),
    }


@asynccontextmanager
async def imap_client(config):
    """Async context manager for IMAP connection."""
    if config.get("needs_proxy") and config.get("proxy_host"):
        client = _ProxiedIMAP4_SSL(
            config["imap_host"], config["imap_port"],
            config["proxy_host"], config["proxy_port"],
        )
    else:
        client = aioimaplib.IMAP4_SSL(config["imap_host"], config["imap_port"])
    try:
        await client.wait_hello_from_server()
        await client.login(config["user"], config["password"])
        if config.get("needs_id"):
            from aioimaplib import Commands, Cmd, Exec
            Commands['ID'] = Cmd(name='ID', valid_states=('AUTH', 'SELECTED'), exec=Exec.is_sync)
            cmd = aioimaplib.Command('ID', client.protocol.new_tag(),
                                     '("name" "email_cli" "version" "1.0")',
                                     loop=asyncio.get_event_loop())
            await client.protocol.execute(cmd)
        yield client
    except Exception as e:
        print(
            f"IMAP connection error: {e}\n\n"
            "提示：如无法直接连接此邮箱，可在该邮箱中设置转发规则，\n"
            "将邮件转发到已配置的邮箱来查看。详见 SKILL.md「连接失败兜底」。",
            file=sys.stderr,
        )
        sys.exit(2)
    finally:
        try:
            await client.logout()
        except Exception:
            pass


def decode_mime(value):
    """Decode MIME-encoded header value to readable string."""
    if not value:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, (bytes, bytearray)):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def strip_html(text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    import html as html_mod
    return html_mod.unescape(text).strip()


def build_web_link(config, msg):
    """Build a web link to the mail provider's webmail. Returns None if unknown."""
    account = config.get("account", "")
    if account == "gmail":
        return "https://mail.google.com/"
    if account == "qq":
        return "https://mail.qq.com/"
    if account == "outlook":
        return "https://outlook.live.com/"
    if account == "163":
        return "https://mail.163.com/"
    if account == "139":
        return "https://mail.10086.cn/"
    return None


def extract_html_body(msg):
    """Extract HTML body from email. Returns empty string if no HTML part."""
    if not msg.is_multipart():
        if msg.get_content_type() == "text/html":
            payload = msg.get_payload(decode=True)
            if payload is None:
                return ""
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
        return ""
    for part in msg.get_payload():
        if isinstance(part, str):
            continue
        if part.is_multipart():
            sub = extract_html_body(part)
            if sub:
                return sub
        elif part.get_content_type() == "text/html":
            p = part.get_payload(decode=True)
            if p:
                charset = part.get_content_charset() or "utf-8"
                return p.decode(charset, errors="replace")
    return ""


def extract_body(msg):
    """Extract readable text from an email message.

    Args:
        msg: email.message.Message object

    Returns:
        str: Readable text content of the email
    """
    if not msg.is_multipart():
        payload = msg.get_payload(decode=True)
        if payload is None:
            return ""
        charset = msg.get_content_charset() or "utf-8"
        text = payload.decode(charset, errors="replace")
        if msg.get_content_type() == "text/html":
            return strip_html(text)
        return text
    plain = None
    html = None
    for part in msg.get_payload():
        if isinstance(part, str):
            continue
        ct = part.get_content_type()
        if part.is_multipart():
            sub = extract_body(part)
            if sub:
                return sub
        elif ct == "text/plain" and plain is None:
            p = part.get_payload(decode=True)
            if p:
                plain = p.decode(part.get_content_charset() or "utf-8", errors="replace")
        elif ct == "text/html" and html is None:
            p = part.get_payload(decode=True)
            if p:
                html = strip_html(p.decode(part.get_content_charset() or "utf-8", errors="replace"))
    return plain or html or ""


def format_email(index, uid, msg, sent=False, config=None):
    """Format a single email as Markdown."""
    subject = decode_mime(msg.get("Subject", "(No Subject)"))
    date = msg.get("Date", "Unknown")

    lines = [
        f"## [{index}] UID: {uid} | {date}",
    ]

    if sent:
        to_addr = decode_mime(msg.get("To", "Unknown"))
        lines.append(f"**To:** {to_addr}")
    else:
        from_addr = decode_mime(msg.get("From", "Unknown"))
        lines.append(f"**From:** {from_addr}")

    lines.append(f"**Subject:** {subject}")

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

    if config is not None:
        link = build_web_link(config, msg)
        if link:
            lines.append(f"**Link:** {link}")

    lines.append("")
    body = extract_body(msg)
    lines.append(body if body else "(No readable content)")

    return "\n".join(lines)


# ── IMAP Operations ──────────────────────────────

def _parse_email_date(msg):
    """Parse email Date header to datetime.date. Returns None on failure."""
    date_str = msg.get("Date", "")
    try:
        return parsedate_to_datetime(date_str).date()
    except Exception:
        return None


def filter_emails(emails, since=None, before=None, from_addr=None, subject=None):
    """Filter list of (uid, msg) tuples by date/sender/subject criteria."""
    since_date = None
    if since:
        since_date = datetime.date.fromisoformat(since)
    before_date = None
    if before:
        before_date = datetime.date.fromisoformat(before)

    filtered = []
    for uid, msg in emails:
        if since_date or before_date:
            email_date = _parse_email_date(msg)
            if email_date is None:
                continue
            if since_date and email_date < since_date:
                continue
            if before_date and email_date >= before_date:
                continue
        if from_addr:
            sender = msg.get("From", "").lower()
            if from_addr.lower() not in sender:
                continue
        if subject:
            subj = msg.get("Subject", "").lower()
            if subject.lower() not in subj:
                continue
        filtered.append((uid, msg))
    return filtered


def format_emails(emails, sent=False, config=None):
    """Format list of (uid, msg) tuples as Markdown with reindexed headers."""
    if not emails:
        title = "已发送邮件" if sent else "未读邮件"
        return f"# {title} (0封)\n"
    parts = []
    for i, (uid, msg) in enumerate(emails, 1):
        parts.append(format_email(i, uid, msg, sent=sent, config=config))
    title = "已发送邮件" if sent else "未读邮件"
    header = f"# {title} ({len(emails)}封)\n\n"
    return header + "\n\n---\n\n".join(parts)


async def fetch_emails(config, limit=10, folder="INBOX", search="UNSEEN"):
    """Fetch emails and return list of (uid, msg) tuples."""
    try:
        async with imap_client(config) as client:
            selected_folder = f'"{folder}"' if " " in folder else folder
            await client.select(selected_folder)
            status, data = await client.search(search)
            if status != "OK" or not data[0].strip():
                return []

            seqs = data[0].split()
            seqs = seqs[-limit:]

            results = []
            for seq_bytes in seqs:
                seq_str = seq_bytes.decode()
                status, msg_data = await client.fetch(seq_str, "(UID BODY.PEEK[])")
                if status != "OK":
                    continue
                uid_str = ""
                raw_email = None
                for item in msg_data:
                    if isinstance(item, (bytes, bytearray)):
                        text = bytes(item)
                        if b"UID" in text and raw_email is None:
                            m = re.search(rb"UID (\d+)", text)
                            if m:
                                uid_str = m.group(1).decode()
                        elif b"Received:" in text or b"From:" in text or b"Return-Path:" in text:
                            raw_email = text
                if raw_email is None:
                    continue
                msg = email_lib.message_from_bytes(raw_email)
                results.append((uid_str, msg))

            return results
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error fetching emails: {e}", file=sys.stderr)
        sys.exit(2)


async def list_folders(config):
    """List available IMAP folders. Returns formatted string."""
    try:
        async with imap_client(config) as client:
            status, folders = await client.list('""', '"*"')
            if status != "OK":
                return "Error listing folders"
            lines = []
            for folder in folders:
                if isinstance(folder, (bytes, bytearray)):
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


async def mark_read_uids(config, uids):
    """Mark emails as read by setting \\Seen flag."""
    try:
        async with imap_client(config) as client:
            await client.select("INBOX")
            for uid in uids:
                await client.uid("store", uid, "+FLAGS", "\\Seen")
            print(f"Marked {len(uids)} email(s) as read")
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error marking as read: {e}", file=sys.stderr)
        sys.exit(2)


async def get_email_headers(config, uid):
    """Fetch Message-ID and References for threading. Returns (message_id, references)."""
    try:
        async with imap_client(config) as client:
            await client.select("INBOX")
            status, msg_data = await client.uid("fetch", uid, "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID REFERENCES FROM SUBJECT)])")
            if status != "OK":
                print(f"Email UID {uid} not found", file=sys.stderr)
                sys.exit(3)
            raw = None
            for item in msg_data:
                if isinstance(item, (bytes, bytearray)):
                    text = bytes(item)
                    if b"Message-ID" in text or b"From:" in text:
                        raw = text
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
            status, msg_data = await client.uid("fetch", uid, "(RFC822)")
            if status != "OK":
                print(f"Email UID {uid} not found", file=sys.stderr)
                sys.exit(3)
            raw = None
            for item in msg_data:
                if isinstance(item, (bytes, bytearray)):
                    text = bytes(item)
                    if b"From:" in text or b"Received:" in text or b"Return-Path:" in text:
                        raw = text
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


async def send_email(config, to, subject, body, in_reply_to=None, references=None, html_body=None):
    """Send email via SMTP. If html_body is provided, sends multipart/alternative."""
    if html_body:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
    else:
        msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = config["user"]
    msg["To"] = to
    msg["Subject"] = subject
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references

    try:
        if config.get("needs_proxy") and config.get("proxy_host"):
            sock = await _socks5_open(
                config["smtp_host"], config["smtp_port"],
                config["proxy_host"], config["proxy_port"],
            )
            smtp_kwargs = dict(
                hostname=config["smtp_host"],
                username=config["user"],
                password=config["password"],
                sock=sock,
            )
            if config.get("smtp_starttls"):
                smtp_kwargs.update(use_tls=False, start_tls=True)
            else:
                smtp_kwargs.update(use_tls=True)
            async with aiosmtplib.SMTP(**smtp_kwargs) as smtp:
                await smtp.send_message(msg)
        elif config.get("smtp_starttls"):
            await aiosmtplib.send(
                msg,
                hostname=config["smtp_host"],
                port=config["smtp_port"],
                username=config["user"],
                password=config["password"],
                use_tls=False,
                start_tls=True,
            )
        else:
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


# ── CLI Commands ────────────────────────────────

def cmd_set_persona(args):
    """Set persona mapping (default or per-recipient)."""
    if getattr(args, "style_profile", None):
        persona_key, value = args.style_profile
        if persona_key not in PERSONAS:
            print(f"Error: Unknown persona '{persona_key}'. Available: {', '.join(PERSONAS.keys())}", file=sys.stderr)
            sys.exit(1)
        if value not in ("on", "off"):
            print(f"Error: Invalid value '{value}'. Use 'on' or 'off'.", file=sys.stderr)
            sys.exit(1)
        mapping = load_persona_mapping()
        if "persona_settings" not in mapping:
            mapping["persona_settings"] = json.loads(json.dumps(DEFAULT_PERSONA_SETTINGS))
        mapping["persona_settings"][persona_key] = {"use_style_profile": value == "on"}
        save_persona_mapping(mapping)
        print(f"Style profile for persona '{persona_key}' set to {value}")
    elif args.default:
        if args.default not in PERSONAS:
            print(f"Error: Unknown persona '{args.default}'. Available: {', '.join(PERSONAS.keys())}", file=sys.stderr)
            sys.exit(1)
        mapping = load_persona_mapping()
        mapping["default_persona"] = args.default
        save_persona_mapping(mapping)
        print(f"Default persona set to {args.default}")
    elif args.to:
        if not args.persona:
            print("Error: persona key required with --to", file=sys.stderr)
            sys.exit(1)
        if args.persona not in PERSONAS:
            print(f"Error: Unknown persona '{args.persona}'. Available: {', '.join(PERSONAS.keys())}", file=sys.stderr)
            sys.exit(1)
        mapping = load_persona_mapping()
        mapping["recipients"][args.to] = args.persona
        save_persona_mapping(mapping)
        print(f"Persona for {args.to} set to {args.persona}")
    else:
        print("Error: --default, --to, or --style-profile required", file=sys.stderr)
        sys.exit(1)


def cmd_list_personas(args):
    """List all personas and current mapping."""
    mapping = load_persona_mapping()
    settings = mapping.get("persona_settings", DEFAULT_PERSONA_SETTINGS)
    for key, persona in PERSONAS.items():
        toggle = settings.get(key, {}).get("use_style_profile", True)
        icon = "✅" if toggle else "❌"
        print(f"  {persona['name']}({key})      词库: {icon}")
    print(f"全局默认：{mapping['default_persona']}")
    if mapping["recipients"]:
        print("收件人映射：")
        for email_addr, persona_key in mapping["recipients"].items():
            print(f"  {email_addr} → {persona_key}")


def cmd_style_profile_show(args):
    """Show current style profile."""
    mapping = load_persona_mapping()
    default_persona = mapping["default_persona"]
    settings = mapping.get("persona_settings", DEFAULT_PERSONA_SETTINGS)
    use_sp = settings.get(default_persona, {}).get("use_style_profile", True)
    if not use_sp:
        print(f"Style profile disabled for current persona: {default_persona}")
        return
    profile = load_style_profile()
    if profile is None:
        print("No style profile found.")
        return
    print(json.dumps(profile, ensure_ascii=False, indent=2))


def cmd_style_profile_clear(args):
    """Clear style profile."""
    clear_style_profile()
    print("Style profile cleared.")


def cmd_style_profile_save(args):
    """Save style profile (called by AI, not user directly)."""
    try:
        scenarios = json.loads(args.scenarios)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in --scenarios: {e}", file=sys.stderr)
        sys.exit(1)
    try:
        source_files = json.loads(args.source_files) if args.source_files else []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in --source-files: {e}", file=sys.stderr)
        sys.exit(1)
    try:
        catchphrases = json.loads(args.catchphrases) if args.catchphrases else []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in --catchphrases: {e}", file=sys.stderr)
        sys.exit(1)
    save_style_profile(args.summary, scenarios, source_files, catchphrases)
    print("Style profile saved.")


def cmd_list_accounts(args):
    accounts = list_accounts()
    if not accounts:
        print("No accounts configured.")
        return
    for acc in accounts:
        print(f"  {acc['name']}: {acc['user']}")


def cmd_fetch(args):
    since = args.since
    if args.days is not None:
        if since:
            print("Error: --days and --since cannot be used together", file=sys.stderr)
            sys.exit(1)
        since = (datetime.date.today() - datetime.timedelta(days=args.days)).isoformat()

    for label, val in [("--since", since), ("--before", args.before)]:
        if val:
            try:
                datetime.date.fromisoformat(val)
            except ValueError:
                print(f"Error: invalid date format '{val}', expected YYYY-MM-DD", file=sys.stderr)
                sys.exit(1)

    config = get_config(getattr(args, "account", None))
    limit = 0 if args.fetch_all else args.limit
    emails = asyncio.run(fetch_emails(config, limit=limit, folder=args.folder))
    filtered = filter_emails(emails, since=since, before=args.before,
                             from_addr=args.from_addr, subject=args.subject)
    print(format_emails(filtered, config=config))


def cmd_reply(args):
    config = get_config(getattr(args, "account", None))
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
    config = get_config(getattr(args, "account", None))
    orig = asyncio.run(get_email_full(config, args.uid))
    subject = decode_mime(orig.get("Subject", ""))
    if not subject.lower().startswith("fwd:"):
        subject = f"Fwd: {subject}"

    from_addr = decode_mime(orig.get("From", ""))
    date_str = orig.get("Date", "")
    orig_subject = decode_mime(orig.get("Subject", ""))
    fwd_header_plain = f"---------- Forwarded message ----------\nFrom: {from_addr}\nDate: {date_str}\nSubject: {orig_subject}\n"
    fwd_header_html = (
        '<div style="border-left: 2px solid #ccc; padding-left: 8px; margin-left: 4px;">'
        f'<br><b>From:</b> {from_addr}<br><b>Date:</b> {date_str}<br><b>Subject:</b> {orig_subject}<br><br>'
    )

    orig_body = extract_body(orig)
    orig_html = extract_html_body(orig)

    note_prefix = f"{args.note}\n\n" if args.note else ""
    note_html = f"<p>{args.note}</p><br>" if args.note else ""

    plain = f"{note_prefix}{fwd_header_plain}\n{orig_body}"

    html = None
    if orig_html:
        html = f"{note_html}{fwd_header_html}{orig_html}</div>"

    asyncio.run(send_email(
        config,
        to=args.to,
        subject=subject,
        body=plain,
        html_body=html,
    ))


def cmd_send(args):
    config = get_config(getattr(args, "account", None))
    asyncio.run(send_email(config, to=args.to, subject=args.subject, body=args.body))


def cmd_sent(args):
    config = get_config(getattr(args, "account", None))
    folder = args.folder or config["sent_folder"]
    emails = asyncio.run(fetch_emails(config, limit=args.limit, folder=folder, search="ALL"))
    emails.reverse()
    print(format_emails(emails, sent=True, config=config))


def cmd_archive(args):
    config = get_config(getattr(args, "account", None))
    uids = [u.strip() for u in args.uid.split(",")]
    asyncio.run(archive_uids(config, uids))


def cmd_folders(args):
    config = get_config(getattr(args, "account", None))
    result = asyncio.run(list_folders(config))
    print(result)


def cmd_mark_read(args):
    config = get_config(getattr(args, "account", None))
    uids = [u.strip() for u in args.uid.split(",")]
    asyncio.run(mark_read_uids(config, uids))


def main():
    parser = argparse.ArgumentParser(description="QQ Mail CLI")
    parser.add_argument("--account", "-a", default=None,
                        help="Account name (default: first configured account)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list-accounts", help="List configured email accounts")
    p.set_defaults(func=cmd_list_accounts)

    p = sub.add_parser("fetch", help="Fetch unread emails")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--all", action="store_true", dest="fetch_all", help="Fetch all unread emails (no limit)")
    p.add_argument("--folder", default="INBOX")
    p.add_argument("--since", default=None, help="Start date inclusive (YYYY-MM-DD)")
    p.add_argument("--before", default=None, help="End date exclusive (YYYY-MM-DD)")
    p.add_argument("--days", type=int, default=None, help="Last N days")
    p.add_argument("--from", dest="from_addr", default=None, help="Sender substring match")
    p.add_argument("--subject", default=None, help="Subject substring match")
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

    p = sub.add_parser("sent", help="List recently sent emails")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--folder", default=None, help="Override sent folder name")
    p.set_defaults(func=cmd_sent)

    p = sub.add_parser("archive", help="Archive emails by UID")
    p.add_argument("--uid", required=True, help="Comma-separated UIDs")
    p.set_defaults(func=cmd_archive)

    p = sub.add_parser("folders", help="List IMAP folders")
    p.set_defaults(func=cmd_folders)

    p = sub.add_parser("mark-read", help="Mark emails as read")
    p.add_argument("--uid", required=True, help="Comma-separated UIDs")
    p.set_defaults(func=cmd_mark_read)

    p = sub.add_parser("set-persona", help="Set persona mapping")
    p.add_argument("--default", default=None, help="Set global default persona")
    p.add_argument("--to", default=None, metavar="EMAIL", help="Set persona for a specific recipient")
    p.add_argument("--style-profile", nargs=2, metavar=("PERSONA", "ON_OFF"),
                    help="Toggle style profile for a persona (on/off)")
    p.add_argument("persona", nargs="?", default=None, help="Persona key (used with --to)")
    p.set_defaults(func=cmd_set_persona)

    p = sub.add_parser("list-personas", help="List all personas and current mapping")
    p.set_defaults(func=cmd_list_personas)

    p = sub.add_parser("style-profile", help="Manage style profile")
    sp = p.add_subparsers(dest="style_action", required=True)

    sp_show = sp.add_parser("show", help="Show current style profile")
    sp_show.set_defaults(func=cmd_style_profile_show)

    sp_clear = sp.add_parser("clear", help="Clear style profile")
    sp_clear.set_defaults(func=cmd_style_profile_clear)

    sp_save = sp.add_parser("save", help="Save style profile (AI-called)")
    sp_save.add_argument("--summary", required=True, help="Style summary text")
    sp_save.add_argument("--scenarios", required=True, help="JSON array of {context, example}")
    sp_save.add_argument("--source-files", default=None, help="JSON array of source filenames")
    sp_save.add_argument("--catchphrases", default=None, help="JSON array of catchphrases/quotes")
    sp_save.set_defaults(func=cmd_style_profile_save)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
