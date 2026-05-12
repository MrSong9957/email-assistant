param(
    [ValidateSet("claude-code", "codex", "opencode")]
    [string]$Tool = "claude-code",
    [switch]$Project
)

$SkillDir = "email-assistant"
$Files = @("SKILL.md", "email_cli.py", "requirements.txt", ".env.example")

$ToolDirs = @{
    "claude-code" = Join-Path $env:USERPROFILE ".claude\skills\$SkillDir"
    "codex"       = Join-Path $env:USERPROFILE ".agents\skills\$SkillDir"
    "opencode"    = Join-Path $env:USERPROFILE ".config\opencode\skills\$SkillDir"
}

if ($Project) {
    $Target = ".claude\skills\$SkillDir"
} else {
    $Target = $ToolDirs[$Tool]
}

Write-Host "安装到 $Target ..."
New-Item -ItemType Directory -Force -Path $Target | Out-Null

foreach ($f in $Files) {
    Copy-Item -Path $f -Destination $Target
}

if ($Tool -ne "claude-code") {
    $DefaultPath = '~\.claude\skills\email-assistant'
    $NewPath = $Target -replace [regex]::Escape($env:USERPROFILE), '~'
    $skillFile = Join-Path $Target "SKILL.md"
    (Get-Content $skillFile -Raw) -replace [regex]::Escape($DefaultPath), $NewPath |
        Set-Content $skillFile -NoNewline
    Write-Host "已替换 SKILL.md 路径: $DefaultPath → $NewPath"
}

if ((Test-Path ".env") -and -not (Test-Path "$Target\.env")) {
    Copy-Item -Path ".env" -Destination $Target
    Write-Host "已复制 .env（首次安装）"
} elseif ((Test-Path ".env") -and (Test-Path "$Target\.env")) {
    Write-Host "已跳过 .env（目标已存在，不覆盖）"
}

pip install -r "$Target\requirements.txt" --quiet
Write-Host "完成: $Target"
