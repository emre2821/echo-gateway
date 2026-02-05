Write-Host "Killing all Node processes on MCP ports..."
$ports = @(":3010", ":3011", ":8082")
foreach ($port in $ports) {
    $connections = netstat -ano | Select-String $port
    foreach ($conn in $connections) {
        $processPid = ($conn.ToString() -split '\s+')[4]
        if ($processPid -and $processPid -match '^\d+$') {
            Write-Host "Killing PID $processPid on port $port..."
            Stop-Process -Id $processPid -Force
        }
    }
}
Write-Host "Port cleanup complete!"
