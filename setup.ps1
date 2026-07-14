# setup.ps1 -- build this workspace's machine-local Python environment.
#
# The repository may live in a synced folder, but virtual environments contain
# machine-specific paths and many small files. This script therefore creates the
# environment outside the repository at:
#   %LOCALAPPDATA%\venvs\data-analysis-v1
#
# Usage:
#   .\setup.ps1                  # create or update the environment
#   .\setup.ps1 -Force           # delete and rebuild only the external environment
#   .\setup.ps1 -RemoveLocalVenv # also remove an accidental repository .venv

param(
    [switch]$Force,
    [switch]$RemoveLocalVenv
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$ExpectedVenvDir = Join-Path $env:LOCALAPPDATA 'venvs\data-analysis-v1'
$VenvDir = [System.IO.Path]::GetFullPath($ExpectedVenvDir)
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'

# 1. Find Python 3.12 without constructing a shell command string.
$PythonCommand = $null
$PythonArgs = @()
$PythonVersion = $null
$Candidates = @(
    [pscustomobject]@{ Command = 'py'; Args = @('-3.12') },
    [pscustomobject]@{ Command = 'python3.12'; Args = @() },
    [pscustomobject]@{ Command = 'python'; Args = @() }
)

foreach ($Candidate in $Candidates) {
    $Resolved = Get-Command -Name $Candidate.Command -ErrorAction SilentlyContinue
    if (-not $Resolved) { continue }

    $CandidateArgs = $Candidate.Args
    try {
        $Version = & $Resolved.Source @CandidateArgs --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $Version -match '^Python 3\.12(?:\.|$)') {
            $PythonCommand = $Resolved.Source
            $PythonArgs = $CandidateArgs
            $PythonVersion = $Version
            break
        }
    } catch {
        continue
    }
}

if (-not $PythonCommand) {
    Write-Error 'Python 3.12 was not found. Install the Windows release from https://www.python.org/downloads/windows/, enable the Python launcher or PATH option, and rerun setup.ps1.'
}
Write-Host "Using Python: $PythonCommand $($PythonArgs -join ' ') ($PythonVersion)"

# 2. Rebuild the dedicated external environment only when explicitly requested.
if ($Force -and (Test-Path -LiteralPath $VenvDir)) {
    if ($VenvDir -ne [System.IO.Path]::GetFullPath($ExpectedVenvDir)) {
        Write-Error 'External virtual-environment path verification failed.'
    }
    Write-Host "Removing external environment at $VenvDir ..."
    Remove-Item -LiteralPath $VenvDir -Recurse -Force
}

# 3. Create or validate the environment.
if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Host "Creating virtual environment at $VenvDir ..."
    & $PythonCommand @PythonArgs -m venv $VenvDir
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $VenvPython)) {
        Write-Error 'Virtual environment creation failed.'
    }
} else {
    $ExistingVersion = & $VenvPython --version 2>&1
    if ($LASTEXITCODE -ne 0 -or $ExistingVersion -notmatch '^Python 3\.12(?:\.|$)') {
        Write-Error "The existing environment uses '$ExistingVersion'. Rerun .\setup.ps1 -Force to rebuild it with Python 3.12."
    }
    Write-Host "Using existing virtual environment at $VenvDir"
}

# An in-repository environment is ignored and removed only when explicitly requested.
$LocalVenv = Join-Path $ProjectRoot '.venv'
if ((Test-Path -LiteralPath $LocalVenv) -and -not $RemoveLocalVenv) {
    Write-Warning "An in-repository .venv exists at $LocalVenv. The external environment at $VenvDir is preferred."
}

# 4. Reconstruct local output folders retained in Git only by placeholder files.
$SessionDir = Join-Path $ProjectRoot 'session'
if (-not (Test-Path -LiteralPath $SessionDir)) {
    New-Item -ItemType Directory -Path $SessionDir | Out-Null
}

# Create a local placeholder credential file without ever overwriting a user's values.
$EnvFile = Join-Path $ProjectRoot '.env'
if (-not (Test-Path -LiteralPath $EnvFile)) {
    Copy-Item -LiteralPath (Join-Path $ProjectRoot '.env.example') -Destination $EnvFile
    Write-Host 'Created .env from the safe placeholder template.'
    Write-Warning 'Add only credentials you are authorized to use. Enter them directly in .env; never paste secrets into AI chat.'
}

# 5. Install public dependencies.
Write-Host ''
Write-Host 'Installing public dependencies...'
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { Write-Error 'pip upgrade failed.' }
& $VenvPython -m pip install -r (Join-Path $ProjectRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { Write-Error 'Public dependency installation failed.' }

# 6. Install the proprietary CEIC client only when an authorized wheel is local.
$WheelsDir = Join-Path $ProjectRoot 'wheels'
$CeicWheel = $null
if (Test-Path -LiteralPath $WheelsDir) {
    $CeicWheel = Get-ChildItem -LiteralPath $WheelsDir -Filter 'ceic_api_client-2.11.5.396-*.whl' -File | Select-Object -First 1
}
if ($CeicWheel) {
    Write-Host ''
    Write-Host "Installing optional CEIC client from $($CeicWheel.Name)..."
    & $VenvPython -m pip install $CeicWheel.FullName
    if ($LASTEXITCODE -ne 0) { Write-Error 'CEIC client installation failed.' }
} else {
    Write-Warning 'Authorized CEIC wheel not found in wheels/. Core setup is complete, but fetch-ceic is unavailable. See SETUP.md.'
}

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot 'bin\x13as.exe'))) {
    Write-Warning 'bin\x13as.exe was not found. Core setup is complete, but x13-sa is unavailable. See SETUP.md.'
}

& $VenvPython -m pip check
if ($LASTEXITCODE -ne 0) { Write-Error 'Installed dependency validation failed.' }

# Remove safe tool caches left by direct Python/test commands. Conversation
# outputs, credentials, downloaded data, and licensed files are never touched.
Write-Host ''
Write-Host 'Cleaning disposable repository caches...'
$CleanArgs = @()
if ($RemoveLocalVenv) { $CleanArgs += '-RemoveLocalVenv' }
& (Join-Path $ProjectRoot 'bin\clean.ps1') @CleanArgs

Write-Host ''
Write-Host 'Core Python setup is ready.' -ForegroundColor Green
Write-Host 'Run scripts via: .\bin\python.ps1 <script.py>'
& $VenvPython -c "import sys; print('venv python ->', sys.executable)"

Write-Host ''
Write-Host 'Feature readiness:'
& (Join-Path $ProjectRoot 'bin\doctor.ps1')
Write-Host ''
Write-Host 'If any desired feature needs action, follow SETUP.md and rerun setup.ps1.'
