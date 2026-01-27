param(
    [switch]$Aggressive
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Split-Path -Parent $root
Set-Location $proj

# Ensure UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$timestamp = (Get-Date).ToString('yyyyMMdd_HHmm')
$logDir = Join-Path $proj 'logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$logFile = Join-Path $logDir ("scanner_$timestamp.log")

$python = 'python'
$args = '.\\scanner.py'
if ($Aggressive) { $args = "$args --aggressive" }

"[INFO] Starting scan at $timestamp (Aggressive=$Aggressive)" | Tee-Object -FilePath $logFile

try {
    & $python $args 2>&1 | Tee-Object -FilePath $logFile -Append
    "[INFO] Completed scan at $(Get-Date -Format 'yyyyMMdd_HHmm')" | Tee-Object -FilePath $logFile -Append
}
catch {
    "[ERROR] $($_.Exception.Message)" | Tee-Object -FilePath $logFile -Append
    exit 1
}
