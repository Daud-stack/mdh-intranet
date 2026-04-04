# PowerShell script to download and setup ngrok for Windows
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "   ngrok Setup for Office Web Viewer   " -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

$ngrokPath = "$PSScriptRoot\ngrok"
$zipPath = "$PSScriptRoot\ngrok.zip"
$ngrokExe = "$ngrokPath\ngrok.exe"

# Check if ngrok already exists
if (Test-Path $ngrokExe) {
    Write-Host "[OK] ngrok already installed at: $ngrokExe" -ForegroundColor Green
    Write-Host ""
}
else {
    Write-Host "Downloading ngrok..." -ForegroundColor Yellow
    
    # Download ngrok for Windows
    $url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    
    try {
        Invoke-WebRequest -Uri $url -OutFile $zipPath -UseBasicParsing
        Write-Host "[OK] Download complete!" -ForegroundColor Green
        
        # Extract
        Write-Host "Extracting ngrok..." -ForegroundColor Yellow
        if (-not (Test-Path $ngrokPath)) {
            New-Item -ItemType Directory -Path $ngrokPath | Out-Null
        }
        Expand-Archive -Path $zipPath -DestinationPath $ngrokPath -Force
        Write-Host "[OK] Extraction complete!" -ForegroundColor Green
        
        # Cleanup
        Remove-Item $zipPath -Force
        Write-Host "[OK] Cleanup complete!" -ForegroundColor Green
        Write-Host ""
    }
    catch {
        Write-Host "[ERROR] Error downloading ngrok: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please download manually from: https://ngrok.com/download" -ForegroundColor Yellow
        exit 1
    }
}

# Display version
Write-Host "Checking ngrok version..." -ForegroundColor Cyan
& $ngrokExe version
Write-Host ""

Write-Host "=======================================" -ForegroundColor Green
Write-Host "       ngrok Setup Complete!           " -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Run: .\ngrok\ngrok.exe http 8000" -ForegroundColor White
Write-Host "2. Copy the 'Forwarding' URL (https://xxxxx.ngrok.io)" -ForegroundColor White
Write-Host "3. Update settings.py ALLOWED_HOSTS with the ngrok URL" -ForegroundColor White
Write-Host "4. Access your app via the ngrok URL" -ForegroundColor White
Write-Host ""
Write-Host "For authentication (optional):" -ForegroundColor Cyan
Write-Host "  .\ngrok\ngrok.exe config add-authtoken YOUR_TOKEN" -ForegroundColor White
Write-Host "  Get token from: https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor White
Write-Host ""
