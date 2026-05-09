# Email Assistant

通过 IMAP/SMTP 连接邮箱，支持查看、回复、转发、发送和归档邮件。作为 AI 编程工具的技能运行，用自然语言操作邮件。

## 安装

```bash
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env` 填入邮箱地址和授权码：

```
QQ_MAIL_USER=你的QQ邮箱@qq.com
QQ_MAIL_APP_PASSWORD=你的授权码
```

## 配置技能

### Claude Code

```bash
mkdir -p ~/.claude/skills/email-assistant
cp SKILL.md email_cli.py requirements.txt .env.example ~/.claude/skills/email-assistant/
cp -r tests/ ~/.claude/skills/email-assistant/
cp .env ~/.claude/skills/email-assistant/
pip install -r ~/.claude/skills/email-assistant/requirements.txt
```

### 其他工具

将 `SKILL.md`、`email_cli.py`、`requirements.txt`、`.env.example`、`tests/` 复制到对应工具的技能/指令目录下即可。

## 使用

在对话中直接说：

```
看看有什么新邮件
回复第1封，告诉他周三没问题
转发第2封给 alice@example.com
把通知邮件归档
标记已读 4、6-10
```

## 授权码获取

各邮箱服务商获取 SMTP/IMAP 授权码的步骤：

### QQ 邮箱

登录 QQ 邮箱 → **设置** → **账号与安全** → **安全设置** → **POP3/IMAP/SMTP/Exchange/CardDAV 服务** → **生成授权码**

> 授权码为 16 位字母，不是 QQ 密码。生成后只显示一次，请妥善保存。

## 配置项

| 环境变量 | 必填 | 默认值 | 说明 |
|---------|------|--------|------|
| `QQ_MAIL_USER` | 是 | — | QQ 邮箱地址 |
| `QQ_MAIL_APP_PASSWORD` | 是 | — | IMAP/SMTP 授权码 |
| `QQ_MAIL_IMAP_HOST` | 否 | `imap.qq.com` | IMAP 服务器 |
| `QQ_MAIL_IMAP_PORT` | 否 | `993` | IMAP 端口 |
| `QQ_MAIL_SMTP_HOST` | 否 | `smtp.qq.com` | SMTP 服务器 |
| `QQ_MAIL_SMTP_PORT` | 否 | `465` | SMTP 端口 |
| `QQ_MAIL_ARCHIVE_FOLDER` | 否 | `Archives` | 归档目标文件夹 |

可通过环境变量或项目根目录 `.env` 文件配置。环境变量优先级高于 `.env` 文件。

## 项目结构

```
├── SKILL.md                  # 技能定义（路径指向 ~/.claude/skills/email-assistant/）
├── email_cli.py              # CLI 入口和核心逻辑
├── requirements.txt          # Python 依赖
├── requirements-dev.txt      # 开发依赖（测试）
├── .env.example              # 配置模板
├── tests/                    # 测试
├── docker/                   # 开发环境
└── docs/                     # 文档
```

## 项目进度

**最近更新：2026-05-09**

### 已完成

- **2026-05-09** 目录重构：将 `skills/email-assistant/` 扁平化到项目根目录，去除 `{{PROJECT_DIR}}` 占位符，安装改为显式文件列表
- **2026-05-09** 邮件分类简化：删除"待处理"分类，只保留"需要关注"和"订阅/通知"两级
- **2026-05-09** 标记已读功能：fetch 改用 `BODY.PEEK[]` 避免自动标记，新增 `mark-read` 命令，汇报后询问标记、回复/转发后自动标记
- **2026-05-09** 修复 5 个失败测试：`TestFetchEmails` mock 从 `uid` 改为 `search`、fetch 数据格式从 tuple 改为 bytes；`TestGetConfig` 隔离 `_load_dotenv` 防止 `.env` 回填
- **2026-05-09** 邮件筛选：`fetch` 新增 `--since`/`--before`/`--days`/`--from`/`--subject` 客户端过滤，SKILL.md 新增自然语言映射指南

### 待办

- 支持多邮箱账户
