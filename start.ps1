# AgentsGroup2026 — Windows Start Script (optimized for parity with macOS start.sh)
$ErrorActionPreference = "Continue"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT

Write-Host "=== AgentsGroup2026 Starting ===" -ForegroundColor Cyan
Write-Host ""

# ── Load .env into the current process ──
function Load-DotEnv($path) {
    if (-not (Test-Path $path)) {
        Write-Host "[!] No .env found. Use scripts\setup_keys.sh or set environment variables directly." -ForegroundColor Yellow
        Write-Host ""
        return
    }

    Get-Content $path -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#")) {
            $match = [regex]::Match($line, '^\s*([^=\s]+)\s*=\s*(.*)\s*$')
            if ($match.Success) {
                $name = $match.Groups[1].Value
                $value = $match.Groups[2].Value.Trim()
                if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                    $value = $value.Substring(1, $value.Length - 2)
                }
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
    }
    Write-Host "[OK] Loaded .env environment variables" -ForegroundColor Green
    Write-Host ""
}

Load-DotEnv "$ROOT\.env"

# ── Port check & auto-kill (cleanup_port equivalent) ──
function Clean-Port($port) {
    $ownerPids = @(
        netstat -ano -p tcp 2>$null |
            Select-String -Pattern (":$port\s+.*LISTENING\s+(\d+)\s*$") |
            ForEach-Object { $_.Matches[0].Groups[1].Value } |
            Sort-Object -Unique
    )
    if ($ownerPids.Count -gt 0) {
        Write-Host "[*] Cleaning up port $port (PID: $($ownerPids -join ', '))" -ForegroundColor Yellow
        foreach ($ownerPid in $ownerPids) {
            Stop-Process -Id ([int]$ownerPid) -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep 1
        Write-Host "    [OK] Port $port released" -ForegroundColor Green
    } else {
        Write-Host "    [OK] Port $port is free" -ForegroundColor Green
    }
}
Write-Host "[*] Checking ports..." -ForegroundColor Yellow
Clean-Port 8080
Clean-Port 5173
Write-Host ""

# ── Create and use Python venv (aligned with start.sh and run-python.cjs) ──
$VENV_DIR = "$ROOT\venv"
$DOTVENV_DIR = "$ROOT\.venv"
$VENV_PY = "$VENV_DIR\Scripts\python.exe"
$DOTVENV_PY = "$DOTVENV_DIR\Scripts\python.exe"
$PYTHON_CMD = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PYTHON_CMD -or $PYTHON_CMD -like "*\WindowsApps\python.exe") {
    $PYTHON_CMD = (Get-Command py -ErrorAction SilentlyContinue).Source
    if (-not $PYTHON_CMD) {
        Write-Host "[X] Python not found. Please install Python 3.11+." -ForegroundColor Red
        exit 1
    }
}
$RUNTIME_PY = $PYTHON_CMD

if (-not (Test-Path $VENV_DIR) -and -not (Test-Path $DOTVENV_DIR)) {
    Write-Host "[*] Creating Python virtual environment..." -ForegroundColor Cyan
    if ((Split-Path $PYTHON_CMD -Leaf) -ieq "py.exe") {
        & $PYTHON_CMD -3 -m venv --system-site-packages $VENV_DIR
    } else {
        & $PYTHON_CMD -m venv --system-site-packages $VENV_DIR
    }
    if (-not $?) {
        Write-Host "[X] Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

if (Test-Path $DOTVENV_PY) {
    $RUNTIME_PY = $DOTVENV_PY
    Write-Host "    [OK] Using project virtualenv (.venv)" -ForegroundColor Green
} elseif (Test-Path $VENV_PY) {
    $RUNTIME_PY = $VENV_PY
    Write-Host "    [OK] Using project virtualenv (venv)" -ForegroundColor Green
}

# ── Python dependencies (core + optional) ──
$PYTHON_CORE = @("fastapi", "uvicorn", "pydantic", "httpx", "cryptography")
$PYTHON_OPTIONAL = @("aiohttp", "pytest", "pytest-asyncio")

function List-MissingModules($pythonBin, $modules) {
    $missing = @()
    foreach ($mod in $modules) {
        & $pythonBin -c "import importlib.util; import sys; sys.exit(0 if importlib.util.find_spec('$mod') else 1)" 2>$null
        if ($LASTEXITCODE -ne 0) {
            $missing += $mod
        }
    }
    return $missing
}

Write-Host "[*] Checking Python dependencies..." -ForegroundColor Cyan
$coreMissing = List-MissingModules $RUNTIME_PY $PYTHON_CORE
if ($coreMissing.Count -gt 0) {
    $systemCoreMissing = List-MissingModules $PYTHON_CMD $PYTHON_CORE
    if ($systemCoreMissing.Count -eq 0) {
        $RUNTIME_PY = $PYTHON_CMD
        Write-Host "    [!] Project virtualenv is missing core packages; falling back to system Python" -ForegroundColor Yellow
    } else {
        Write-Host "    [!] Missing core modules: $($coreMissing -join ', ')" -ForegroundColor Yellow
        Write-Host "    [*] Installing..." -ForegroundColor Yellow
        & $RUNTIME_PY -m pip install --disable-pip-version-check @coreMissing 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    [X] Failed to install core dependencies" -ForegroundColor Red
            exit 1
        }
    }
}
Write-Host "    [OK] Core dependencies ready" -ForegroundColor Green

$optionalMissing = List-MissingModules $RUNTIME_PY $PYTHON_OPTIONAL
if ($optionalMissing.Count -gt 0) {
    Write-Host "    [!] Optional modules missing: $($optionalMissing -join ', ')" -ForegroundColor Yellow
    Write-Host "        Some features may be degraded until installed." -ForegroundColor Yellow
}
Write-Host ""

# ── Node.js ──
$node = Get-Command node -ErrorAction SilentlyContinue
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npm -or -not $node) {
    Write-Host "[X] Node.js/npm not found. Please install Node.js." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "$ROOT\node_modules")) {
    Write-Host "[*] Installing Node dependencies..." -ForegroundColor Cyan
    npm install --silent 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    [!] npm install had issues, retrying without --silent..." -ForegroundColor Yellow
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    [X] Failed to install Node dependencies" -ForegroundColor Red
            exit 1
        }
    }
}
Write-Host "    [OK] Node dependencies ready" -ForegroundColor Green
Write-Host ""

# ── Offline reconciliation check (non-blocking, zero LLM/tokens) ──
$usageDb = "$ROOT\storage\usage.db"
$reconcileScript = "$ROOT\scripts\offline_reconcile_check.py"
if ((Test-Path $usageDb) -and (Test-Path $reconcileScript)) {
    Write-Host "[*] Running offline reconciliation check..." -ForegroundColor Cyan
    & $RUNTIME_PY $reconcileScript --quiet --window 7d
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [OK] Usage ledger is consistent" -ForegroundColor Green
    } else {
        Write-Host "    [!] Reconciliation found inconsistencies; startup continues" -ForegroundColor Yellow
    }
    Write-Host ""
} else {
    Write-Host "[*] Offline reconciliation skipped (usage.db not generated yet)" -ForegroundColor Gray
    Write-Host ""
}

# ── Admin password (dev bootstrap) ──
$adminPasswordFile = "$ROOT\config\.dev_admin_password"
$usersFile = "$ROOT\config\users.json"

function Admin-AccountExists {
    if (Test-Path $usersFile) {
        try {
            $users = Get-Content $usersFile -Raw -Encoding UTF8 | ConvertFrom-Json
            return $null -ne $users.admin
        } catch { }
    }
    return $false
}

if ((-not (Test-Path env:ADMIN_PASSWORD)) -and (-not (Test-Path env:AG_ALLOW_DEFAULT_ADMIN))) {
    if (-not (Admin-AccountExists) -and -not (Test-Path $adminPasswordFile)) {
        # Generate new password
        $chars = [char[]]((48..57) + (65..90) + (97..122))
        $password = -join ((1..20) | ForEach-Object { $chars | Get-Random })
        
        $parent = Split-Path $adminPasswordFile -Parent
        if (-not (Test-Path $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
        $password | Out-File -FilePath $adminPasswordFile -Encoding ASCII -NoNewline
        $env:ADMIN_PASSWORD = $password
        
        Write-Host "[*] Local development admin login:" -ForegroundColor Cyan
        Write-Host "    Username: admin" -ForegroundColor Yellow
        Write-Host "    Password: $password" -ForegroundColor Yellow
        Write-Host "    Stored at config\.dev_admin_password (gitignored)" -ForegroundColor Gray
        Write-Host ""
    } elseif (Test-Path $adminPasswordFile) {
        $env:ADMIN_PASSWORD = (Get-Content $adminPasswordFile -Raw -Encoding ASCII).Trim()
        Write-Host "[*] Local development admin login:" -ForegroundColor Cyan
        Write-Host "    Username: admin" -ForegroundColor Yellow
        Write-Host "    Password: $($env:ADMIN_PASSWORD)" -ForegroundColor Yellow
        Write-Host "    Stored at config\.dev_admin_password (gitignored)" -ForegroundColor Gray
        Write-Host ""
    }
} elseif (Test-Path env:ADMIN_PASSWORD) {
    Write-Host "[*] Auth: ADMIN_PASSWORD provided for admin login" -ForegroundColor Cyan
    Write-Host ""
} elseif ((Test-Path env:AG_ALLOW_DEFAULT_ADMIN) -and $env:AG_ALLOW_DEFAULT_ADMIN -match '^(1|true|yes)$') {
    Write-Host "[*] Auth: AG_ALLOW_DEFAULT_ADMIN enabled; local login is admin / admin123" -ForegroundColor Cyan
    Write-Host ""
} elseif (Admin-AccountExists) {
    Write-Host "[*] Auth: existing admin account found. Set ADMIN_PASSWORD to reset it." -ForegroundColor Cyan
    Write-Host ""
}

# ── Start backend ──
Write-Host "[*] Starting backend on port 8080..." -ForegroundColor Cyan
$backendArgs = @("main.py", "--port", "8080")
if ($env:AG_NO_RELOAD -ne "1") {
    $backendArgs += "--reload"
    Write-Host "    [OK] Backend hot reload enabled (set AG_NO_RELOAD=1 to disable)" -ForegroundColor Green
}
$backendProcess = Start-Process $RUNTIME_PY -ArgumentList $backendArgs `
    -WorkingDirectory "$ROOT\src\backend" -WindowStyle Hidden -PassThru

# Wait for backend to be ready
Write-Host "    Waiting for backend..." -ForegroundColor Yellow
$ready = $false
for ($i = 1; $i -le 15; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8080/api/v1/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) {
            Write-Host "    [OK] Backend ready" -ForegroundColor Green
            $ready = $true
            break
        }
    } catch { }
    
    if (-not $backendProcess.HasExited) {
        Start-Sleep 1
    } else {
        Write-Host "    [X] Backend process exited unexpectedly (code $($backendProcess.ExitCode))." -ForegroundColor Red
        exit 1
    }
}
if (-not $ready) {
    Write-Host "    [X] Backend did not respond in time." -ForegroundColor Red
    Stop-Process $backendProcess -Force -ErrorAction SilentlyContinue
    exit 1
}

# ── Start frontend ──
Write-Host "[*] Starting frontend on port 5173..." -ForegroundColor Cyan
# Match start.sh: use the project npm dev script.
$npmCommand = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npmCommand) {
    $npmCommand = (Get-Command npm -ErrorAction SilentlyContinue).Source
}
if (-not $npmCommand) {
    Write-Host "[X] npx not found. Please install Node.js/npm." -ForegroundColor Red
    Stop-Process $backendProcess -Force -ErrorAction SilentlyContinue
    exit 1
}
$frontendProcess = Start-Process $npmCommand -ArgumentList "run","dev" `
    -WorkingDirectory $ROOT -WindowStyle Hidden -PassThru

Start-Sleep 2
if ($frontendProcess.HasExited -and $frontendProcess.ExitCode -ne 0) {
    Write-Host "[X] Frontend process exited unexpectedly." -ForegroundColor Red
    Stop-Process $backendProcess -Force -ErrorAction SilentlyContinue
    exit 1
}

Write-Host ""
Write-Host "════════════════════════════════════════" -ForegroundColor Green
Write-Host "  AgentsGroup2026 is running!" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8080" -ForegroundColor Green
Write-Host "  API Docs: http://localhost:8080/docs" -ForegroundColor Green
Write-Host "════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow

$global:backendPid = $backendProcess.Id
$global:frontendPid = $frontendProcess.Id

try {
    while ($true) {
        Start-Sleep 1
        if ($backendProcess.HasExited) {
            Write-Host ""
            Write-Host "[!] Backend process has exited." -ForegroundColor Red
            break
        }
        if ($frontendProcess.HasExited) {
            Write-Host ""
            Write-Host "[!] Frontend process has exited." -ForegroundColor Red
            break
        }
    }
} finally {
    Write-Host ""
    Write-Host "Shutting down..." -ForegroundColor Yellow
    Stop-Process -Id $global:backendPid -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $global:frontendPid -Force -ErrorAction SilentlyContinue
    Write-Host "Done." -ForegroundColor Yellow
}
