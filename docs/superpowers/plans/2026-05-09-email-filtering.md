# 邮件筛选功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `fetch` 命令添加客户端侧的日期、发件人、主题筛选，支持自然语言交互。

**Architecture:** `fetch_emails` 改为返回结构化数据列表 `[(uid, msg), ...]`，新增纯函数 `filter_emails` 做本地过滤，`format_emails` 负责格式化输出。`cmd_fetch` 串联 fetch → filter → format。

**Tech Stack:** Python 3.11+，email 标准库解析 RFC 2822 日期，argparse CLI

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `email_cli.py` | Modify | 重构 `fetch_emails` 返回值，新增 `filter_emails`，提取 `format_emails`，更新 `cmd_fetch` 和 argparse |
| `tests/test_imap.py` | Modify | 新增 `TestFilterEmails` 测试类 |
| `SKILL.md` | Modify | 新增筛选映射指南 |

---

### Task 1: 重构 fetch_emails — 返回结构化数据

**Files:**
- Modify: `email_cli.py:175-215`（`fetch_emails` 函数）
- Modify: `tests/test_imap.py:27-85`（现有 3 个 fetch 测试需适配新返回值）

- [ ] **Step 1: 修改 fetch_emails 返回列表而非 Markdown**

将 `fetch_emails` 的返回值从 Markdown 字符串改为 `[(uid, msg), ...]` 列表。空结果返回空列表。

```python
async def fetch_emails(config, limit=10, folder="INBOX"):
    """Fetch unread emails and return list of (uid, msg) tuples."""
    try:
        async with imap_client(config) as client:
            await client.select(folder)
            status, data = await client.search("UNSEEN")
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
                        text = item if isinstance(item, bytes) else bytes(item)
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
```

- [ ] **Step 2: 更新现有 3 个 fetch 测试的断言**

测试返回值从字符串改为列表，断言列表长度和内容。

`test_returns_markdown_with_emails` → `test_returns_list_of_emails`：
```python
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
```

`test_returns_empty_when_no_unseen`：
```python
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
```

`test_respects_limit`：
```python
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
```

- [ ] **Step 3: 运行测试验证重构不破坏**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS（fetch 测试断言新返回值，其他测试不受影响）

- [ ] **Step 4: 提交**

```bash
git add email_cli.py tests/test_imap.py
git commit -m "refactor: fetch_emails returns structured list instead of markdown"
```

---

### Task 2: 新增 filter_emails 纯函数 + format_emails

**Files:**
- Modify: `email_cli.py`（新增 `filter_emails`，新增 `format_emails`）
- Modify: `tests/test_imap.py`（新增 `TestFilterEmails` 类）

- [ ] **Step 1: 写 filter_emails 的失败测试**

在 `tests/test_imap.py` 末尾新增测试类，用真实的 `email_lib.message_from_bytes` 构造测试数据，不 mock IMAP：

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_imap.py::TestFilterEmails -v`
Expected: FAIL（`ImportError: cannot import name 'filter_emails'`）

- [ ] **Step 3: 实现 filter_emails**

在 `email_cli.py` 的 `fetch_emails` 函数之前（约第 173 行）新增：

```python
def _parse_email_date(msg):
    """Parse email Date header to datetime.date. Returns None on failure."""
    from email.utils import parsedate_to_datetime
    date_str = msg.get("Date", "")
    try:
        return parsedate_to_datetime(date_str).date()
    except Exception:
        return None


def filter_emails(emails, since=None, before=None, from_addr=None, subject=None):
    """Filter list of (uid, msg) tuples by date/sender/subject criteria."""
    from datetime import date as date_type
    import datetime

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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_imap.py::TestFilterEmails -v`
Expected: ALL PASS

- [ ] **Step 5: 新增 format_emails + 写测试**

`format_emails` 接收过滤后的列表，重新编号后拼接 Markdown。先在 `tests/test_imap.py` 新增：

```python
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
```

Run: `python -m pytest tests/test_imap.py::TestFormatEmails -v`
Expected: FAIL

- [ ] **Step 6: 实现 format_emails**

在 `email_cli.py` 中新增（放在 `filter_emails` 之后）：

```python
def format_emails(emails):
    """Format list of (uid, msg) tuples as Markdown with reindexed headers."""
    if not emails:
        return "# 未读邮件 (0封)\n"
    parts = []
    for i, (uid, msg) in enumerate(emails, 1):
        parts.append(format_email(i, uid, msg))
    header = f"# 未读邮件 ({len(emails)}封)\n\n"
    return header + "\n\n---\n\n".join(parts)
```

Run: `python -m pytest tests/test_imap.py::TestFormatEmails -v`
Expected: ALL PASS

- [ ] **Step 7: 全量测试**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 8: 提交**

```bash
git add email_cli.py tests/test_imap.py
git commit -m "feat: add filter_emails and format_emails for client-side filtering"
```

---

### Task 3: 串联 cmd_fetch + 新增 CLI 参数

**Files:**
- Modify: `email_cli.py:353-356`（`cmd_fetch`）
- Modify: `email_cli.py:423-426`（argparse fetch 子命令）

- [ ] **Step 1: 写 cmd_fetch 集成测试**

在 `tests/test_imap.py` 末尾新增：

```python
class TestCmdFetchWithFilters:
    def test_days_and_since_mutually_exclusive(self):
        from email_cli import main
        import subprocess
        result = subprocess.run(
            ["python", "email_cli.py", "fetch", "--days", "7", "--since", "2026-05-01"],
            capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), "..")
        )
        assert result.returncode != 0
```

Run: `python -m pytest tests/test_imap.py::TestCmdFetchWithFilters -v`
Expected: FAIL（参数尚未定义）

- [ ] **Step 2: 更新 argparse fetch 参数**

将 `email_cli.py` 中 fetch 子命令定义（约第 423 行）改为：

```python
    p = sub.add_parser("fetch", help="Fetch unread emails")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--folder", default="INBOX")
    p.add_argument("--since", default=None, help="Start date inclusive (YYYY-MM-DD)")
    p.add_argument("--before", default=None, help="End date exclusive (YYYY-MM-DD)")
    p.add_argument("--days", type=int, default=None, help="Last N days")
    p.add_argument("--from", dest="from_addr", default=None, help="Sender substring match")
    p.add_argument("--subject", default=None, help="Subject substring match")
    p.set_defaults(func=cmd_fetch)
```

- [ ] **Step 3: 重写 cmd_fetch**

将 `cmd_fetch`（约第 353 行）改为：

```python
def cmd_fetch(args):
    import datetime

    since = args.since
    if args.days is not None:
        if since:
            print("Error: --days and --since cannot be used together", file=sys.stderr)
            sys.exit(1)
        since = (datetime.date.today() - datetime.timedelta(days=args.days)).isoformat()

    config = get_config()
    emails = asyncio.run(fetch_emails(config, limit=args.limit, folder=args.folder))
    filtered = filter_emails(emails, since=since, before=args.before,
                             from_addr=args.from_addr, subject=args.subject)
    print(format_emails(filtered))
```

- [ ] **Step 4: 运行全量测试**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 5: 提交**

```bash
git add email_cli.py tests/test_imap.py
git commit -m "feat: wire filter params into cmd_fetch with --days/--since/--before/--from/--subject"
```

---

### Task 4: 更新 SKILL.md 映射指南

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: 在 SKILL.md "查看未读邮件"部分的 fetch 命令后新增筛选指南**

在 `SKILL.md` 第 39 行（`python ... fetch [--limit 10] [--folder INBOX]`）之后，插入筛选说明：

```markdown
**筛选邮件**

支持通过自然语言按日期、发件人、主题筛选。翻译规则：

| 用户说 | 参数 |
|--------|------|
| "最近 N 天的邮件" | `--days N` |
| "5月1日以来的邮件" | `--since 2026-05-01` |
| "5月1日到5日的邮件" | `--since 2026-05-01 --before 2026-05-06` |
| "张三发的邮件" | `--from 张三` |
| "关于报告的邮件" | `--subject 报告` |
| 组合使用 | 参数自由组合，如 `--days 7 --from 张三 --subject 报告` |

示例：
```bash
python ~/.claude/skills/email-assistant/email_cli.py fetch --days 7
python ~/.claude/skills/email-assistant/email_cli.py fetch --since 2026-05-01 --from 张三
```
```

- [ ] **Step 2: 提交**

```bash
git add SKILL.md
git commit -m "docs: add filtering guide to SKILL.md"
```

---

### Task 5: 更新 README 项目进度

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 在已完成列表追加条目**

在 `README.md` 已完成部分末尾添加：

```markdown
- **2026-05-09** 邮件筛选：`fetch` 新增 `--since`/`--before`/`--days`/`--from`/`--subject` 客户端过滤，SKILL.md 新增自然语言映射指南
```

从待办中移除"按范围/日期筛选邮件"。

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs: update README with filtering progress"
```

---

## Verification

```bash
python -m pytest tests/ -v
```

全部测试通过后，手动验证 CLI：

```bash
python email_cli.py fetch --days 7
python email_cli.py fetch --since 2026-05-01 --from test
```
