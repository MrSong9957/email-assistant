# CLAUDE.md

---

## Superpowers

### 开发工作流

遵循 Superpowers 七阶段工作流：

#### 1. 头脑风暴（Brainstorming）`brainstorming`
写代码之前，先通过提问细化需求，探索替代方案，分段展示设计供验证。

#### 2. Git Worktree `using-git-worktrees`
设计批准后，创建隔离工作空间（新分支），验证测试基线干净。

#### 3. 编写计划（Writing Plans）`writing-plans`
将工作拆分为 2-5 分钟的小任务。每个任务包含：精确文件路径、完整代码、验证步骤。

#### 4. 子代理驱动开发（Subagent-Driven Development）`subagent-driven-development` / `dispatching-parallel-agents` / `executing-plans`
每个任务分派独立子代理执行，双阶段审查（规格合规 + 代码质量）。

#### 5. 测试驱动开发（TDD）`test-driven-development`
严格 RED-GREEN-REFACTOR：先写失败测试 → 看它失败 → 写最小代码 → 看它通过 → 提交。
测试之前写的代码应删除重写。

#### 6. 代码审查（Code Review）`requesting-code-review` / `receiving-code-review`
任务间进行审查，按严重性报告问题。CRITICAL 级别阻止推进。

#### 7. 完成分支（Finishing Branch）`finishing-a-development-branch` / `verification-before-completion`
验证测试通过，呈现选项（merge/PR/保留/丢弃），清理 worktree。

---

### 技能库

可用技能通过 `Skill` 工具调用，按阶段归类：

#### 规划阶段
| 技能 | 触发时机 |
|------|---------|
| brainstorming | 任何创造性工作（新功能、新组件、行为修改）**之前**必须使用 |
| writing-plans | 有需求/规格需要拆分为多步任务时，写代码之前 |
| using-git-worktrees | 需要隔离工作空间、创建 feature 分支时 |

#### 执行阶段
| 技能 | 触发时机 |
|------|---------|
| subagent-driven-development | 当前会话中执行已拆分的独立任务 |
| dispatching-parallel-agents | 2+ 个无依赖的独立任务需要并行时 |
| executing-plans | 在独立会话中执行已有计划（含审查检查点） |
| test-driven-development | 实现功能或修复 bug 前，先写测试 |

#### 质量保障
| 技能 | 触发时机 |
|------|---------|
| verification-before-completion | 声称工作完成/修复/通过 **之前**，必须先运行验证 |
| requesting-code-review | 完成任务、实现大功能、合并前 |
| receiving-code-review | 收到代码审查反馈时，先验证再实施 |

#### 收尾阶段
| 技能 | 触发时机 |
|------|---------|
| finishing-a-development-branch | 实现完成、测试通过后，决定 merge/PR/保留/丢弃 |

#### 其他技能
| 技能 | 触发时机 |
|------|---------|
| using-superpowers | 每次对话开始时，建立技能发现和调用规则 |
| writing-skills | 创建/编辑技能，或验证技能可用性 |
| systematic-debugging | 跨阶段：遇到 bug、测试失败、意外行为时，**先观察再修复** |

---

### 设计原则

- 系统化优于临时应对：流程优于猜测
- 复杂度缩减：简洁是首要目标

技能分为两类：
- **刚性技能**（TDD、调试）：严格执行，不走捷径
- **弹性技能**（模式）：按上下文灵活应用

技能优先级：流程技能优先（brainstorming、debugging）→ 实施技能其次（frontend-design 等）

技能调用：1% 规则，即使只有 1% 可能适用也必须先调用技能；调用顺序：技能检查在澄清问题之前；指令优先级：用户指令 > superpowers 技能 > 默认行为

### 铁律

1. **TDD 铁律**：没有失败测试，不写生产代码
2. **调试铁律**：没有根因调查，不实施修复
3. **验证铁律**：没有运行证据，不声称完成

### 子代理派发规则

子代理无法调用 Skill 工具（不在其工具列表中）。父代理必须预加载技能内容并注入子代理 prompt：

**派发流程：**
1. 父代理调用 `Skill` 加载所需技能，获取完整内容
2. 将技能内容用 `---<SKILL_NAME> START---` / `---<SKILL_NAME> END---` 标记包裹
3. 嵌入子代理 prompt 的开头，附加具体任务指令

**场景映射：**
- 实现任务 → 父代理加载 `test-driven-development` 技能内容 → 注入 prompt
- 代码质量审查 → 父代理加载 `requesting-code-review` 技能内容 → 注入 prompt
- 完成分支 → 父代理加载 `finishing-a-development-branch` 技能内容 → 注入 prompt

**prompt 模板：**
```
你是一个遵循 <技能名> 规则的代理。以下是你的技能规则：

---<SKILL_NAME> START---
（父代理加载的完整技能内容）
---<SKILL_NAME> END---

（具体任务描述）
```

---

## 项目信息

### 项目概述

Python 邮件助手，作为 Claude Code 技能（Skill）运行。通过 IMAP 连接 QQ 邮箱，拉取未读邮件并用 AI 摘要分类后终端展示；用户口头指示回复/转发/归档，助手通过 SMTP 执行。

### 技术栈

- Python 3.13+ asyncio
- IMAP（收信）+ SMTP（发信），QQ 邮箱
- 部署形态：Claude Code Skill（`~/.claude/skills/email-assistant/SKILL.md`）

### 架构

```
用户口头指令 → Claude Code → Skill → asyncio IMAP/SMTP → QQ 邮箱
                                        ↓
                                   AI 摘要 + 分类 → 终端展示
```

运行环境为 Docker 开发容器（基础镜像 `s7620605/dev-base`，含 Python 3 + Node.js 20）。

### 目录结构

```
project/
├── CLAUDE.md              # 开发工作流和项目信息
├── SKILL.md               # 技能定义（部署产物）
├── email_cli.py           # 邮件助手源码（部署产物）
├── README.md              # 使用说明
├── requirements.txt       # 运行依赖
├── requirements-dev.txt   # 开发依赖
├── .env.example           # 环境变量模板
├── .gitignore
├── tests/                 # 测试
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_formatter.py
│   ├── test_imap.py
│   └── test_smtp.py
└── docker/                # 容器配置
    ├── docker-compose.yml
    ├── Dockerfile
    ├── settings.json.template
    └── README.md
```

### 环境配置

| 变量 | 用途 |
|------|------|
| `ANTHROPIC_API_KEY` | 智谱 AI API Key |
| `QQ_MAIL_IMAP_*` | IMAP 连接凭证 |
| `QQ_MAIL_SMTP_*` | SMTP 发信凭证 |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | GitHub MCP 认证 |
| `OBSIDIAN_VAULT_PATH` | Obsidian 知识库路径（宿主机） |
| `HTTP_PROXY` / `HTTPS_PROXY` | 网络代理 |
