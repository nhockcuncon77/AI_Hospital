# Free the server port so our server can bind. Run in PowerShell.
# Default port is 5050 (set PORT=5000 in .env if you use 5000).
$port = if ($env:PORT) { $env:PORT } else { 5050 }
$conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($conn) {
  $conn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
  Write-Host "Stopped process(es) on port $port."
} else {
  Write-Host "Nothing is listening on port $port."
}
