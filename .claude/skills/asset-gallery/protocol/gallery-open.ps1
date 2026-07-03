# gallery-open protocol handler
# Receives a gallery-open:<url-encoded-absolute-path> URI from the browser.
# Folders open in File Explorer; files open in a text editor.
# Safety: refuses any path outside the Marketing AI System root.

param([string]$Uri)

$raw = $Uri -replace '^gallery-open:/*', ''
$path = [Uri]::UnescapeDataString($raw) -replace '/', '\'

# This script lives at <root>\.claude\skills\asset-gallery\protocol\gallery-open.ps1,
# so the install root is four levels up — auto-detected, works wherever installed.
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
if (-not $path.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
    exit 1
}

if (Test-Path -LiteralPath $path -PathType Container) {
    Start-Process explorer.exe -ArgumentList "`"$path`""
}
elseif (Test-Path -LiteralPath $path) {
    # Prefer VS Code if available (better markdown editing), else Notepad
    $code = Get-Command code -ErrorAction SilentlyContinue
    if ($code) {
        Start-Process -FilePath $code.Source -ArgumentList "`"$path`"" -WindowStyle Hidden
    } else {
        Start-Process notepad.exe -ArgumentList "`"$path`""
    }
}
