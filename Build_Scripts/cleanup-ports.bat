@echo off
echo Killing all Node processes on MCP ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3010 :3011 :8081"') do (
    echo Killing PID %%a...
    taskkill /F /PID %%a 2>nul
)
echo Port cleanup complete!
timeout /t 2 >nul
