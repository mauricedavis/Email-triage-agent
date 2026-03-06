# setup_local.ps1
# ================
# Run this once in PowerShell to set up the local project folder.
#
# Usage:
#   cd C:\Users\MauriceJDavis\email-triage-agent
#   PowerShell -ExecutionPolicy Bypass -File .\setup_local.ps1

$ProjectPath = "C:\Users\MauriceJDavis\email-triage-agent"
$PythonCmd = "python"

Write-Host ""
Write-Host "============================================================"
Write-Host "  Email Triage Agent -- Local Setup"
Write-Host "============================================================"
Write-Host ""

# 1. Ensure project folder exists
if (-Not (Test-Path $ProjectPath)) {
    New-Item -ItemType Directory -Path $ProjectPath -Force | Out-Null
    Write-Host "[OK] Created folder: $ProjectPath"
} else {
    Write-Host "[OK] Folder exists: $ProjectPath"
}

Set-Location $ProjectPath

# 2. Create subdirectories
$dirs = @("config", "modules", "output", "logs")
foreach ($dir in $dirs) {
    if (-Not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "[OK] Created subfolder: $dir"
    }
}

# 3. Check Python
Write-Host ""
Write-Host "[..] Checking Python..."
try {
    $pyVersion = & $PythonCmd --version 2>&1
    Write-Host "     $pyVersion"
} catch {
    Write-Host "[!!] Python not found. Install from python.org and re-run this script."
    exit 1
}

# 4. Install dependencies
Write-Host ""
Write-Host "[..] Installing Python dependencies..."
& $PythonCmd -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!!] pip install failed. Check your internet connection."
    exit 1
}
Write-Host "[OK] Dependencies installed"

# 5. Create .env from template if not already present
Write-Host ""
if (-Not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] Created .env from template"
    Write-Host "     NEXT: Open and edit .env with your credentials"
} else {
    Write-Host "[--] .env already exists -- skipping"
}

# 6. Test dry run
Write-Host ""
Write-Host "[..] Running dry-run test (mock data, no credentials needed)..."
Write-Host ""
& $PythonCmd agent.py --dry-run
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[!!] Dry run failed -- set ANTHROPIC_API_KEY in .env first"
} else {
    Write-Host ""
    Write-Host "[OK] Dry run complete! Check output\ folder for the HTML briefing."
}

# 7. Summary
Write-Host ""
Write-Host "============================================================"
Write-Host "  Setup complete!"
Write-Host "============================================================"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Edit credentials:  notepad .env"
Write-Host "  2. Run live:          python agent.py"
Write-Host "  3. Push to GitHub:    python github_push.py"
Write-Host "  4. Schedule it:       See README.md - Task Scheduler section"
Write-Host ""
