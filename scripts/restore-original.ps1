#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"
$Res = "C:\Program Files\XTerminal\resources"
$Asar = Join-Path $Res "app.asar"
$Bak  = Join-Path $Res "app.asar.pre-vip-patch.bak"
if (-not (Test-Path -LiteralPath $Bak)) {
  throw "No backup found at $Bak — nothing to restore (or backup path differs)."
}
Get-Process -Name "XTerminal" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1
Copy-Item -LiteralPath $Bak -Destination $Asar -Force
Write-Host "Restored original app.asar from $Bak"
