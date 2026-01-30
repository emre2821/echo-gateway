@echo off
rem Early debug file in TEMP so we capture runs even if pushd fails
set "TMPDBG=%TEMP%\run_mcp_debug.txt"
echo ==== run_mcp debug > "%TMPDBG%"
echo Time: %DATE% %TIME% >> "%TMPDBG%"
echo Launched: %~f0 >> "%TMPDBG%"
rem MCP Server launcher (Batch)
rem - Runs from its own directory
rem - Sets EDEN_API_KEY from env, .env, keys.json (via PowerShell), or prompts
rem - Optionally activates .venv, installs requirements, runs server.py

rem Change to script dir; on failure log and continue so debug file is written
pushd "%~dp0" 2>>"%TMPDBG%" || (echo Failed to change directory >> "%TMPDBG%" )

echo === MCP Server Launcher ===

rem Ensure a debug file exists early so double-click runs can be diagnosed
set "DBGFILE=run_mcp_debug.txt"
echo ==== run_mcp debug > "%DBGFILE%"
echo Time: %DATE% %TIME%>> "%DBGFILE%"
echo Started run_mcp.bat >> "%DBGFILE%"
echo WorkingDir: %CD% >> "%DBGFILE%"
echo --------------------- >> "%DBGFILE%"

rem Activate venv if present
if exist ".venv\Scripts\activate.bat" (
    echo Activating .venv...
    call ".venv\Scripts\activate.bat"
) else (
    echo No .venv found; using system python.
)

rem Resolve EDEN_API_KEY
if defined EDEN_API_KEY (
    echo EDEN_API_KEY already set in environment.
) else (
    rem Try .env first
    if exist ".env" (
        for /f "usebackq tokens=1* delims==" %%A in (".env") do (
            if /I "%%A"=="EDEN_API_KEY" set "EDEN_API_KEY=%%B"
        )
    )

    rem If still not set, try keys.json via PowerShell to extract a likely value.
    rem NOTE: invoking PowerShell via `for /f (...) in (`powershell ...`)` can cause
    rem cmd.exe to terminate early on some systems when PowerShell errors or is
    rem restricted. To avoid that known edge-case, run PowerShell and redirect
    rem its output to a temporary file, then read the file non-fatally.
    if not defined EDEN_API_KEY if exist "keys.json" (
        set "TMPKEY=%TEMP%\eden_key_tmp.txt"
        set "DBGFILE=run_mcp_debug.txt"
        rem Run PowerShell and capture stdout+stderr to temp file
        powershell -NoProfile -Command "try{ $j=Get-Content 'keys.json' -Raw | ConvertFrom-Json; if ($j -is [array]){ $j[0] } elseif ($j.PSObject.Properties.Count -gt 0){ $v=$j.PSObject.Properties[0].Value; if ($v -is [array]){$v[0]} else{$v} } else{''}} catch {Write-Error $_; exit 0}" > "%TMPKEY%" 2>&1
        rem Write helpful debug info so double-click runs can be diagnosed
        echo ==== run_mcp debug > "%DBGFILE%"
        echo Time: %DATE% %TIME%>> "%DBGFILE%"
        if exist "%TMPKEY%" (
            echo ---- temp output ---->> "%DBGFILE%"
            type "%TMPKEY%" >> "%DBGFILE%" 2>> "%DBGFILE%"
            echo --------------------- >> "%DBGFILE%"
            rem set EDEN_API_KEY if temp file non-empty
            for /f "usebackq delims=" %%K in ("%TMPKEY%") do (
                if not defined EDEN_API_KEY set "EDEN_API_KEY=%%K"
            )
            del "%TMPKEY%" >nul 2>&1
        ) else (
            echo PowerShell did not produce temp file.>> "%DBGFILE%"
        )
        echo Debug written to %~dp0%DBGFILE%>> "%DBGFILE%"
    )

    if not defined EDEN_API_KEY (
        set /p EDEN_API_KEY=Enter EDEN_API_KEY (visible): 
    )
)

echo EDEN_API_KEY=%EDEN_API_KEY%

rem Install requirements if marker missing
if exist requirements.txt (
    if not exist .requirements_installed (
        echo Installing dependencies from requirements.txt...
        python -m pip install -r requirements.txt
        if errorlevel 1 (
            echo pip install failed with code %ERRORLEVEL%
        ) else (
            type nul > .requirements_installed
            echo Dependencies installed.
        )
    ) else (
        echo Requirements marker found; skipping install.
    )
)

echo Starting MCP server (python server.py). Press Ctrl+C to stop.
python server.py
echo Server exited with code %ERRORLEVEL%

pause
popd
