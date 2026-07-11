#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Res = "C:\Program Files\XTerminal\resources"
$Asar = Join-Path $Res "app.asar"
$Bak  = Join-Path $Res "app.asar.pre-vip-patch.bak"
$MainPatch = Join-Path $RepoRoot "patches\main-index.js"
$SshPatch  = Join-Path $RepoRoot "patches\feature-session-ssh-BwM8gFj5.js"

foreach ($p in @($Asar, $MainPatch, $SshPatch)) {
  if (-not (Test-Path -LiteralPath $p)) { throw "Missing: $p" }
}

Write-Host "Stopping XTerminal if running..."
Get-Process -Name "XTerminal" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

if (-not (Test-Path -LiteralPath $Bak)) {
  Copy-Item -LiteralPath $Asar -Destination $Bak -Force
  Write-Host "Backup created: $Bak"
} else {
  Write-Host "Backup already exists: $Bak"
}

$Work = Join-Path $env:TEMP ("xterminal-vip-asar-" + [guid]::NewGuid().ToString("N"))
$Out  = Join-Path $env:TEMP "xterminal-app-vip-patched.asar"
New-Item -ItemType Directory -Path $Work | Out-Null

try {
  Write-Host "Extracting stock asar..."
  npx --yes asar extract $Asar $Work
  if ($LASTEXITCODE -ne 0) { throw "asar extract failed" }

  $dstMain = Join-Path $Work "dist\main\index.js"
  $dstSsh  = Join-Path $Work "dist\render\assets\feature-session-ssh-BwM8gFj5.js"
  if (-not (Test-Path -LiteralPath $dstMain)) { throw "Unexpected asar layout (no dist/main/index.js) — wrong XTerminal version?" }
  if (-not (Test-Path -LiteralPath $dstSsh))  { throw "Unexpected asar layout (no feature-session-ssh bundle) — wrong XTerminal version?" }

  Copy-Item -LiteralPath $MainPatch -Destination $dstMain -Force
  Copy-Item -LiteralPath $SshPatch  -Destination $dstSsh  -Force

  Write-Host "Packing patched asar..."
  if (Test-Path -LiteralPath $Out) { Remove-Item -LiteralPath $Out -Force }
  npx --yes asar pack $Work $Out
  if ($LASTEXITCODE -ne 0) { throw "asar pack failed" }

  Copy-Item -LiteralPath $Out -Destination $Asar -Force
  Write-Host "Installed patched asar -> $Asar"

  $cache = Join-Path $env:APPDATA "xterminal\.cacheJs"
  if (Test-Path -LiteralPath $cache) {
    Remove-Item -LiteralPath $cache -Recurse -Force
    Write-Host "Cleared decrypt cache: $cache"
  }

  Write-Host ""
  Write-Host "DONE. Launch XTerminal."
  Write-Host "Optional: XTerminal.exe --remote-debugging-port=9222"
  Write-Host "Then: window.__XTERMINAL_E2E__.setVipState(true)"
}
finally {
  if (Test-Path -LiteralPath $Work) { Remove-Item -LiteralPath $Work -Recurse -Force -ErrorAction SilentlyContinue }
  if (Test-Path -LiteralPath $Out)  { Remove-Item -LiteralPath $Out  -Force -ErrorAction SilentlyContinue }
}
