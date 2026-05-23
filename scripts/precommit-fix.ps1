# Pre-commit auto-fix loop.
# Runs ruff format/lint, restages modifications, then retries commit.
# Usage: .\scripts\precommit-fix.ps1 "commit message"
#
# Replaces the --no-verify workaround: keeps hooks active but auto-stages
# the formatter output instead of failing the commit.

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Message
)

# Don't stop on stderr warnings from git/ruff
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot\..

Write-Host "[1/3] Running pre-commit on staged files..." -ForegroundColor Cyan
& pre-commit run
$hookExit = $LASTEXITCODE

if ($hookExit -ne 0) {
    Write-Host "[2/3] Hooks modified files - restaging..." -ForegroundColor Yellow
    & git add -u
    Write-Host "      Re-running hooks to confirm clean..." -ForegroundColor Yellow
    & pre-commit run
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Hooks still failing after auto-fix. Fix manually." -ForegroundColor Red
        exit 1
    }
}

Write-Host "[3/3] Committing..." -ForegroundColor Cyan
& git commit -m $Message
exit $LASTEXITCODE
