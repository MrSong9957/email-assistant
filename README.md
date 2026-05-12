# Email Assistant for Claude Code

用自然语言管理邮箱 — 通过 IMAP/SMTP 连接 QQ 邮箱和 Gmail，在 AI 对话中直接查看、回复、转发和归档邮件。

English | 中文

## 特性

- **自然语言操作** — 说"看看有什么新邮件"即可，无需记忆命令
- **AI 智能分类** — 自动将邮件分为「需要关注」和「订阅/通知」，表格化汇报
- **Newsletter 拆解** — 自动识别并提取 Nature Briefing、AI Weekly 等订阅邮件中的文章
- **多邮箱账户** — 同时支持 QQ 邮箱和 Gmail，`--account` 一键切换
- **完整邮件操作** — 查看、回复、转发、发新邮件、归档、标记已读
- **HTML 转发** — 保留原始邮件的 HTML 格式，非纯文本降级
- **发送验证** — 回复/转发/发送后自动验证邮件已进入发件箱
- **双语展示** — 外语邮件发送前展示中文大意 + 外语正文

## 架构

```
用户口头指令 → Claude Code → SKILL.md → email_cli.py → IMAP/SMTP → 邮箱
                                                              ↓
                                                         AI 摘要 + 分类 → 终端展示
```

## 快速开始

**1. 安装**

```bash
# 一键安装到 Claude Code 技能目录
chmod +x install.sh && ./install.sh

# 或 Windows PowerShell
.\install.ps1
```

**2. 配置**

复制 `.env.example` 为 `.env`，填入邮箱和授权码：

```bash
MAIL_ACCOUNTS=qq,gmail
QQ_MAIL_USER=your@qq.com
QQ_MAIL_APP_PASSWORD=你的授权码
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=你的应用专用密码
```

> QQ 邮箱：设置 → 账号与安全 → 安全设置 → POP3/IMAP/SMTP → 生成授权码
> Gmail：Google 账号 → 安全性 → 两步验证 → 应用专用密码

**3. 使用**

在 Claude Code 对话中直接说：

```
看看有什么新邮件
回复第1封，告诉他周三没问题
转发第2封给 alice@example.com
把通知邮件归档
```

## 使用效果

### 查看未读邮件

```
用户：看看有什么新邮件

📬 邮件汇报 — 共 10 封未读
🔴 需要关注 2 封 · ⚪ 订阅/通知 8 封

┌─────┬──────┬────────────┬──────────────────────┬────────────────────────────────────────┐
│ #   │ 类别 │ 发件人     │ 主题                 │ 摘要                                   │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  1  │  ⚪  │ AI Weekly  │ PE built AI's new…  │ 私募股权构建 AI 新分发渠道的新闻摘要   │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  6  │  🔴  │ GitHub     │ 第三方应用已添加     │ 安全告警：有应用获得账号访问权限       │
└─────┴──────┴────────────┴──────────────────────┴────────────────────────────────────────┘

需要查看详情或操作哪封？
> 是否标记已读？可以"全部标记"或指定序号，未标记的下次仍会出现。
```

### Newsletter 拆解

```
用户：查看Nature的内容

第 2 封 (2026.05.05) | Nature Briefing
主题：Who needs testosterone therapy?

┌──────────────────────┬──────────────────────────────────────────────────────────────┐
│ 文章                 │ 摘要                                                         │
├──────────────────────┼──────────────────────────────────────────────────────────────┤
│ 🏛️ 伊朗科学中心遭… │ 美以轰炸损毁伊朗多所大学和医院，研究者警告攻击大学成为新常态 │
├──────────────────────┼──────────────────────────────────────────────────────────────┤
│ 🧬 AI 简化蛋白质字… │ 用生成式 AI 设计只需 19 种氨基酸即可运转的细菌核糖体         │
├──────────────────────┼──────────────────────────────────────────────────────────────┤
│ ☢️ 科学家重返福岛   │ 福岛核灾 15 年后，浪江町建设 F-REI 研究所                    │
└──────────────────────┴──────────────────────────────────────────────────────────────┘
```

### 回复与发送验证

```
用户：回复第7封，告诉他 SMTP 连接正常

> Re: Gmail SMTP 测试
> 收到，SMTP 连接正常。这是一封测试回复。

确认发送吗？

用户：确认

✅ 发送成功，已验证

📬 已发送邮件 — 最近 5 封

┌─────┬──────────────────────┬──────────────────┬──────────────────────────────────────────┐
│ #   │ 收件人               │ 主题             │ 摘要                                     │
├─────┼──────────────────────┼──────────────────┼──────────────────────────────────────────┤
│  1  │ sry***58@gmail.com   │ Re: Gmail SMTP…  │ SMTP 连接正常，测试回复                   │
└─────┴──────────────────────┴──────────────────┴──────────────────────────────────────────┘
```

更多使用场景（双语邮件、归档、标记已读等）请查看 [SKILL.md](SKILL.md)。

## 配置

| 环境变量 | 必填 | 默认值 | 说明 |
|---------|------|--------|------|
| `MAIL_ACCOUNTS` | 是 | — | 账户列表，逗号分隔（如 `qq,gmail`） |
| `QQ_MAIL_USER` | 是 | — | QQ 邮箱地址 |
| `QQ_MAIL_APP_PASSWORD` | 是 | — | QQ 邮箱授权码 |
| `GMAIL_USER` | 是* | — | Gmail 邮箱地址 |
| `GMAIL_APP_PASSWORD` | 是* | — | Gmail 应用专用密码 |
| `*_IMAP_HOST` | 否 | 见下表 | IMAP 服务器 |
| `*_IMAP_PORT` | 否 | `993` | IMAP 端口 |
| `*_SMTP_HOST` | 否 | 见下表 | SMTP 服务器 |
| `*_SMTP_PORT` | 否 | `465` | SMTP 端口 |

> *仅当 `MAIL_ACCOUNTS` 包含 `gmail` 时必填

Provider 默认值：

| Provider | IMAP | SMTP | 归档文件夹 | 发件箱 |
|----------|------|------|-----------|--------|
| QQ | imap.qq.com | smtp.qq.com | Archives | Sent Messages |
| Gmail | imap.gmail.com | smtp.gmail.com | [Gmail]/All Mail | [Gmail]/Sent Mail |

## 安装方式

### 一键脚本

```bash
# Claude Code（默认）
./install.sh

# 其他工具
./install.sh --tool codex        # Codex CLI
./install.sh --tool opencode     # OpenCode
./install.sh --project           # 项目级安装
```

Windows PowerShell：

```powershell
.\install.ps1                         # Claude Code
.\install.ps1 -Tool codex             # Codex CLI
.\install.ps1 -Project                # 项目级安装
```

### 手动安装

1. 创建技能目录：`mkdir -p ~/.claude/skills/email-assistant`
2. 复制文件：`cp SKILL.md email_cli.py requirements.txt .env.example ~/.claude/skills/email-assistant/`
3. 安装依赖：`pip install -r ~/.claude/skills/email-assistant/requirements.txt`
4. 配置凭证：复制 `.env.example` 为 `.env`，填入邮箱和授权码

### 工具目录对照

| 工具 | 全局目录 | 项目级目录 |
|------|---------|-----------|
| Claude Code | `~/.claude/skills/email-assistant/` | `.claude/skills/email-assistant/` |
| Codex CLI | `~/.agents/skills/email-assistant/` | `.agents/skills/email-assistant/` |
| Cursor | — | `.cursor/skills/email-assistant/` |
| OpenCode | `~/.config/opencode/skills/email-assistant/` | 项目内 |

## 开发

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest tests/ -v

# Docker 开发环境
docker compose -f docker/docker-compose.yml up
```

## 项目结构

```
├── SKILL.md                  # 技能定义（Claude Code / Codex CLI 的入口）
├── email_cli.py              # CLI 核心逻辑（IMAP/SMTP/格式化）
├── requirements.txt          # 运行依赖
├── requirements-dev.txt      # 开发依赖
├── .env.example              # 配置模板
├── install.sh / install.ps1  # 一键安装脚本
├── tests/                    # 测试（76 个用例）
├── docker/                   # 开发环境配置
└── docs/                     # 文档
```

## License

[MIT](LICENSE)
