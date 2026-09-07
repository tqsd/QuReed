param([switch]$Web, [int]$Port = 8765, [string]$Scheme = 'experiment.json')
$ErrorActionPreference = 'Stop'
$projectDirectory = $PSScriptRoot
$qureedPython = Join-Path (Split-Path -Parent $projectDirectory) '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $qureedPython)) {
    throw "The shared QuReed interpreter is missing: $qureedPython"
}
Push-Location -LiteralPath $projectDirectory
try {
    if ($Web) {
        & $qureedPython -m bocda_model.gui --web --port $Port --scheme $Scheme
    } else {
        & $qureedPython -m bocda_model.gui --scheme $Scheme
    }
    if ($LASTEXITCODE -ne 0) { throw "QuReed GUI exited with code $LASTEXITCODE" }
} finally {
    Pop-Location
}
