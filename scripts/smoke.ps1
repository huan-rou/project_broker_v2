$ErrorActionPreference = "Stop"

Write-Host "Checking backend health..."
Invoke-RestMethod http://localhost:8000/health | ConvertTo-Json -Depth 5

Write-Host "Checking preflight..."
Invoke-RestMethod http://localhost:8000/api/v1/system/preflight | ConvertTo-Json -Depth 8

Write-Host "Smoke check complete."
