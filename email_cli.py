"""QQ Mail CLI for Claude Code email-assistant skill."""

import argparse
import asyncio
import datetime
import email as email_lib
import os
import re
import sys
from contextlib import asynccontextmanager
from email.header import decode_header
from email.utils import parsedate_to_datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aioimaplib
import aiosmtplib


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


def get_config():
    """Read email configuration from environment variables."""
    _load_dotenv()
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
        "sent_folder": os.environ.get("QQ_MAIL_SENT_FOLDER", "Sent Messages"),
    }


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


def format_email(index, uid, msg, sent=False):
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


def format_emails(emails, sent=False):
    """Format list of (uid, msg) tuples as Markdown with reindexed headers."""
    if not emails:
        title = "已发送邮件" if sent else "未读邮件"
        return f"# {title} (0封)\n"
    parts = []
    for i, (uid, msg) in enumerate(emails, 1):
        parts.append(format_email(i, uid, msg, sent=sent))
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

    config = get_config()
    limit = 0 if args.fetch_all else args.limit
    emails = asyncio.run(fetch_emails(config, limit=limit, folder=args.folder))
    filtered = filter_emails(emails, since=since, before=args.before,
                             from_addr=args.from_addr, subject=args.subject)
    print(format_emails(filtered))


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
    config = get_config()
    asyncio.run(send_email(config, to=args.to, subject=args.subject, body=args.body))


def cmd_sent(args):
    config = get_config()
    folder = args.folder or config["sent_folder"]
    emails = asyncio.run(fetch_emails(config, limit=args.limit, folder=folder, search="ALL"))
    emails.reverse()
    print(format_emails(emails, sent=True))


def cmd_archive(args):
    config = get_config()
    uids = [u.strip() for u in args.uid.split(",")]
    asyncio.run(archive_uids(config, uids))


def cmd_folders(args):
    config = get_config()
    result = asyncio.run(list_folders(config))
    print(result)


def cmd_mark_read(args):
    config = get_config()
    uids = [u.strip() for u in args.uid.split(",")]
    asyncio.run(mark_read_uids(config, uids))


def main():
    parser = argparse.ArgumentParser(description="QQ Mail CLI")
    sub = parser.add_subparsers(dest="command", required=True)

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

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
