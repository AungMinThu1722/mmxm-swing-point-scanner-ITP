param(
    [string]$Destination = "$HOME\.codex\skills\mmxm-swing-point-scanner-ITP",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

if ((Test-Path $Destination) -and -not $Force) {
    throw "Destination '$Destination' already exists. Re-run with -Force to replace it."
}

if (Test-Path $Destination) {
    Remove-Item -Recurse -Force $Destination
}

New-Item -ItemType Directory -Force -Path $Destination | Out-Null
Copy-Item -Path (Join-Path $PSScriptRoot '*') -Destination $Destination -Recurse -Force

Write-Host "Installed skill to $Destination"
