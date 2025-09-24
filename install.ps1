# Ferbos Mini Integration Installer for Windows

Write-Host "Installing Ferbos Mini Integration..." -ForegroundColor Green

# Get Home Assistant config directory
if (-not $env:HA_CONFIG) {
    $env:HA_CONFIG = "C:\config"
}

# Create custom_components directory if it doesn't exist
$customComponentsPath = Join-Path $env:HA_CONFIG "custom_components"
if (-not (Test-Path $customComponentsPath)) {
    New-Item -ItemType Directory -Path $customComponentsPath -Force
}

# Download the integration
Write-Host "Downloading Ferbos Mini integration..." -ForegroundColor Yellow
$zipPath = Join-Path $env:TEMP "ferbos_mini.zip"
Invoke-WebRequest -Uri "https://github.com/ikhsanfauzan2812/ferbos-mini-addon/archive/main.zip" -OutFile $zipPath

# Extract the integration
$extractPath = Join-Path $env:TEMP "ferbos_mini_extract"
Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force

# Copy the integration
$sourcePath = Join-Path $extractPath "ferbos-mini-addon-main\custom_components\ferbos_mini"
$destPath = Join-Path $customComponentsPath "ferbos_mini"
Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force

# Clean up
Remove-Item -Path $zipPath -Force
Remove-Item -Path $extractPath -Recurse -Force

Write-Host "✅ Ferbos Mini integration installed successfully!" -ForegroundColor Green
Write-Host "Please restart Home Assistant and add the integration via Settings > Devices & Services" -ForegroundColor Cyan
