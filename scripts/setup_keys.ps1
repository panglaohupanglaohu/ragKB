# setup_keys.ps1 — Windows PowerShell 交互式设置 API key 环境变量，写入项目根目录 .env
# 用法: powershell -ExecutionPolicy Bypass -File scripts\setup_keys.ps1
# 之后在 /agent-team-config.html 编辑模型时，API Key 字段填 env:VAR_NAME（如 env:DEEPSEEK_API_KEY）

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$EnvFile = Join-Path $RootDir ".env"

Write-Host "=== AgentsGroup2026 API Key 环境变量设置（Windows）===" -ForegroundColor Cyan
Write-Host "目标文件: $EnvFile"
Write-Host "已存在的变量会被更新，新变量会追加。"
Write-Host ""

# 常见 provider → 环境变量名映射
$KnownKeys = @(
    @{ Var = "DEEPSEEK_API_KEY"; Label = "DeepSeek" },
    @{ Var = "OPENAI_API_KEY"; Label = "OpenAI" },
    @{ Var = "ANTHROPIC_API_KEY"; Label = "Anthropic" },
    @{ Var = "OPENROUTER_API_KEY"; Label = "OpenRouter" },
    @{ Var = "GITHUB_MODELS_API_KEY"; Label = "GitHub Models" },
    @{ Var = "QWEN_API_KEY"; Label = "Qwen (通义千问)" }
)

function Write-Kv {
    param([string]$Key, [string]$Value)
    if (Test-Path $EnvFile) {
        $lines = Get-Content $EnvFile -Encoding UTF8 | Where-Object { $_ -notmatch "^$Key=" }
    } else {
        $lines = @()
    }
    $lines += "$Key=`"$Value`""
    $lines | Out-File -FilePath $EnvFile -Encoding UTF8
}

function Get-Current {
    param([string]$Key)
    if (Test-Path $EnvFile) {
        $line = Get-Content $EnvFile -Encoding UTF8 | Where-Object { $_ -match "^$Key=" } | Select-Object -First 1
        if ($line) {
            $val = $line.Split('=', 2)[1].Trim('"')
            return $val
        }
    }
    return ""
}

function Set-Key {
    param([string]$VarName, [string]$Label)
    $current = Get-Current -Key $VarName
    if ($current) {
        $masked = $current.Substring(0, [Math]::Min(4, $current.Length)) + "****"
        Write-Host "  当前 $VarName : $masked （已设置）"
    } else {
        Write-Host "  当前 $VarName : （未设置）"
    }
    $value = Read-Host "  输入 $Label API Key（回车跳过，保持不变）"
    if ($value) {
        Write-Kv -Key $VarName -Value $value
        Write-Host "  ✓ $VarName 已保存" -ForegroundColor Green
    }
}

# 主菜单
while ($true) {
    Write-Host ""
    Write-Host "--- 已知 provider ---"
    for ($i = 0; $i -lt $KnownKeys.Count; $i++) {
        $idx = $i + 1
        $k = $KnownKeys[$i]
        $status = "未设置"
        if (Test-Path $EnvFile) {
            $line = Get-Content $EnvFile -Encoding UTF8 | Where-Object { $_ -match "^$($k.Var)=" } | Select-Object -First 1
            if ($line) { $status = "已设置" }
        }
        Write-Host "  $idx) $($k.Label) ($($k.Var)) [$status]"
    }
    Write-Host "  c) 自定义变量名"
    Write-Host "  l) 查看当前 .env"
    Write-Host "  q) 完成"
    $choice = Read-Host "选择"
    switch ($choice) {
        { $_ -match '^[1-6]$' } {
            $k = $KnownKeys[[int]$choice - 1]
            Set-Key -VarName $k.Var -Label $k.Label
        }
        "c" {
            $cvar = Read-Host "  变量名（如 MY_CUSTOM_KEY）"
            $cval = Read-Host "  输入值"
            if ($cvar -and $cval) {
                Write-Kv -Key $cvar -Value $cval
                Write-Host "  ✓ $cvar 已保存" -ForegroundColor Green
            }
        }
        "l" {
            Write-Host "--- $EnvFile ---"
            if (Test-Path $EnvFile) {
                Get-Content $EnvFile -Encoding UTF8 | ForEach-Object {
                    if ($_ -match "^([^=]+)=(.*)$") {
                        $v = $matches[2].Trim('"')
                        $masked = $v.Substring(0, [Math]::Min(4, $v.Length)) + "****"
                        Write-Host "$($matches[1])=$masked"
                    } else {
                        Write-Host $_
                    }
                }
            } else {
                Write-Host "  （文件不存在）"
            }
        }
        "q" {
            Write-Host ""
            Write-Host "=== 完成 ===" -ForegroundColor Cyan
            Write-Host ".env 已保存到: $EnvFile（已被 .gitignore 忽略）"
            Write-Host ""
            Write-Host "下一步：在 /agent-team-config.html 编辑模型时，API Key 字段填："
            Write-Host "  env:VAR_NAME"
            Write-Host "例如：env:DEEPSEEK_API_KEY"
            Write-Host ""
            Write-Host "重启后端后生效（后端启动时自动加载 .env）。"
            break
        }
        default { Write-Host "无效选择" -ForegroundColor Yellow }
    }
}
