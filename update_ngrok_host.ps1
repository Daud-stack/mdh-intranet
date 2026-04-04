# PowerShell script to update Django ALLOWED_HOSTS with ngrok URL
param(
    [Parameter(Mandatory = $true)]
    [string]$NgrokUrl
)

Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "   Django ALLOWED_HOSTS Updater        " -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Remove https:// and http:// from URL
$cleanUrl = $NgrokUrl -replace "https://", "" -replace "http://", "" -replace "/$", ""

Write-Host "Updating ALLOWED_HOSTS with: $cleanUrl" -ForegroundColor Yellow
Write-Host ""

$settingsPath = "mdh_intranet\settings.py"

if (-not (Test-Path $settingsPath)) {
    Write-Host "[ERROR] settings.py not found at: $settingsPath" -ForegroundColor Red
    exit 1
}

# Read the settings file
$content = Get-Content $settingsPath -Raw

# Check if ngrok URL already exists
if ($content -match $cleanUrl) {
    Write-Host "[OK] $cleanUrl is already in ALLOWED_HOSTS!" -ForegroundColor Green
    exit 0
}

# Find the ALLOWED_HOSTS line and add the ngrok URL
$pattern = "('localhost,127\.0\.0\.1,\[::1\],host\.docker\.internal,10\.232\.190\.161')"
$replacement = "'localhost,127.0.0.1,[::1],host.docker.internal,10.232.190.161,$cleanUrl'"

if ($content -match $pattern) {
    $newContent = $content -replace $pattern, $replacement
    Set-Content -Path $settingsPath -Value $newContent
    Write-Host "[OK] ALLOWED_HOSTS updated successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next step: Restart Django server" -ForegroundColor Yellow
    Write-Host "  1. Press Ctrl+C in the Django terminal" -ForegroundColor White
    Write-Host "  2. Run: python manage.py runserver" -ForegroundColor White
    Write-Host ""
}
else {
    Write-Host "[WARNING] Could not automatically update ALLOWED_HOSTS" -ForegroundColor Yellow
    Write-Host "Please manually add '$cleanUrl' to ALLOWED_HOSTS in settings.py" -ForegroundColor Yellow
}

Write-Host "You can now access your app at: https://$cleanUrl" -ForegroundColor Green
Write-Host ""
