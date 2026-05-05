@echo off
:: FinPilot — Durdurma (Docker Devcontainer)
title FinPilot — Durduruluyor
color 0B
setlocal EnableDelayedExpansion

echo.
echo  FinPilot durduruluyor...
echo.

:: ─── Docker var mı? ──────────────────────────────────────────
where docker >nul 2>&1
if errorlevel 1 (
    echo  [HATA] Docker bulunamadi!
    pause & exit /b 1
)

:: ─── Çalışan devcontainer'ı bul ─────────────────────────────
set "CONTAINER_ID="

for /f "tokens=*" %%c in ('docker ps -q 2^>nul') do (
    docker inspect %%c --format "{{range .Mounts}}{{.Destination}} {{end}}" 2>nul | findstr /C:"/workspaces/Borsa" >nul 2>&1
    if not errorlevel 1 (
        set "CONTAINER_ID=%%c"
        goto :found
    )
)

for /f "tokens=*" %%c in ('docker ps --format "{{.Names}}" 2^>nul') do (
    echo %%c | findstr /I "borsa finpilot vsc-" >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=*" %%i in ('docker ps -q --filter "name=%%c" 2^>nul') do set "CONTAINER_ID=%%i"
        goto :found
    )
)

for /f "tokens=*" %%c in ('docker ps -q --filter "label=devcontainer.metadata" 2^>nul') do (
    set "CONTAINER_ID=%%c"
    goto :found
)

echo  [HATA] Calissan devcontainer bulunamadi.
echo  Servisler zaten durmus olmali.
pause & exit /b 0

:found
echo  Devcontainer bulundu: %CONTAINER_ID%
echo  Portlar kapatiliyor (8000 ve 3000)...

docker exec %CONTAINER_ID% bash -c "fuser -k 8000/tcp 2>/dev/null; fuser -k 3000/tcp 2>/dev/null; echo Tamam." 2>nul

echo.
echo  FinPilot durduruldu.
echo.
pause
