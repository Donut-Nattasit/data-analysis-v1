# Central Python launcher for data-analysis_v1.
# Usage: .\bin\python.ps1 [script.py] [args...]

$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$env:PYTHONPATH = $ProjectRoot
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

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
