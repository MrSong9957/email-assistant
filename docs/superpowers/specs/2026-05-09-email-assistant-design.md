# QQ 邮箱助手 Skill 设计

## Context

用户需要一个在 Claude Code 等 AI 编程工具中使用的邮件助手 Skill。通过 IMAP 连接 QQ 邮箱拉取未读邮件，由 AI 摘要分类后在终端展示；用户口头指示回复/转发/归档，助手通过 SMTP 执行。

## 架构方案：单文件 CLI + SKILL.md

```
email-assistant/
├── SKILL.md              # Skill 指令（告诉 AI 如何使用工具）
└── email_cli.py          # Python CLI，子命令模式
```

**职责分离：**
- Python：无状态管道工具（IMAP/SMTP 操作，输出 Markdown）
- AI：有状态大脑（记忆邮件上下文、理解意图、组织回复内容）
- 通信方式：stdin/stdout + 命令行参数

### 数据流

```
用户 → AI（匹配 Skill）→ python email_cli.py fetch → IMAP 拉取 → Markdown 输出 → AI 展示给用户
用户口头指示 → AI 组织内容 → python email_cli.py reply --uid X --body "..." → SMTP 发送
```

## CLI 命令设计

### fetch — 拉取未读邮件

```bash
python email_cli.py fetch [--limit 10] [--folder INBOX]
```

输出 Markdown：

```markdown
# 未读邮件 (3封)

---

## [1] UID: 12345 | 2026-05-09 14:30
**From:** 张三 <zhangsan@example.com>
**Subject:** 关于项目进度
**Attachments:** report.pdf (2.1MB)

邮件正文内容...

---

## [2] UID: 12346 | 2026-05-09 15:00
...
```

### reply — 回复邮件

```bash
python email_cli.py reply --uid <UID> --body "回复内容" [--html]
```

根据原邮件 Message-ID 生成 `In-Reply-To` 和 `References` 头。

### forward — 转发邮件

```bash
python email_cli.py forward --uid <UID> --to "recipient@example.com" [--note "转发备注"]
```

### send — 发新邮件

```bash
python email_cli.py send --to "recipient@example.com" --subject "主题" --body "正文"
```

### archive — 归档邮件

```bash
python email_cli.py archive --uid <UID>  # 支持多个 UID: --uid 123 124 125
```

将邮件从 INBOX 移动到 `Archives` 文件夹。

### folders — 列出文件夹

```bash
python email_cli.py folders
```

列出所有可用 IMAP 文件夹。

## 环境变量

```bash
# 必需
QQ_MAIL_USER=your@qq.com
QQ_MAIL_APP_PASSWORD=xxxxxxxxxxxx

# 可选（有默认值）
QQ_MAIL_IMAP_HOST=imap.qq.com
QQ_MAIL_IMAP_PORT=993
QQ_MAIL_SMTP_HOST=smtp.qq.com
QQ_MAIL_SMTP_PORT=465
QQ_MAIL_ARCHIVE_FOLDER=Archives
```

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| 凭证缺失/错误 | stderr + 退出码 1 |
| 网络连接失败 | stderr + 退出码 2 |
| UID 不存在 | stderr + 退出码 3 |
| SMTP 发送失败 | stderr + 退出码 4 |

AI 读取 stderr 和退出码后用自然语言告知用户。

## 依赖

- `aioimaplib` — asyncio IMAP 客户端
- `aiosmtplib` — asyncio SMTP 客户端

## SKILL.md 要点

- 启动时检查环境变量，缺失则引导用户配置
- 明确 fetch → 展示 → 用户指示 → 执行 → 确认的流程
- 发送/回复/转发前必须向用户展示内容并确认
- 不自动批量操作
- 包含 2-3 个典型对话示例
- 附件只列文件名和大小，不下载内容

## 附件处理

忽略附件内容，仅在 Markdown 输出中列出文件名和大小。

## Python 版本兼容

容器内为 Python 3.11.2，代码需兼容 3.11+（不使用 3.13+ 专属特性）。
