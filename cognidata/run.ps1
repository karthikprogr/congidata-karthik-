# CogniData Smart Launcher
# Run from anywhere: powershell -ExecutionPolicy Bypass -File run.ps1

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

Write-Host "`n🚀 CogniData Launcher" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

# Install backend deps if needed
Write-Host "`n📦 Checking backend dependencies..." -ForegroundColor Yellow
Set-Location $backend
pip install -r requirements.txt -q

# Install frontend deps if needed
Write-Host "📦 Checking frontend dependencies..." -ForegroundColor Yellow
Set-Location $frontend
if (-not (Test-Path "node_modules")) {
    Write-Host "   Installing npm packages..." -ForegroundColor DarkYellow
    npm install --silent
}

Write-Host "`n✅ Starting services..." -ForegroundColor Green
Write-Host "   Backend  → http://localhost:8000" -ForegroundColor White
Write-Host "   Frontend → http://localhost:5173" -ForegroundColor White
Write-Host "   API Docs → http://localhost:8000/docs" -ForegroundColor White
Write-Host "`n   Press Ctrl+C to stop both services`n" -ForegroundColor DarkGray

# Start backend — no --reload for faster response times
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$backend'; Write-Host 'Backend starting...' -ForegroundColor Cyan; python -m uvicorn app.main:app --port 8000 --workers 1 --loop asyncio"

# Small delay then start frontend
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontend'; Write-Host 'Frontend starting...' -ForegroundColor Cyan; npm run dev"

# Open browser after a moment
Start-Sleep -Seconds 4
Start-Process "http://localhost:5173"

Write-Host "✅ Both services launched in separate windows." -ForegroundColor Green
