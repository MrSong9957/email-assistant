# Email Assistant — AI-Powered Email in Your Terminal

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) / [Codex CLI](https://github.com/openai/codex) / [OpenCode](https://github.com/opencode-ai/opencode) **Skill** that lets you manage your inbox with natural language. Connect QQ Mail and Gmail via IMAP/SMTP — check, reply, forward, and archive emails without leaving your AI conversation.

Just install the skill with a natural language command in your AI tool, then configure your email authorization code in `.env` — that's all you need to get started.

[中文文档](README.zh-CN.md)

## One-Click Install

In Claude Code, just say:

```
Install the email-assistant skill: git clone https://github.com/MrSong9957/email-assistant.git && cd email-assistant && ./install.sh
```

Or simply:

```
Install this Skill: https://github.com/MrSong9957/email-assistant
```

That's it. The skill is ready to use.

## Configure

Copy `.env.example` to `.env` and fill in your email credentials:

```bash
MAIL_ACCOUNTS=qq,gmail,163
QQ_MAIL_USER=your@qq.com
QQ_MAIL_APP_PASSWORD=your-authorization-code
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=your-app-password
MAIL163_USER=your@163.com
MAIL163_APP_PASSWORD=your-authorization-code
```

> **Get your authorization code / app password:**
>
> | Provider | Status | Setup |
> |----------|--------|-------|
> | QQ Mail | ✅ Supported | [mail.qq.com](https://mail.qq.com) → Settings → Account & Security → Security Settings → POP3/IMAP/SMTP/Exchange/CardDAV → Generate authorization code |
> | Gmail | ✅ Supported | [App passwords](https://myaccount.google.com/apppasswords) |
> | 163 Mail | ✅ Supported | [mail.163.com](https://mail.163.com) → Settings → POP3/SMTP/IMAP |
> | Outlook | Planned* | [outlook.live.com](https://outlook.live.com) — *can use [email forwarding](https://outlook.live.com/mail/0/options/mail/rules) as fallback* |
> | iCloud Mail | Planned | [appleid.apple.com](https://appleid.apple.com) |
> | Aliyun Mail | Planned | [mail.aliyun.com](https://mail.aliyun.com) |
> | 139 Mail | ✅ Supported | [mail.10086.cn](https://mail.10086.cn) → 设置 → 常用设置 → 获取授权码 |
> | Sina Mail | Planned | [mail.sina.com](https://mail.sina.com) |
> | ProtonMail | Planned | [proton.me](https://proton.me) (requires Bridge) |
> | Zoho Mail | Planned | [zoho.com/mail](https://www.zoho.com/mail) |

## Usage

Say it naturally in your AI conversation:

```
Check my new emails
Reply to #1, tell him Wednesday works
Forward #2 to alice@example.com
Archive the notification emails
```

## Demos

### Check Unread Emails

```
You: Check my new emails

📬 Email Report — 10 unread
🔴 Needs attention 2 · ⚪ Subscriptions 8

┌─────┬──────┬────────────┬──────────────────────┬────────────────────────────────────────┐
│ #   │ Cat. │ Sender     │ Subject              │ Summary                                │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  1  │  ⚪  │ AI Weekly  │ PE built AI's new…  │ PE firms building AI distribution channels │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  2  │  ⚪  │ Nature     │ Who needs testoste… │ Testosterone therapy research progress  │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  3  │  ⚪  │ PyCoder's  │ marimo pair, Findi… │ marimo pairing, LLM bug-finding tools  │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  4  │  ⚪  │ JD.com     │ Order confirmed      │ Order confirmed, track delivery        │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  5  │  ⚪  │ Nature     │ Digital distractio… │ Digital-age attention management study │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  6  │  🔴  │ GitHub     │ Third-party app added│ Security alert: app got account access │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  7  │  ⚪  │ PyCharm    │ Python Unplugged…   │ Community livestream event highlights  │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  8  │  ⚪  │ AI Weekly  │ Anthropic updates    │ Anthropic's biggest 2026 release week  │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  9  │  🔴  │ GitHub     │ Personal token added │ Security alert: classic PAT added      │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│ 10  │  ⚪  │ Nature     │ Detailed map of uni… │ High-res universe map, best sci photos │
└─────┴──────┴────────────┴──────────────────────┴────────────────────────────────────────┘

Which one would you like to view or act on?
> Mark as read? "Mark all" or specify a number. Unmarked ones will appear again next time.
```

### View Email Details

```
You: Show me the Nature newsletter

Email #2 (2026.05.05) | Nature Briefing
Subject: Who needs testosterone therapy?

┌──────────────────────┬──────────────────────────────────────────────────────────────┐
│ Article              │ Summary                                                      │
├──────────────────────┼──────────────────────────────────────────────────────────────┤
│ 🏛️ Iranian science… │ US-Israeli bombings damaged Iranian universities & hospitals │
├──────────────────────┼──────────────────────────────────────────────────────────────┤
│ 🧬 AI simplifies…   │ Generative AI designs ribosomes needing only 19 amino acids  │
├──────────────────────┼──────────────────────────────────────────────────────────────┤
│ ☢️ Scientists retu… │ Fukushima 15 years on, Namie builds F-REI research center   │
└──────────────────────┴──────────────────────────────────────────────────────────────┘
```

### Read Full Article

```
You: Show me the full article about the Iranian science center bombing

Email #2 — Iranian science center bombed (2026.05.05)

US and Israeli airstrikes damaged several universities and hospitals in Iran. Nature interviewed researchers:

- Affected institutions: Tehran's Shefa Neuroscience Center is one confirmed
  damaged facility, led by neuroscientist Ali Gorji (based in Germany),
  who supervises PhD students there.
- Researcher voices: Gorji stated: "If attacking universities becomes
  normalized, it could happen in any future foolish war. That mindset is
  more destructive than attacking a single building."
- Official response: White House and Israeli military representatives told
  Nature they don't target civilian infrastructure, but did not explain
  why these institutions were bombed.

> Source: Nature | 8 min read

> 💡 `Mark 2 read` · `View #5 Nature` · `View all unread`
```

### Reply & Send Verification

```
You: Reply to #7, tell him SMTP is working

Sure, preparing your reply:

> Re: Gmail SMTP Test
>
> Received, SMTP connection is working. This is a test reply.

Confirm send?

You: Confirm

✅ Sent successfully, verified

📬 Sent Emails — Recent 5

┌─────┬──────────────────────┬──────────────────┬──────────────────────────────────────────┐
│ #   │ Recipient            │ Subject          │ Summary                                  │
├─────┼──────────────────────┼──────────────────┼──────────────────────────────────────────┤
│  1  │ sry***58@gmail.com   │ Re: Gmail SMTP…  │ SMTP working, test reply                  │
├─────┼──────────────────────┼──────────────────┼──────────────────────────────────────────┤
│  2  │ 7***7@qq.com         │ Fwd: Security…   │ Gmail security alert forwarded            │
├─────┼──────────────────────┼──────────────────┼──────────────────────────────────────────┤
│  3  │ 7***7@qq.com         │ Fwd: Order stat… │ JD.com order forwarded                    │
└─────┴──────────────────────┴──────────────────┴──────────────────────────────────────────┘

Reply appeared in Sent folder at #1. Send & verify flow complete.
> 💡 `Handle next email` · `View remaining unread`
```

### Compose & Send Verification

```
You: Send an English email to Dakang

📧 Email to be sent:

> **Chinese summary:**
> Hey Dakang, thanks for your lightning-fast response time. Reading a
> message within 48 hours is truly awe-inspiring. Next time we meet I must
> ask about your time management secrets.
>
> **Actual email (English):**
> Hey Dakang,
>
> Just wanted to take a moment to appreciate your absolutely breathtaking
> response time. The way you manage to read a message and still not reply
> for 48 hours is truly next-level. I aspire to that level of prioritization
> one day.
>
> Can't wait for our next hangout where I can watch you check your phone
> and put it back in your pocket. Truly inspiring stuff.
>
> Warmest regards,
> MrSong

Confirm send?

You: Send

✅ Sent successfully, verified

📬 Sent Emails — Recent 5

┌─────┬───────────────┬──────────────────────┬──────────────────────────────────────────────────────┐
│ #   │ Recipient     │ Subject              │ Summary                                              │
├─────┼───────────────┼──────────────────────┼──────────────────────────────────────────────────────┤
│  1  │ 7***7@qq.com  │ Just wanted to say…  │ Appreciating your response time, 48hr no-reply master│
├─────┼───────────────┼──────────────────────┼──────────────────────────────────────────────────────┤
│  2  │ 7***7@qq.com  │ How's it going       │ How's work? Enjoy the May Day holiday?              │
├─────┼───────────────┼──────────────────────┼──────────────────────────────────────────────────────┤
│  3  │ 7***7@qq.com  │ Weekend greetings    │ Hey Dakang, long time no see! Have a great weekend  │
├─────┼───────────────┼──────────────────────┼──────────────────────────────────────────────────────┤
│  4  │ 7***7@qq.com  │ Re-select folder test│ Testing re-select                                    │
├─────┼───────────────┼──────────────────────┼──────────────────────────────────────────────────────┤
│  5  │ 7***7@qq.com  │ Stability re-test    │ Confirming fix is stable                             │
└─────┴───────────────┴──────────────────────┴──────────────────────────────────────────────────────┘

English email appeared in Sent folder at #1. Bilingual display, send & verify flow complete.
> 💡 `Check unread emails` · `View email 1 details`
```

### Personas & Style Profiles

Email Assistant can adopt different **personas** when writing emails — pick from 4 presets (sarcastic, workplace, customer, romantic) and map them to specific recipients. Each persona shapes the tone and wording of your replies.

**Style profile** learns your personal writing patterns (catchphrases, slang, habits) from chat logs and blends them into emails. The **style toggle** controls whether the style profile is active for a given persona — formal personas like "workplace" and "customer" disable it by default to keep things professional.

Quick commands:
- `给 <收件人> 配 <人格名>` — map a persona to a recipient
- `查看人格列表` / `list-personas` — see all personas and mappings
- `set-persona <recipient> --style-profile on/off` — toggle style per persona

### Persona-Based Reply

```
You: Configure sarcastic persona for Dakang, send him an email

Dakang mapped to sarcastic persona. Style toggle: ✅ ON.

🎭 Sarcastic (recipient-specific) · Style ON

📧 Email to be sent:

> **Persona:** 🎭 Sarcastic (recipient-specific)
> **To:** 742890757@qq.com
> **Subject:** Long time no see (didn't miss you)
>
> Dakang,
>
> Is it possible you forgot I exist? A salted fish with zero dreams
> somehow still breathing — impressive, truly. I'm literally initiating
> contact with a salted fish. Numb.
> Anyway, keep being a salted fish. Nobody does shameless like you.
>
> — Someone with more dreams than you

Confirm send?
```

### Style Toggle Comparison

```
You: Configure workplace persona for Dakang, send him an email

🎭 Workplace (recipient-specific) · Style OFF

📧 Email to be sent:

> **Persona:** 🎭 Workplace (recipient-specific) · Style OFF
> **To:** 742890757@qq.com
> **Subject:** Project Update — Email Assistant Iteration Progress
>
> Dakang,
>
> Quick update on recent email assistant features:
>
> Completed:
> - Persona-based replies: 4 preset personas, auto-matched per recipient
> - Style profile: Extract personal writing patterns from chat logs
> - Style toggle: Per-persona control, auto-disabled for formal contexts
>
> Let me know if you have suggestions or need adjustments.
>
> Song

Confirm send?
```

### Persona Management

```
You: List all personas

  Sarcastic(sarcastic)        Style: ✅
  Workplace(workplace)        Style: ❌
  Customer(customer)          Style: ❌
  Romantic(romantic)          Style: ✅
Default: workplace
Recipient mapping:
  742890757@qq.com → sarcastic
```

More scenarios (archiving, mark as read, etc.) in [SKILL.md](SKILL.md).

## Features

- **Natural language** — Say "check my new emails", no commands to remember
- **AI-powered categorization** — Auto-sorts into "needs attention" vs. "subscriptions/notifications"
- **Newsletter digest** — Extracts articles from Nature Briefing, AI Weekly, etc.
- **Multiple accounts** — QQ Mail and Gmail, switch with `--account`
- **Full email operations** — Check, reply, forward, compose, archive, mark as read
- **HTML forwarding** — Preserves original HTML formatting
- **Send verification** — Auto-verifies sent mail appears in Sent folder
- **Bilingual display** — Shows Chinese summary + foreign-language body before sending
- **Personas** — 4 preset personas (sarcastic / workplace / customer / romantic), per-recipient mapping
- **Style profile** — Learns your writing style from chat logs, auto-applies to emails
- **Style toggle** — Per-persona switch to control whether style profile is used (formal personas block memes)

## Traditional Install

<details>
<summary>One-click script</summary>

```bash
# Clone and install
git clone https://github.com/MrSong9957/email-assistant.git
cd email-assistant
chmod +x install.sh && ./install.sh

# Other tools
./install.sh --tool codex        # Codex CLI
./install.sh --tool opencode     # OpenCode
./install.sh --project           # Project-level install
```

Windows PowerShell:

```powershell
.\install.ps1                         # Claude Code
.\install.ps1 -Tool codex             # Codex CLI
.\install.ps1 -Project                # Project-level install
```

</details>

<details>
<summary>Manual install</summary>

1. Create skill directory: `mkdir -p ~/.claude/skills/email-assistant`
2. Copy files: `cp SKILL.md email_cli.py requirements.txt .env.example ~/.claude/skills/email-assistant/`
3. Install dependencies: `pip install -r ~/.claude/skills/email-assistant/requirements.txt`
4. Configure: copy `.env.example` to `.env` and fill in credentials

</details>

<details>
<summary>Tool directory reference</summary>

| Tool | Global | Project |
|------|--------|---------|
| Claude Code | `~/.claude/skills/email-assistant/` | `.claude/skills/email-assistant/` |
| Codex CLI | `~/.agents/skills/email-assistant/` | `.agents/skills/email-assistant/` |
| Cursor | — | `.cursor/skills/email-assistant/` |
| OpenCode | `~/.config/opencode/skills/email-assistant/` | project root |

</details>

<details>
<summary>Configuration reference</summary>

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MAIL_ACCOUNTS` | Yes | — | Comma-separated account list (e.g. `qq,gmail`) |
| `QQ_MAIL_USER` | Yes | — | QQ Mail address |
| `QQ_MAIL_APP_PASSWORD` | Yes | — | QQ Mail authorization code |
| `GMAIL_USER` | Yes* | — | Gmail address |
| `GMAIL_APP_PASSWORD` | Yes* | — | Gmail app password |
| `MAIL163_USER` | Yes* | — | 163 Mail address |
| `MAIL163_APP_PASSWORD` | Yes* | — | 163 Mail authorization code |
| `*_IMAP_HOST` | No | see below | IMAP server |
| `*_IMAP_PORT` | No | `993` | IMAP port |
| `*_SMTP_HOST` | No | see below | SMTP server |
| `*_SMTP_PORT` | No | `465` | SMTP port |

> *Required only when `MAIL_ACCOUNTS` includes the corresponding provider (gmail, 163)

| Provider | IMAP | SMTP | Archive folder | Sent folder |
|----------|------|------|----------------|-------------|
| QQ | imap.qq.com | smtp.qq.com | Archives | Sent Messages |
| Gmail | imap.gmail.com | smtp.gmail.com | [Gmail]/All Mail | [Gmail]/Sent Mail |
| 163 | imap.163.com | smtp.163.com | Archives | Sent Messages |

</details>

## Development

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
docker compose -f docker/docker-compose.yml up
```

## License

[MIT](LICENSE)
