@echo off
echo Starting RedInk...
echo.
echo Starting backend...
start "Backend" cmd /k "uv run python -m backend.app"
timeout /t 5 /nobreak >nul
echo Starting frontend...
cd frontend
start "Frontend" cmd /k "pnpm dev"
echo.
echo RedInk is starting...
echo Backend: http://localhost:12398
echo Frontend: http://localhost:5173
echo.
pause
