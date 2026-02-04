# Eden MCP Hub Controller Startup Script
Write-Host "=== Eden MCP Hub Controller ===" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>$null
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# Install dependencies if needed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import psutil, mcp" 2>$null
    Write-Host "Dependencies already installed." -ForegroundColor Green
} catch {
    Write-Host "Installing required dependencies..." -ForegroundColor Yellow
    python -m pip install psutil mcp
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error installing dependencies." -ForegroundColor Red
        exit 1
    }
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
}

# Create necessary directories
Write-Host "Setting up directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "mcp_servers" | Out-Null

# Change to the script's directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptPath
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Gray

# Start the hub controller
Write-Host "Starting MCP Hub Controller..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the hub" -ForegroundColor Yellow
Write-Host ""

try {
    python mcp_hub_controller_simple.py
} catch {
    Write-Host "`nHub stopped." -ForegroundColor Cyan
}

Write-Host "=== Eden MCP Hub Controller Shutdown ===" -ForegroundColor Cyan
