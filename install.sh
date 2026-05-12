#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="email-assistant"
FILES=(SKILL.md email_cli.py requirements.txt .env.example)

declare -A TOOL_GLOBAL_DIRS=(
    ["claude-code"]="$HOME/.claude/skills/$SKILL_DIR"
    ["codex"]="$HOME/.agents/skills/$SKILL_DIR"
    ["opencode"]="$HOME/.config/opencode/skills/$SKILL_DIR"
)

TOOL="claude-code"
PROJECT=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --tool)
            TOOL="$2"
            shift 2
            ;;
        --project)
            PROJECT=true
            shift
            ;;
        *)
            echo "用法: $0 [--tool claude-code|codex|opencode] [--project]"
            exit 1
            ;;
    esac
done

if [[ "$OSTYPE" =~ msys|win32|cygwin ]]; then
    echo "检测到 Windows 环境，建议使用 PowerShell 脚本：pwsh install.ps1"
    exit 1
fi

if [[ "$PROJECT" == true ]]; then
    TARGET=".claude/skills/$SKILL_DIR"
else
    if [[ -z "${TOOL_GLOBAL_DIRS[$TOOL]+_}" ]]; then
        echo "未知工具: $TOOL（支持: ${!TOOL_GLOBAL_DIRS[*]}）"
        exit 1
    fi
    TARGET="${TOOL_GLOBAL_DIRS[$TOOL]}"
fi

echo "安装到 $TARGET ..."
mkdir -p "$TARGET"

for f in "${FILES[@]}"; do
    cp "$f" "$TARGET/"
done

DEFAULT_PATH='~/.claude/skills/email-assistant'
if [[ "$TOOL" != "claude-code" ]]; then
    SED_PATH="${TARGET/#$HOME\//~/}"
    sed -i "s|$DEFAULT_PATH|$SED_PATH|g" "$TARGET/SKILL.md"
    echo "已替换 SKILL.md 路径: $DEFAULT_PATH → $SED_PATH"
fi

if [[ -f .env ]] && [[ ! -f "$TARGET/.env" ]]; then
    cp .env "$TARGET/.env"
    echo "已复制 .env（首次安装）"
elif [[ -f .env ]] && [[ -f "$TARGET/.env" ]]; then
    echo "已跳过 .env（目标已存在，不覆盖）"
fi

pip install -r "$TARGET/requirements.txt" --quiet --break-system-packages
echo "完成: $TARGET"
