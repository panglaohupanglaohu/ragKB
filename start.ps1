# AgentsGroup2026 — Windows Start Script (optimized for parity with macOS start.sh)
$ErrorActionPreference = "Continue"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT

Write-Host "=== AgentsGroup2026 Starting ===" -ForegroundColor Cyan
Write-Host ""

# ── Port check & auto-kill (cleanup_port equivalent) ──
function Clean-Port($port) {
    $listener = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
    if ($listener) {
        $ownerPid = $listener.OwningProcess
        Write-Host "[*] Cleaning up port $port (PID: $ownerPid)" -ForegroundColor Yellow
        Stop-Process -Id $ownerPid -Force -ErrorAction SilentlyContinue
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

# ── Create and use Python venv (aligned with start.sh) ──
$VENV_DIR = "$ROOT\venv"
$VENV_PY = "$VENV_DIR\Scripts\python.exe"
$RUNTIME_PY = "python"

if (-not (Test-Path $VENV_DIR)) {
    Write-Host "[*] Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv --system-site-packages $VENV_DIR
    if (-not $?) {
        Write-Host "[X] Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

if (Test-Path $VENV_PY) {
    $RUNTIME_PY = $VENV_PY
    Write-Host "    [OK] Using project virtualenv" -ForegroundColor Green
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
    Write-Host "    [!] Missing core modules: $($coreMissing -join ', ')" -ForegroundColor Yellow
    Write-Host "    [*] Installing..." -ForegroundColor Yellow
    & $RUNTIME_PY -m pip install --disable-pip-version-check @coreMissing 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    [X] Failed to install core dependencies" -ForegroundColor Red
        exit 1
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
    }
}

# ── Start backend ──
Write-Host "[*] Starting backend on port 8080..." -ForegroundColor Cyan
$backendProcess = Start-Process $RUNTIME_PY -ArgumentList "main.py","--port","8080" `
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
# Use npx vite directly (more reliable than npm run dev which depends on rtk tool)
$frontendProcess = Start-Process npx -ArgumentList "vite","--config","vite.config.mjs","--port","5173" `
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
