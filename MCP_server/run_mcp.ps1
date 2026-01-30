#!/usr/bin/env pwsh
<#
Simple MCP Server launcher (PowerShell)

Features:
- Runs from the script directory
- Sets EDEN_API_KEY from existing env, .env, keys.json, or prompts the user
- Optionally activates .venv if present
- Installs requirements from requirements.txt when needed
- Runs `python server.py` and keeps the window open after exit
#>

# Ensure script runs from its own directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "=== MCP Server Launcher ===" -ForegroundColor Cyan

# Simple debug logger (writes to TEMP so double-click runs can be diagnosed)
$dbg = Join-Path $env:TEMP 'run_mcp_debug.txt'
try { "==== run_mcp debug" | Out-File -FilePath $dbg -Encoding utf8 -Force } catch {}
"Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $dbg -Append -Encoding utf8
"Script: $($MyInvocation.MyCommand.Definition)" | Out-File -FilePath $dbg -Append -Encoding utf8
"WorkingDir: $scriptDir" | Out-File -FilePath $dbg -Append -Encoding utf8
function Append-Debug {
    param([string]$m)
    try { $m | Out-File -FilePath $dbg -Append -Encoding utf8 } catch {}
}
Append-Debug "---"

# Optionally activate virtualenv
$venvActivate = Join-Path $scriptDir '.venv\Scripts\Activate.ps1'
if (Test-Path $venvActivate) {
    Write-Host "Activating virtual environment..."
    try {
        & $venvActivate
            Append-Debug "Activated .venv: $venvActivate"
    } catch {
        Write-Warning "Failed to activate .venv: $_"
            Append-Debug "Failed to activate .venv: $_"
    }
} else {
    Write-Host "No .venv found; continuing with system python."
        Append-Debug "No .venv found"
}

# EDEN_API_KEY resolution: env -> .env -> keys.json -> prompt
if (-not $env:EDEN_API_KEY -or $env:EDEN_API_KEY -eq '') {
    $key = $null
    if (Test-Path (Join-Path $scriptDir '.env')) {
        foreach ($line in Get-Content '.env') {
            if ($line -match '^[\s]*EDEN_API_KEY\s*=\s*(.+)') {
                $key = $matches[1].Trim()
                break
            }
        }
    }

    # If keys.json exists, try to parse it here. Note: avoid invoking PowerShell
    # indirectly from a batch `for /f (...) in (`powershell ...`)` form — that
    # pattern can cause cmd.exe to terminate early on some systems when
    # PowerShell errors or is restricted. This launcher runs PowerShell
    # directly (safe) and extracts a likely key.
    if (-not $key) {
        if (Test-Path (Join-Path $scriptDir 'keys.json')) {
            try {
                $j = Get-Content 'keys.json' -Raw | ConvertFrom-Json
                if ($j -is [System.Array]) {
                    $key = $j[0]
                } else {
                    # try to extract the first property/value or value
                    $props = $j | Get-Member -MemberType NoteProperty -Force | Select-Object -First 1
                    if ($props) {
                        $pname = $props.Name
                        $val = $j.$pname
                        if ($val -is [System.Array]) { $key = $val[0] } else { $key = $val }
                    } else {
                        $s = $j | Out-String
                        if ($s) { $key = $s.Trim() }
                    }
                }
            } catch {
                Write-Verbose "Could not parse keys.json: $_"
                Append-Debug "Could not parse keys.json: $_"
            }
        }
    }

    if (-not $key) {
        Write-Host "EDEN_API_KEY not found in environment or files."
        $key = Read-Host "Enter EDEN_API_KEY (will be visible)"
        Append-Debug "Prompted user for EDEN_API_KEY"
    }

    if ($key) {
        # Sanity-check: prefer the trimmed string and report length (do not print the key)
        $ktrim = ([string]$key).Trim()
        if ($ktrim.Length -gt 0) {
            $env:EDEN_API_KEY = $ktrim
            Write-Host "EDEN_API_KEY set for this session (length: $($ktrim.Length))."
            Append-Debug "EDEN_API_KEY set (length: $($ktrim.Length))"
        } else {
            Write-Warning "EDEN_API_KEY resolved but empty. Server may reject requests requiring the key."
            Append-Debug "EDEN_API_KEY resolved but empty"
        }
    } else {
        Write-Warning "EDEN_API_KEY is empty. Server may reject requests requiring the key."
    }
} else {
    Write-Host "EDEN_API_KEY already present in environment."
    Append-Debug "EDEN_API_KEY already present in environment (length: $($env:EDEN_API_KEY.Length))"
}

# Install requirements if necessary (uses a marker file to avoid repeated installs)
if (Test-Path (Join-Path $scriptDir 'requirements.txt')) {
    $marker = Join-Path $scriptDir '.requirements_installed'
    $needInstall = -not (Test-Path $marker)
    if (-not $needInstall) {
        try {
            $reqTime = (Get-Item 'requirements.txt').LastWriteTime
            $markerTime = (Get-Item $marker).LastWriteTime
            if ($reqTime -gt $markerTime) { $needInstall = $true }
        } catch { $needInstall = $true }
    }

    if ($needInstall) {
        Write-Host "Installing dependencies from requirements.txt..."
        Append-Debug "Installing dependencies from requirements.txt"
        try {
            & python -m pip install -r requirements.txt
            if ($LASTEXITCODE -eq 0) {
                New-Item -Path $marker -ItemType File -Force | Out-Null
                Write-Host "Dependencies installed."
                Append-Debug "pip install succeeded"
            } else {
                Write-Warning "pip install exited with code $LASTEXITCODE"
                Append-Debug "pip install failed with exit code $LASTEXITCODE"
            }
        } catch {
            Write-Warning "Failed to install requirements: $_"
            Append-Debug "Failed to install requirements: $_"
        }
    } else {
        Write-Host "Requirements appear up-to-date (marker present)."
        Append-Debug "Requirements up-to-date"
    }
}

Write-Host "Starting MCP server (python server.py). Use Ctrl+C to stop." -ForegroundColor Green
try {
    & python server.py
    $rc = $LASTEXITCODE
    Write-Host "Server process exited with code $rc" -ForegroundColor Yellow
    Append-Debug "Server process exited with code $rc"
} catch {
    Write-Warning "Server execution failed: $_"
    Append-Debug "Server execution failed: $_"
}

Write-Host "Press Enter to close this window..."
[void][System.Console]::ReadLine()
