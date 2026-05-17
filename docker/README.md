# Docker 开发容器

基于共享基础镜像 `s7620605/claude-code-opencode` 的隔离开发环境，通过 .env 配置使用智谱 AI。

## 架构

```
.env (API Key) → docker-compose.yml → 容器环境变量 → Claude Code
```

基础镜像已包含：Debian + Python 3 + Node.js 20 + Claude Code + OpenCode + gh CLI + entrypoint。
项目只需注入环境变量即可使用。

## 快速开始

```bash
# 1. 编辑 .env，填入 API Key 和代理（可选）
# ANTHROPIC_API_KEY=your-api-key
# HTTP_PROXY=http://host.docker.internal:7890

# 2. 启动（首次会 pull 镜像）
docker compose up -d

# 3. 进入容器
docker exec -it -u app dev-container bash

# 4. 首次运行 Claude Code
claude
# 提示 "Do you want to use this API key?" 选择 Yes

# 5. 测试
claude -p "hello"
```

## 隔离说明

| 目录 | 类型 | 说明 |
|------|------|------|
| /home/app/project | Bind Mount | 项目目录，与宿主机双向同步 |
| /home/app/.claude | Docker Volume | Claude 配置，完全隔离 |
| /home/app/.config/opencode | Docker Volume | OpenCode 配置，完全隔离 |

### 邮件助手配置（可选）

| 变量 | 用途 |
|------|------|
| `QQ_MAIL_USER` | QQ 邮箱地址 |
| `QQ_MAIL_APP_PASSWORD` | QQ 邮箱授权码（非登录密码） |

获取授权码：QQ 邮箱 → 设置 → 账户 → POP3/IMAP/SMTP → 开启 IMAP → 生成授权码

## 故障排除

```bash
# 重建容器（保留 Volume 数据）
docker compose down && docker compose up -d

# 完全重置（删除所有配置）
docker compose down -v && docker compose up -d

# 更新基础镜像
docker compose pull && docker compose up -d
```

## 常用命令

```bash
docker compose logs -f          # 查看日志
docker compose down             # 停止
docker compose pull             # 更新镜像
docker volume ls                # 查看卷
```
