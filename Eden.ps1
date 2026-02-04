# Eden Launcher PowerShell Script
Write-Host "🌱 Starting Eden System..." -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

# Start the Python launcher
try {
    & python eden_start.py
}
catch {
    Write-Host "Error: Python not found. Please install Python." -ForegroundColor Red
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
