# Book Sphere Frontend Startup Script
Write-Host "Starting Book Sphere Frontend..." -ForegroundColor Green
Write-Host ""

# Change to frontend directory
Set-Location -Path "frontend"

# Install dependencies if needed
Write-Host "Checking frontend dependencies..." -ForegroundColor Yellow
if (!(Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
}

Write-Host ""
Write-Host "Starting frontend development server..." -ForegroundColor Green
Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""

# Start the development server
npm start
