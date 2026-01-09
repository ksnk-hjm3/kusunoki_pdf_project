@echo off
echo Starting Flask server...
start cmd /k "python main.py"

timeout /t 2 >nul

echo Starting ngrok tunnel...
start cmd /k "ngrok http 8000"

echo All services started.
