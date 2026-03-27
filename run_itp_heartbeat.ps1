param(
    [string]$Watchlist = "$PSScriptRoot\references\itp_watchlist.example.json",
    [string]$State = "$PSScriptRoot\state\itp_state.json",
    [string]$Timeframe = "15M",
    [int]$Bars = 5,
    [int]$TrimOngoing = 1,
    [int]$BatchSize = 9,
    [double]$SleepBetweenBatches = 2.0
)

$ErrorActionPreference = "Stop"
$repoRoot = $PSScriptRoot
$env:PYTHONPATH = $repoRoot

Push-Location $repoRoot
try {
    python .\scripts\itp_scan.py `
        --watchlist $Watchlist `
        --state $State `
        --timeframe $Timeframe `
        --bars $Bars `
        --trim-ongoing $TrimOngoing `
        --batch-size $BatchSize `
        --sleep-between-batches $SleepBetweenBatches
}
finally {
    Pop-Location
}
