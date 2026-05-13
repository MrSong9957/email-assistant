# Email Assistant — 用自然语言管理邮箱

一个 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) / [Codex CLI](https://github.com/openai/codex) / [OpenCode](https://github.com/opencode-ai/opencode) **技能（Skill）**，用自然语言管理邮箱。通过 IMAP/SMTP 连接 QQ 邮箱和 Gmail，在 AI 对话中直接查看、回复、转发和归档邮件。

[English](README.md)

## 一键安装

在 Claude Code 中直接说：

```
请帮我安装 email-assistant 技能：git clone https://github.com/MrSong9957/email-assistant.git && cd email-assistant && ./install.sh
```

或者：

```
请帮我安装这个 Skill：https://github.com/MrSong9957/email-assistant
```

安装完成，直接可用。

## 配置

复制 `.env.example` 为 `.env`，填入邮箱和授权码：

```bash
MAIL_ACCOUNTS=qq,gmail,163
QQ_MAIL_USER=your@qq.com
QQ_MAIL_APP_PASSWORD=你的授权码
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=你的应用专用密码
MAIL163_USER=your@163.com
MAIL163_APP_PASSWORD=你的授权码
```

> **获取授权码 / 应用专用密码：**
>
> | 邮箱 | 状态 | 设置入口 |
> |------|------|----------|
> | QQ 邮箱 | ✅ 已支持 | [mail.qq.com](https://mail.qq.com) → 设置 → 账号与安全 → 安全设置 → POP3/IMAP/SMTP/Exchange/CardDAV 服务（已开启） → 生成授权码 |
> | Gmail | ✅ 已支持 | [应用专用密码](https://myaccount.google.com/apppasswords) |
> | 163 邮箱 | ✅ 已支持 | [mail.163.com](https://mail.163.com) → 设置 → POP3/SMTP/IMAP |
> | Outlook | 计划中* | [outlook.live.com](https://outlook.live.com) — *可通过 [邮件转发](https://outlook.live.com/mail/0/options/mail/rules) 作为替代方案* |
> | iCloud 邮箱 | 计划中 | [appleid.apple.com](https://appleid.apple.com) |
> | 阿里邮箱 | 计划中 | [mail.aliyun.com](https://mail.aliyun.com) |
> | 139 邮箱 | ✅ 已支持 | [mail.10086.cn](https://mail.10086.cn) → 设置 → 常用设置 → 获取授权码 |
> | 新浪邮箱 | 计划中 | [mail.sina.com](https://mail.sina.com) |
> | ProtonMail | 计划中 | [proton.me](https://proton.me)（需 Bridge） |
> | Zoho 邮箱 | 计划中 | [zoho.com/mail](https://www.zoho.com/mail) |

## 使用

在 AI 对话中直接说：

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
│  2  │  ⚪  │ Nature     │ Who needs testoste… │ 睾酮疗法相关研究进展                   │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  3  │  ⚪  │ PyCoder's  │ marimo pair, Findi… │ marimo 配对、LLM 找 Bug 等工具新闻     │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  4  │  ⚪  │ 京东       │ 京东已收到您的订单   │ 订单已确认，可关注物流                 │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  5  │  ⚪  │ Nature     │ Digital distractio… │ 数字时代注意力管理与恢复研究           │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  6  │  🔴  │ GitHub     │ 第三方应用已添加     │ 安全告警：有应用获得账号访问权限       │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  7  │  ⚪  │ PyCharm    │ Python Unplugged…   │ 社区直播活动要点回顾                   │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  8  │  ⚪  │ AI Weekly  │ Anthropic 本周更新   │ Anthropic 2026 年最大发布周摘要        │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│  9  │  🔴  │ GitHub     │ 个人令牌已添加       │ 安全告警：有经典 PAT 被添加到账号      │
├─────┼──────┼────────────┼──────────────────────┼────────────────────────────────────────┤
│ 10  │  ⚪  │ Nature     │ 宇宙详细地图         │ 宇宙高分辨率地图及本月最佳科学图片     │
└─────┴──────┴────────────┴──────────────────────┴────────────────────────────────────────┘

需要查看详情或操作哪封？
> 是否标记已读？可以"全部标记"或指定序号，未标记的下次仍会出现。
```

### 查看邮件详情

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

### 查看具体新闻

```
用户：查看伊朗科学中心遭轰炸具体内容

第 2 封 — 伊朗科学中心遭轰炸 (2026.05.05)

美国和以色列的轰炸损毁了伊朗部分大学和医院。Nature 采访了相关研究者：

- 受损机构：德黑兰 Shefa 神经科学研究中心是已知受损机构之一。该中心由在
  德国任职的神经科学家 Ali Gorji 负责指导博士生。
- 研究者声音：Gorji 表示："如果攻击大学成为一种常态，那么在任何未来的
  愚蠢战争中都可能发生。这种想法比攻击单栋建筑更具破坏性。"
- 官方回应：白宫发言人和以色列军方代表分别向 Nature 表示，他们不以民用
  基础设施为目标，但未解释为何这些机构遭到轰炸。

> 来源：Nature | 8 min read

> 💡 `标记 2 已读` · `查看第 5 封 Nature` · `查看全部未读`
```

### 回复邮件与发送验证

```
用户：回复第7封，告诉他 SMTP 连接正常

好的，准备回复。邮件内容如下：

> Re: Gmail SMTP 测试
>
> 收到，SMTP 连接正常。这是一封测试回复。

确认发送吗？

用户：确认

✅ 发送成功，已验证

📬 已发送邮件 — 最近 5 封

┌─────┬──────────────────────┬──────────────────┬──────────────────────────────────────────┐
│ #   │ 收件人               │ 主题             │ 摘要                                     │
├─────┼──────────────────────┼──────────────────┼──────────────────────────────────────────┤
│  1  │ sry***58@gmail.com   │ Re: Gmail SMTP…  │ SMTP 连接正常，测试回复                   │
├─────┼──────────────────────┼──────────────────┼──────────────────────────────────────────┤
│  2  │ 7***7@qq.com         │ Fwd: 安全提醒    │ Gmail 安全提醒转发                        │
├─────┼──────────────────────┼──────────────────┼──────────────────────────────────────────┤
│  3  │ 7***7@qq.com         │ Fwd: 订单状态    │ 京东订单转发                              │
└─────┴──────────────────────┴──────────────────┴──────────────────────────────────────────┘

回复邮件已出现在发件箱第 1 位，发送、验证全流程通过。
> 💡 `处理下一封` · `查看剩余未读`
```

### 发新邮件与发送验证

```
用户：给达康发一封英文邮件

📧 即将发送的内容：

> **中文大意：**
> 达康你好，谢谢你回复我消息的闪电般的速度。真的，你能在 48 小时内
> 看完一条消息，这种效率简直让人叹为观止。下次见面我一定要请教你
> 的时间管理秘诀。
>
> **实际发送（英文）：**
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

确认发送吗？

用户：发送

✅ 发送成功，已验证

📬 已发送邮件 — 最近 5 封

┌─────┬───────────────┬──────────────────────┬──────────────────────────────────────────────────────┐
│ #   │ 收件人        │ 主题                 │ 摘要                                                 │
├─────┼───────────────┼──────────────────────┼──────────────────────────────────────────────────────┤
│  1  │ 7***7@qq.com  │ Just wanted to say…  │ 欣赏你惊人的回复速度，看完消息48小时不回真是大师级   │
├─────┼───────────────┼──────────────────────┼──────────────────────────────────────────────────────┤
│  2  │ 7***7@qq.com  │ 近况问候             │ 最近工作忙吗？五一假期过得怎么样？                   │
├─────┼───────────────┼──────────────────────┼──────────────────────────────────────────────────────┤
│  3  │ 7***7@qq.com  │ 周末问候             │ 达康你好，好久不见！周末愉快                         │
├─────┼───────────────┼──────────────────────┼──────────────────────────────────────────────────────┤
│  4  │ 7***7@qq.com  │ 重选文件夹验证       │ 测试re-select                                        │
├─────┼───────────────┼──────────────────────┼──────────────────────────────────────────────────────┤
│  5  │ 7***7@qq.com  │ 稳定性二次验证       │ 确认修复稳定                                         │
└─────┴───────────────┴──────────────────────┴──────────────────────────────────────────────────────┘

英文邮件已出现在发件箱第 1 位，双语展示、发送、验证全流程通过。
> 💡 `查看未读邮件` · `查看详情 1`
```

更多使用场景（归档、标记已读等）请查看 [SKILL.md](SKILL.md)。

## 特性

- **自然语言操作** — 说"看看有什么新邮件"即可，无需记忆命令
- **AI 智能分类** — 自动将邮件分为「需要关注」和「订阅/通知」，表格化汇报
- **Newsletter 拆解** — 自动识别并提取 Nature Briefing、AI Weekly 等订阅邮件中的文章
- **多邮箱账户** — 同时支持 QQ 邮箱和 Gmail，`--account` 一键切换
- **完整邮件操作** — 查看、回复、转发、发新邮件、归档、标记已读
- **HTML 转发** — 保留原始邮件的 HTML 格式，非纯文本降级
- **发送验证** — 回复/转发/发送后自动验证邮件已进入发件箱
- **双语展示** — 外语邮件发送前展示中文大意 + 外语正文

## 传统安装

<details>
<summary>一键脚本</summary>

```bash
# 克隆并安装
git clone https://github.com/MrSong9957/email-assistant.git
cd email-assistant
chmod +x install.sh && ./install.sh

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

</details>

<details>
<summary>手动安装</summary>

1. 创建技能目录：`mkdir -p ~/.claude/skills/email-assistant`
2. 复制文件：`cp SKILL.md email_cli.py requirements.txt .env.example ~/.claude/skills/email-assistant/`
3. 安装依赖：`pip install -r ~/.claude/skills/email-assistant/requirements.txt`
4. 配置凭证：复制 `.env.example` 为 `.env`，填入邮箱和授权码

</details>

<details>
<summary>工具目录对照</summary>

| 工具 | 全局目录 | 项目级目录 |
|------|---------|-----------|
| Claude Code | `~/.claude/skills/email-assistant/` | `.claude/skills/email-assistant/` |
| Codex CLI | `~/.agents/skills/email-assistant/` | `.agents/skills/email-assistant/` |
| Cursor | — | `.cursor/skills/email-assistant/` |
| OpenCode | `~/.config/opencode/skills/email-assistant/` | 项目内 |

</details>

<details>
<summary>配置参考</summary>

| 环境变量 | 必填 | 默认值 | 说明 |
|---------|------|--------|------|
| `MAIL_ACCOUNTS` | 是 | — | 账户列表，逗号分隔（如 `qq,gmail`） |
| `QQ_MAIL_USER` | 是 | — | QQ 邮箱地址 |
| `QQ_MAIL_APP_PASSWORD` | 是 | — | QQ 邮箱授权码 |
| `GMAIL_USER` | 是* | — | Gmail 邮箱地址 |
| `GMAIL_APP_PASSWORD` | 是* | — | Gmail 应用专用密码 |
| `MAIL163_USER` | 是* | — | 163 邮箱地址 |
| `MAIL163_APP_PASSWORD` | 是* | — | 163 邮箱授权码 |
| `*_IMAP_HOST` | 否 | 见下表 | IMAP 服务器 |
| `*_IMAP_PORT` | 否 | `993` | IMAP 端口 |
| `*_SMTP_HOST` | 否 | 见下表 | SMTP 服务器 |
| `*_SMTP_PORT` | 否 | `465` | SMTP 端口 |

> *仅当 `MAIL_ACCOUNTS` 包含对应邮箱（gmail、163）时必填

| Provider | IMAP | SMTP | 归档文件夹 | 发件箱 |
|----------|------|------|-----------|--------|
| QQ | imap.qq.com | smtp.qq.com | Archives | Sent Messages |
| Gmail | imap.gmail.com | smtp.gmail.com | [Gmail]/All Mail | [Gmail]/Sent Mail |
| 163 | imap.163.com | smtp.163.com | Archives | Sent Messages |

</details>

## 开发

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
docker compose -f docker/docker-compose.yml up
```

## License

[MIT](LICENSE)
