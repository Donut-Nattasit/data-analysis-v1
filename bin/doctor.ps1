# doctor.ps1 -- report local feature readiness without displaying secret values.

param(
    [switch]$RequireAllFeatures
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $env:LOCALAPPDATA 'venvs\data-analysis-v1\Scripts\python.exe'
$Checks = @()

function Add-Check {
    param(
        [string]$Feature,
        [bool]$Ready,
        [string]$Detail,
        [bool]$Core = $false
    )

    $script:Checks += [pscustomobject]@{
        Status = if ($Ready) { 'READY' } else { 'ACTION' }
        Feature = $Feature
        Detail = $Detail
        Core = $Core
        IsReady = $Ready
    }
}

function Test-EnvValue {
    param(
        [string]$Path,
        [string]$Name
    )

    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $escapedName = [regex]::Escape($Name)
    $line = Get-Content -LiteralPath $Path | Where-Object { $_ -match "^\s*$escapedName\s*=" } | Select-Object -Last 1
    if (-not $line) { return $false }
    $value = ($line -split '=', 2)[1].Trim().Trim('"').Trim("'")
    return (-not [string]::IsNullOrWhiteSpace($value)) -and (-not $value.StartsWith('your_', [System.StringComparison]::OrdinalIgnoreCase))
}

$PythonReady = Test-Path -LiteralPath $VenvPython
if ($PythonReady) {
    $version = & $VenvPython --version 2>&1
    $PythonReady = $LASTEXITCODE -eq 0 -and $version -match '^Python 3\.12(?:\.|$)'
}
$PythonDetail = if ($PythonReady) { 'Python 3.12 external environment detected.' } else { 'Run .\setup.ps1 to create the Python 3.12 environment.' }
Add-Check 'Core Python environment' $PythonReady $PythonDetail $true

$PackagesReady = $false
if ($PythonReady) {
    & $VenvPython -c "import numpy, pandas, requests, statsmodels, sklearn, matplotlib" 2>$null
    $PackagesReady = $LASTEXITCODE -eq 0
}
$PackagesDetail = if ($PackagesReady) { 'Required public Python packages import successfully.' } else { 'Run .\setup.ps1 to install the pinned public packages.' }
Add-Check 'Core Python packages' $PackagesReady $PackagesDetail $true

$GeneratedDirectoryNames = @('__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.hypothesis', '.ipynb_checkpoints', 'htmlcov', '.tox', '.nox')
$GeneratedFileNames = @('.coverage', 'coverage.xml')
$GeneratedItems = @(Get-ChildItem -LiteralPath $ProjectRoot -File -Force | Where-Object {
    $_.Extension -in @('.pyc', '.pyo') -or $_.Name -in $GeneratedFileNames
})
$SearchRoots = Get-ChildItem -LiteralPath $ProjectRoot -Directory -Force | Where-Object {
    $_.Name -notin @('.git', 'session', '.venv')
}
foreach ($Root in $SearchRoots) {
    if ($Root.Name -in $GeneratedDirectoryNames) { $GeneratedItems += $Root }
    $GeneratedItems += Get-ChildItem -LiteralPath $Root.FullName -Directory -Recurse -Force -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -in $GeneratedDirectoryNames
    }
    $GeneratedItems += Get-ChildItem -LiteralPath $Root.FullName -File -Recurse -Force -ErrorAction SilentlyContinue | Where-Object {
        $_.Extension -in @('.pyc', '.pyo') -or $_.Name -in $GeneratedFileNames
    }
}
$LocalVenvExists = Test-Path -LiteralPath (Join-Path $ProjectRoot '.venv')
$RepositoryClean = $GeneratedItems.Count -eq 0 -and -not $LocalVenvExists
$CleanDetail = if ($RepositoryClean) { 'Tool caches are external and no in-repository .venv was found.' } else { 'Run .\bin\clean.ps1; add -RemoveLocalVenv if an in-repository .venv exists.' }
Add-Check 'Lean repository layout' $RepositoryClean $CleanDetail $false

$RootEnv = Join-Path $ProjectRoot '.env'
$ParentEnv = Join-Path (Split-Path -Parent $ProjectRoot) '.env'
$EnvPath = if (Test-Path -LiteralPath $RootEnv) { $RootEnv } elseif (Test-Path -LiteralPath $ParentEnv) { $ParentEnv } else { $RootEnv }
$EnvExists = Test-Path -LiteralPath $EnvPath
$EnvDetail = if ($EnvExists) { '.env is present; values remain hidden.' } else { 'Run .\setup.ps1 to create .env, then enter credentials directly in that file.' }
Add-Check 'Local credential file' $EnvExists $EnvDetail $false

$CeicKey = Test-EnvValue $EnvPath 'CEIC_API_KEY'
$CeicClient = $false
if ($PythonReady) {
    & $VenvPython -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('ceic_api_client') else 1)" 2>$null
    $CeicClient = $LASTEXITCODE -eq 0
}
$CeicReady = $CeicKey -and $CeicClient
$CeicDetail = if ($CeicReady) { 'API key and authorized client are configured (secret hidden).' } else { 'Requires CEIC_API_KEY plus the authorized CEIC wheel; see SETUP.md.' }
Add-Check 'CEIC retrieval' $CeicReady $CeicDetail $false

$BotReady = Test-EnvValue $EnvPath 'BOT_API_TOKEN'
$BotDetail = if ($BotReady) { 'BOT_API_TOKEN is configured (value hidden).' } else { 'Register at the current BOT API portal and set BOT_API_TOKEN; see SETUP.md.' }
Add-Check 'Bank of Thailand retrieval' $BotReady $BotDetail $false

$EiaReady = Test-EnvValue $EnvPath 'EIA_API_KEY'
$EiaDetail = if ($EiaReady) { 'EIA_API_KEY is configured (value hidden).' } else { 'Register for the free EIA key and set EIA_API_KEY; see SETUP.md.' }
Add-Check 'EIA retrieval' $EiaReady $EiaDetail $false

$ImfReady = Test-EnvValue $EnvPath 'IMF_API_KEY'
$ImfDetail = if ($ImfReady) { 'IMF_API_KEY is configured (value hidden).' } else { 'Use the IMF API portal and set IMF_API_KEY; see SETUP.md.' }
Add-Check 'IMF retrieval' $ImfReady $ImfDetail $false

$SpReady = (Test-EnvValue $EnvPath 'SP_USERNAME') -and (Test-EnvValue $EnvPath 'SP_PASSWORD')
$SpDetail = if ($SpReady) { 'Both organization-authorized settings are configured (values hidden).' } else { 'Requires organization-authorized S&P Global API credentials; see SETUP.md.' }
Add-Check 'S&P Global retrieval' $SpReady $SpDetail $false

$X13Ready = Test-Path -LiteralPath (Join-Path $ProjectRoot 'bin\x13as.exe')
$X13Detail = if ($X13Ready) { 'bin\x13as.exe is present.' } else { 'Download the official Windows build and place its executable at bin\x13as.exe; see SETUP.md.' }
Add-Check 'X-13 seasonal adjustment' $X13Ready $X13Detail $false

$FontDir = Join-Path $ProjectRoot '.agents\skills\apply-nesdc-viz-template\assets\fonts\FCVision'
$FontReady = $false
if (Test-Path -LiteralPath $FontDir) {
    $FontReady = @(Get-ChildItem -LiteralPath $FontDir -File | Where-Object { $_.Extension -in @('.otf', '.ttf') }).Count -gt 0
}
$FontDetail = if ($FontReady) { 'Licensed font files are present.' } else { 'Obtain licensed font files through the authorized NESDC contact; see SETUP.md.' }
Add-Check 'FC Vision typography' $FontReady $FontDetail $false

Add-Check 'World Bank and Thailand MOC' $PythonReady 'No API key is required; these features use the core environment.' $false

$DatabaseRoot = Join-Path (Split-Path -Parent $ProjectRoot) 'database'
$SharedDbsReady = (Test-Path -LiteralPath (Join-Path $DatabaseRoot 'GTA.db')) -and (Test-Path -LiteralPath (Join-Path $DatabaseRoot 'LFS.db'))
Add-Check 'Optional shared databases' $SharedDbsReady 'GTA.db and LFS.db require separate internal authorization under ..\database\.' $false

Write-Host ''
$Checks | Select-Object Status, Feature, Detail | Format-Table -Wrap -AutoSize
Write-Host 'The doctor checks presence/configuration only. It never prints credential values and does not call licensed APIs.'

$CoreMissing = @($Checks | Where-Object { $_.Core -and -not $_.IsReady }).Count -gt 0
$AnyMissing = @($Checks | Where-Object { -not $_.IsReady }).Count -gt 0
if ($CoreMissing -or ($RequireAllFeatures -and $AnyMissing)) { exit 1 }
exit 0
