@echo off
echo Starting RotaAI Local Development Environment...

REM Check if node_modules exists in frontend
if not exist "frontend\node_modules\" (
    echo Installing frontend dependencies...
    cd frontend && npm install && cd ..
)

REM Open two new windows for backend and frontend
start cmd /k "echo Starting Backend... && python main.py"
start cmd /k "echo Starting Frontend... && cd frontend && npm run dev"

echo.
echo Application is starting!
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo.
echo Close the terminal windows to stop the servers.
pause
