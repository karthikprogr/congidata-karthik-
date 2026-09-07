# CogniData Setup Verification Script
# Run this to verify your installation is correct

Write-Host "`n🔍 CogniData Setup Verification" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor DarkGray

$errors = 0
$warnings = 0

# Check Python
Write-Host "Checking Python..." -NoNewline
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.([0-9]+)") {
        $minor = [int]$Matches[1]
        if ($minor -ge 10) {
            Write-Host " ✓ $pythonVersion" -ForegroundColor Green
        } else {
            Write-Host " ⚠ $pythonVersion (3.10+ recommended)" -ForegroundColor Yellow
            $warnings++
        }
    } else {
        Write-Host " ✗ Not found" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host " ✗ Not found" -ForegroundColor Red
    $errors++
}

# Check Node.js
Write-Host "Checking Node.js..." -NoNewline
try {
    $nodeVersion = node --version 2>&1
    if ($nodeVersion -match "v([0-9]+)") {
        $major = [int]$Matches[1]
        if ($major -ge 18) {
            Write-Host " ✓ $nodeVersion" -ForegroundColor Green
        } else {
            Write-Host " ⚠ $nodeVersion (v18+ recommended)" -ForegroundColor Yellow
            $warnings++
        }
    } else {
        Write-Host " ✗ Not found" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host " ✗ Not found" -ForegroundColor Red
    $errors++
}

# Check Git
Write-Host "Checking Git..." -NoNewline
try {
    $gitVersion = git --version 2>&1
    Write-Host " ✓ $gitVersion" -ForegroundColor Green
} catch {
    Write-Host " ⚠ Not found (optional)" -ForegroundColor Yellow
    $warnings++
}

# Check backend directory
Write-Host "Checking backend..." -NoNewline
if (Test-Path "cognidata/backend/app/main.py") {
    Write-Host " ✓ Found" -ForegroundColor Green
} else {
    Write-Host " ✗ Missing" -ForegroundColor Red
    $errors++
}

# Check frontend directory
Write-Host "Checking frontend..." -NoNewline
if (Test-Path "cognidata/frontend/package.json") {
    Write-Host " ✓ Found" -ForegroundColor Green
} else {
    Write-Host " ✗ Missing" -ForegroundColor Red
    $errors++
}

# Check .env file
Write-Host "Checking .env..." -NoNewline
if (Test-Path "cognidata/backend/.env") {
    Write-Host " ✓ Found" -ForegroundColor Green
    
    # Check for OpenAI key
    $envContent = Get-Content "cognidata/backend/.env" -Raw
    if ($envContent -match "OPENAI_API_KEY=sk-") {
        Write-Host "  OpenAI API Key..." -NoNewline
        Write-Host " ✓ Configured" -ForegroundColor Green
    } else {
        Write-Host "  OpenAI API Key..." -NoNewline
        Write-Host " ⚠ Not configured" -ForegroundColor Yellow
        $warnings++
    }
} else {
    Write-Host " ⚠ Missing (will use defaults)" -ForegroundColor Yellow
    $warnings++
}

# Check requirements
Write-Host "Checking Python packages..." -NoNewline
if (Test-Path "cognidata/backend/.venv") {
    Write-Host " ✓ venv exists" -ForegroundColor Green
} else {
    Write-Host " ⚠ venv not found (run setup)" -ForegroundColor Yellow
    $warnings++
}

# Check node_modules
Write-Host "Checking npm packages..." -NoNewline
if (Test-Path "cognidata/frontend/node_modules") {
    Write-Host " ✓ node_modules exists" -ForegroundColor Green
} else {
    Write-Host " ⚠ node_modules not found (run npm install)" -ForegroundColor Yellow
    $warnings++
}

# Check database
Write-Host "Checking database..." -NoNewline
if (Test-Path "cognidata/backend/cognidata.db") {
    Write-Host " ✓ Found" -ForegroundColor Green
} else {
    Write-Host " ⚠ Will be created on first run" -ForegroundColor Yellow
}

# Summary
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
if ($errors -eq 0 -and $warnings -eq 0) {
    Write-Host "✅ Setup verification passed!" -ForegroundColor Green
    Write-Host "`nYou can now run:" -ForegroundColor White
    Write-Host "  powershell -ExecutionPolicy Bypass -File cognidata/run.ps1" -ForegroundColor Cyan
} elseif ($errors -eq 0) {
    Write-Host "⚠️  Setup has $warnings warning(s)" -ForegroundColor Yellow
    Write-Host "`nYou can run the app, but some features may not work:" -ForegroundColor White
    Write-Host "  powershell -ExecutionPolicy Bypass -File cognidata/run.ps1" -ForegroundColor Cyan
} else {
    Write-Host "❌ Setup has $errors error(s) and $warnings warning(s)" -ForegroundColor Red
    Write-Host "`nPlease fix the errors above before running." -ForegroundColor White
}

Write-Host "`nDocumentation:" -ForegroundColor DarkGray
Write-Host "  README.md         - Full documentation" -ForegroundColor Gray
Write-Host "  FIXES_APPLIED.md  - Recent fixes" -ForegroundColor Gray
Write-Host "  cognidata/FEATURES.md - Feature list`n" -ForegroundColor Gray
