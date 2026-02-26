@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0\.." || exit /b 1
set "UV_CACHE_DIR=%CD%\.uv-cache"
set "UV_PROJECT_ENVIRONMENT=%CD%\.uv-venv"
set "PIP_CACHE_DIR=%CD%\.pip-cache"
set "TMP=%CD%\.tmp"
set "TEMP=%TMP%"

if not exist "%UV_CACHE_DIR%" mkdir "%UV_CACHE_DIR%" >nul 2>&1
if not exist "%UV_PROJECT_ENVIRONMENT%" mkdir "%UV_PROJECT_ENVIRONMENT%" >nul 2>&1
if not exist "%PIP_CACHE_DIR%" mkdir "%PIP_CACHE_DIR%" >nul 2>&1
if not exist "%TMP%" mkdir "%TMP%" >nul 2>&1

echo.
echo ==========================================
echo   RedInk Launcher (Windows)
echo ==========================================
echo.

echo [INFO] Checking prerequisites...

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    exit /b 1
)

where uv >nul 2>&1
if errorlevel 1 (
    set "USE_UV=0"
    echo [WARN] uv not found, fallback to pip.
) else (
    set "USE_UV=1"
)

where pnpm >nul 2>&1
if errorlevel 1 (
    where npm >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] pnpm/npm not found in PATH.
        exit /b 1
    )
    set "PKG_MANAGER=npm"
) else (
    set "PKG_MANAGER=pnpm"
)

echo [INFO] Installing backend dependencies...
set "BACKEND_READY=0"
set "DEPS_WARN=0"
if "!USE_UV!"=="1" (
    uv sync
    if !ERRORLEVEL! equ 0 (
        set "BACKEND_READY=1"
    ) else (
        echo [WARN] uv sync failed, fallback to pip.
    )
)

if "!BACKEND_READY!"=="0" (
    pip install -e . -q
    if errorlevel 1 (
        echo [WARN] Backend dependency install failed, continue startup.
        set "DEPS_WARN=1"
    ) else (
        set "USE_UV=0"
    )
)

echo [INFO] Installing frontend dependencies (if needed)...
pushd frontend
if not exist node_modules (
    call %PKG_MANAGER% install
    if errorlevel 1 (
        popd
        echo [WARN] Frontend dependency install failed, continue startup.
        set "DEPS_WARN=1"
        goto :START_SERVICES
    )
)
popd

:START_SERVICES
echo [INFO] Closing old RedInk service windows...
taskkill /FI "WINDOWTITLE eq RedInk-Backend-12398*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq RedInk-Backend-12398-Fallback*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq RedInk-Frontend-5173*" /T /F >nul 2>&1

echo [INFO] Starting backend service...
if exist "%CD%\.venv\Scripts\python.exe" (
    set "BACKEND_PY=%CD%\.venv\Scripts\python.exe"
) else (
    set "BACKEND_PY=python"
)
start "RedInk-Backend-12398" "!BACKEND_PY!" -m backend.app

call :WAIT_FOR_PORT 12398 15
if errorlevel 1 (
    echo [ERROR] Backend failed to start on port 12398.
    exit /b 1
)

echo [INFO] Starting frontend service...
set "FRONTEND_DIR=%CD%\frontend"
start "RedInk-Frontend-5173" /D "%FRONTEND_DIR%" cmd /k "title RedInk Frontend [5173] && call %PKG_MANAGER% run dev"

call :WAIT_FOR_PORT 5173 20
if errorlevel 1 (
    echo [ERROR] Frontend failed to start on port 5173.
    exit /b 1
)

echo.
echo [OK] Services started.
echo [OK] Frontend: http://localhost:5173
echo [OK] Backend : http://localhost:12398
if "!DEPS_WARN!"=="1" (
    echo [WARN] One or more dependency install steps failed.
)
echo.

if /I not "%NO_BROWSER%"=="1" (
    start "" "http://localhost:5173" >nul 2>&1
)

exit /b 0

:WAIT_FOR_PORT
set "PORT=%~1"
set "RETRIES=%~2"
:WAIT_LOOP
for /f %%A in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do (
    exit /b 0
)
set /a RETRIES-=1
if !RETRIES! LEQ 0 exit /b 1
timeout /t 1 /nobreak >nul
goto :WAIT_LOOP
