# Central Python launcher for data-analysis_v1.
# Usage: .\bin\python.ps1 [script.py] [args...]

$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$CacheRoot = Join-Path $env:LOCALAPPDATA 'data-analysis-v1\cache'
$env:PYTHONPATH = $ProjectRoot
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:PYTHONPYCACHEPREFIX = Join-Path $CacheRoot 'python'
$env:MPLCONFIGDIR = Join-Path $CacheRoot 'matplotlib'
$env:NUMBA_CACHE_DIR = Join-Path $CacheRoot 'numba'
$env:JOBLIB_TEMP_FOLDER = Join-Path $CacheRoot 'joblib'

# Keep machine-generated caches out of the repository, which may be synced by
# OneDrive. The tools create their own child directories as needed.
if (-not (Test-Path -LiteralPath $CacheRoot)) {
    New-Item -ItemType Directory -Path $CacheRoot -Force | Out-Null
}

$Candidates = @(
    (Join-Path $env:LOCALAPPDATA 'venvs\data-analysis-v1\Scripts\python.exe'),
    (Join-Path $ProjectRoot '.venv\Scripts\python.exe')
)

$PythonExec = $null
foreach ($Exec in $Candidates) {
    if (Test-Path -LiteralPath $Exec) {
        $PythonExec = [System.IO.Path]::GetFullPath($Exec)
        break
    }
}

if (-not $PythonExec) {
    Write-Error 'Python virtual environment not found.'
    Write-Host 'Run .\setup.ps1 from the project root to build it.' -ForegroundColor Yellow
    exit 1
}

& $PythonExec $args
exit $LASTEXITCODE
