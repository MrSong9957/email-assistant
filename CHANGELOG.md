# Changelog

## Unreleased

### Added
- Web link in email details — opens Gmail/QQ webmail
- Multi-account support (`--account` / `-a` flag, `MAIL_ACCOUNTS` env var)
- Email filtering by date/sender/subject (`--since`, `--before`, `--days`, `--from`, `--subject`)
- Mark as read (`mark-read` command, post-review prompt, auto-mark after reply/forward)
- Post-send verification (sent folder table after reply/forward/send)
- Newsletter detection and article extraction
- Bilingual email display (Chinese summary + foreign language body)
- HTML email forwarding (preserves original HTML formatting)
- Attachment info display (filename + size)
- Docker development environment
- Cross-platform install scripts (`install.sh`, `install.ps1`)
- Multi-tool support (Claude Code, Codex CLI, OpenCode, Cursor)

### Fixed
- Load `.env` from both skill dir and project root as fallback
- Date input validation with clear error messages
- `BODY.PEEK[]` to avoid auto-marking emails as read on fetch
