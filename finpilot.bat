@echo off
:: FinPilot — Masaüstü Başlatıcı (Docker Devcontainer)
:: Çift tıklayın — devcontainer başlar ve tarayıcı açılır.
:: ─────────────────────────────────────────────────────────────

title FinPilot — Başlatılıyor...
color 0B
setlocal EnableDelayedExpansion

echo.
echo  ╔═══════════════════════════════════════╗
echo  ║   FinPilot  —  AI Stock Intelligence  ║
echo  ╚═══════════════════════════════════════╝
echo.

:: ─── Docker var mı? ──────────────────────────────────────────
where docker >nul 2>&1
if errorlevel 1 (
    echo  [HATA] Docker bulunamadi!
    echo  Docker Desktop'i kurun: https://www.docker.com/products/docker-desktop
    pause & exit /b 1
)

:: ─── Çalışan devcontainer'ı bul ─────────────────────────────
echo  [1/4] Devcontainer aranıyor...
set "CONTAINER_ID="

:: Yöntem 1: /workspaces/Borsa mount'u olan container
for /f "tokens=*" %%c in ('docker ps -q 2^>nul') do (
    docker inspect %%c --format "{{range .Mounts}}{{.Destination}} {{end}}" 2>nul | findstr /C:"/workspaces/Borsa" >nul 2>&1
    if not errorlevel 1 (
        set "CONTAINER_ID=%%c"
        goto :found
    )
)

:: Yöntem 2: borsa/finpilot/vsc- içeren container adı
for /f "tokens=*" %%c in ('docker ps --format "{{.Names}}" 2^>nul') do (
    echo %%c | findstr /I "borsa finpilot vsc-" >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=*" %%i in ('docker ps -q --filter "name=%%c" 2^>nul') do set "CONTAINER_ID=%%i"
        goto :found
    )
)

:: Yöntem 3: VS Code devcontainer label
for /f "tokens=*" %%c in ('docker ps -q --filter "label=devcontainer.metadata" 2^>nul') do (
    set "CONTAINER_ID=%%c"
    goto :found
)

echo  [HATA] Calissan devcontainer bulunamadi!
echo.
echo  Cozum: VS Code'u acin, devcontainer baslatın:
echo    1. VS Code ac
echo    2. Ctrl+Shift+P → "Reopen in Container"
echo    3. Container basladiktan sonra bu dosyayi tekrar calistirin.
echo.
pause & exit /b 1

:found
echo  Devcontainer bulundu: %CONTAINER_ID%

:: ─── Port kontrolü — servisler zaten çalışıyor mu? ──────────
echo  [2/4] Port kontrolu...
curl -sf --max-time 2 http://localhost:8000/api/v1/health >nul 2>&1
if not errorlevel 1 (
    echo  API zaten calisiyor.
    goto :open_browser
)

:: ─── Servisleri başlat ───────────────────────────────────────
echo  [3/4] Servisler baslatiliyor...

docker exec -d %CONTAINER_ID% bash -c "cd /workspaces/Borsa && mkdir -p logs && fuser -k 8000/tcp 2>/dev/null; python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 75 > logs/api_startup.log 2>&1" >nul 2>&1
docker exec -d %CONTAINER_ID% bash -c "source /usr/local/share/nvm/nvm.sh 2>/dev/null; cd /workspaces/Borsa/web && npm run dev > ../logs/web_startup.log 2>&1" >nul 2>&1

:: ─── API hazır olana kadar bekle ─────────────────────────────
echo  Servisler basliyor, lutfen bekleyin
set /a WAIT=0
:wait_loop
timeout /t 2 /nobreak >nul
set /a WAIT+=2
curl -sf --max-time 2 http://localhost:8000/api/v1/health >nul 2>&1
if not errorlevel 1 goto :api_ready
if %WAIT% GEQ 60 (
    echo.
    echo  [UYARI] API 60s icinde baslamadi, yine de tarayici aciliyor...
    goto :open_browser
)
set /p "=." <nul
goto :wait_loop

:api_ready
echo.
echo  API hazir! Frontend icin 10 saniye bekleniyor...
timeout /t 10 /nobreak >nul

:open_browser
echo  [4/4] Tarayici aciliyor...
echo.
echo  ╔═══════════════════════════════════════╗
echo  ║  FinPilot HAZIR!                      ║
echo  ║  http://localhost:3001                ║
echo  ╚═══════════════════════════════════════╝
echo.
start http://localhost:3001
timeout /t 3 /nobreak >nul
exit /b 0
