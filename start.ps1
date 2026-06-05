# AgentsGroup2026 — Windows Start Script
$ErrorActionPreference = "Continue"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT

Write-Host ">>> AgentsGroup2026 Starting..." -ForegroundColor Cyan
Write-Host ""

# ── Port check ──
function Test-PortInUse($port) {
    $listener = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
    if ($listener) {
        Write-Host "[X] Port $port is already in use. Stop the process using that port first." -ForegroundColor Red
        exit 1
    }
}
Test-PortInUse 8080
Test-PortInUse 5173

# ── Python ──
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "[X] Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

$requiredModules = @("fastapi", "uvicorn", "pydantic", "httpx", "cryptography", "aiohttp")
Write-Host "[*] Checking Python dependencies..." -ForegroundColor Yellow
$missing = @()
foreach ($mod in $requiredModules) {
    $result = python -c "import $mod" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $missing += $mod
    }
}
if ($missing.Count -gt 0) {
    Write-Host "[!] Missing: $missing. Installing..." -ForegroundColor Yellow
    pip install @missing 2>&1 | Out-Null
}
Write-Host "   [OK] Python dependencies ready" -ForegroundColor Green

# ── Node ──
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Host "[X] Node.js not found. Please install Node.js." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "$ROOT\node_modules")) {
    Write-Host "[*] Installing Node dependencies..." -ForegroundColor Yellow
    npm install
}
Write-Host "   [OK] Node dependencies ready" -ForegroundColor Green

# ── Admin password (dev) ──
$adminPasswordFile = "$ROOT\config\.dev_admin_password"
if (-not (Test-Path env:ADMIN_PASSWORD) -and -not (Test-Path env:AG_ALLOW_DEFAULT_ADMIN)) {
    $usersFile = "$ROOT\config\users.json"
    $hasAdmin = $false
    if (Test-Path $usersFile) {
        try {
            $users = Get-Content $usersFile -Raw -Encoding UTF8 | ConvertFrom-Json
            $hasAdmin = $users.PSObject.Properties.Name -contains "admin"
        } catch { }
    }
    if (-not $hasAdmin -and -not (Test-Path $adminPasswordFile)) {
        $password = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 20 | ForEach-Object { [char]$_ })
        $parent = Split-Path $adminPasswordFile -Parent
        if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
        $password | Out-File -FilePath $adminPasswordFile -Encoding ascii -NoNewline
        $env:ADMIN_PASSWORD = $password
        Write-Host "(*) Local dev admin:" -ForegroundColor Yellow
        Write-Host "   Username: admin" -ForegroundColor Yellow
        Write-Host "   Password: $password" -ForegroundColor Yellow
        Write-Host "   Stored at config\.dev_admin_password (gitignored)." -ForegroundColor Yellow
        Write-Host ""
    }
}

Write-Host "[OK] Dependencies ready" -ForegroundColor Green
Write-Host ""

# ── Start backend ──
Write-Host "[>>] Starting backend on port 8080..." -ForegroundColor Cyan
$backendProcess = Start-Process python -ArgumentList "main.py","--port","8080" -WorkingDirectory "$ROOT\src\backend" -WindowStyle Hidden -PassThru

# Wait for backend
Write-Host "   ... Waiting for backend ..." -ForegroundColor Yellow
$ready = $false
for ($i = 1; $i -le 20; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8080/api/v1/health" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) {
            Write-Host "   [OK] Backend ready" -ForegroundColor Green
            $ready = $true
            break
        }
    } catch { }
    if ($backendProcess.HasExited -and $backendProcess.ExitCode -ne 0) {
        Write-Host "   [X] Backend process exited unexpectedly (code $($backendProcess.ExitCode))." -ForegroundColor Red
        exit 1
    }
    Start-Sleep 1
}
if (-not $ready) {
    Write-Host "   [X] Backend did not respond in time." -ForegroundColor Red
    Stop-Process $backendProcess -Force -ErrorAction SilentlyContinue
    exit 1
}

# ── Start frontend ──
Write-Host "[>>] Starting frontend on port 5173..." -ForegroundColor Cyan
$frontendProcess = Start-Process cmd -ArgumentList "/c","npx vite --config vite.config.mjs --port 5173" -WorkingDirectory $ROOT -WindowStyle Hidden -PassThru

Start-Sleep 3
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
            Write-Host "[!] Backend process has exited." -ForegroundColor Red
            break
        }
        if ($frontendProcess.HasExited) {
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
