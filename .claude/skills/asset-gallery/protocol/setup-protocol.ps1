# One-time setup for the gallery-open: protocol (Windows, user-level — no admin rights).
# Auto-detects THIS install's path, so it works wherever you unzipped the system.
#
#   Register:    powershell -ExecutionPolicy Bypass -File ".\.claude\skills\asset-gallery\protocol\setup-protocol.ps1"
#   Unregister:  powershell -ExecutionPolicy Bypass -File ".\.claude\skills\asset-gallery\protocol\setup-protocol.ps1" -Remove
#
# Writes HKCU\Software\Classes\gallery-open so the gallery's "Open folder" / "Edit copy"
# buttons launch File Explorer / a text editor instead of rendering in the browser.

param([switch]$Remove)

$key = 'HKCU:\Software\Classes\gallery-open'

if ($Remove) {
    if (Test-Path $key) { Remove-Item $key -Recurse -Force }
    Write-Host "gallery-open: protocol UNREGISTERED."
    return
}

# The handler sits next to this script — path resolved at run time, never hardcoded.
$handler = Join-Path $PSScriptRoot 'gallery-open.ps1'
if (-not (Test-Path -LiteralPath $handler)) {
    Write-Error "Handler not found next to this script: $handler"
    exit 1
}

$cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$handler`" `"%1`""

New-Item -Path $key -Force | Out-Null
Set-ItemProperty -Path $key -Name '(default)'   -Value 'URL:gallery-open protocol'
Set-ItemProperty -Path $key -Name 'URL Protocol' -Value ''
New-Item -Path "$key\shell\open\command" -Force | Out-Null
Set-ItemProperty -Path "$key\shell\open\command" -Name '(default)' -Value $cmd

Write-Host "gallery-open: protocol registered."
Write-Host "  handler: $handler"
Write-Host "  Next: click 'Open folder' or 'Edit copy' in any gallery and tick 'Always allow' the first time."
