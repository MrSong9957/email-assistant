# 邮件筛选功能设计

**日期**：2026-05-09
**状态**：已批准

## 背景

`fetch` 命令目前只能拉取所有未读邮件，无筛选能力。用户经常需要按时间或发件人缩小范围，如"最近三天的邮件"、"张三发的邮件"。

## 用户交互模型

用户通过 Claude Code 对话使用自然语言筛选，Claude 负责将自然语言翻译为 CLI 参数组合。CLI 参数作为底层机制存在，用户无需直接使用。

### SKILL.md 映射指南

| 用户说 | Claude 执行 |
|--------|-------------|
| "最近 N 天的邮件" | `--days N` |
| "5月1日以来的邮件" | `--since 2026-05-01` |
| "5月1日到5月5日的邮件" | `--since 2026-05-01 --before 2026-05-06` |
| "张三发的邮件" | `--from 张三` |
| "关于报告的邮件" | `--subject 报告` |
| "最近一周张三发的关于报告的邮件" | `--days 7 --from 张三 --subject 报告` |

## 技术设计

### CLI 参数

`fetch` 子命令新增 5 个可选参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| `--since` | `YYYY-MM-DD` | 开始日期（含当天） |
| `--before` | `YYYY-MM-DD` | 结束日期（不含当天） |
| `--days` | int | 最近 N 天，与 `--since` 互斥 |
| `--from` | str | 发件人模糊匹配（大小写不敏感，子串匹配） |
| `--subject` | str | 主题模糊匹配（大小写不敏感，子串匹配） |

`--days` 与 `--since` 同时指定时报错退出。

### 数据流

```
1. fetch_emails() 照常拉取所有未读邮件 → [(index, uid, msg), ...]
2. filter_emails(emails, since, before, from_addr, subject) → 过滤后列表
3. 格式化过滤后列表 → Markdown
```

### 过滤逻辑

- **日期**：解析邮件 `Date` 头（RFC 2822），只取日期部分，与 `--since`/`--before` 比较
- **发件人/主题**：`in` 操作符，`lower()` 后子串匹配
- **过滤后的 index 保持连续编号**（1, 2, 3...），方便后续回复/转发/标记操作引用

### 修改范围

- **`email_cli.py`**：
  - `fetch_emails` 返回结构化数据列表（uid + msg），不再直接拼接 Markdown
  - 新增 `filter_emails(results, since=None, before=None, from_addr=None, subject=None)`
  - 格式化逻辑从 `fetch_emails` 提取出来，对过滤后的列表调用
  - `cmd_fetch` 解析新参数并串联：fetch → filter → format → print
- **`tests/test_imap.py`**：新增 `TestFilterEmails` 测试类
- **`SKILL.md`**：新增映射指南部分

### 不变的部分

- `imap_client`、`get_config`、其他命令（reply/forward/send/archive/mark-read）不变
- `--limit` 和 `--folder` 参数不变
