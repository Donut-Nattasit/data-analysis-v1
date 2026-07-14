# clean.ps1 -- remove disposable tool caches from the repository.
#
# Session outputs and local configuration are never touched. An accidental
# in-repository virtual environment is removed only with -RemoveLocalVenv.

param(
    [switch]$RemoveLocalVenv
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$ProjectPrefix = $ProjectRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
$CacheDirectoryNames = @(
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    '.ruff_cache',
    '.hypothesis',
    '.ipynb_checkpoints',
    'htmlcov',
    '.tox',
    '.nox'
)
$GeneratedFileNames = @('.coverage', 'coverage.xml')
$Removed = 0

function Assert-DisposableProjectPath {
    param([string]$Path)

    $Resolved = [System.IO.Path]::GetFullPath($Path)
    if (-not $Resolved.StartsWith($ProjectPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path outside the repository: $Resolved"
    }
    if ($Resolved.StartsWith((Join-Path $ProjectRoot '.git') + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path under .git: $Resolved"
    }
    if ($Resolved.StartsWith((Join-Path $ProjectRoot 'session') + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path under session: $Resolved"
    }
    return $Resolved
}

# Never traverse Git metadata, conversation outputs, or a local environment.
$SearchRoots = Get-ChildItem -LiteralPath $ProjectRoot -Directory -Force | Where-Object {
    $_.Name -notin @('.git', 'session', '.venv')
}

$CacheDirectories = @()
$GeneratedFiles = @(Get-ChildItem -LiteralPath $ProjectRoot -File -Force | Where-Object {
    $_.Extension -in @('.pyc', '.pyo') -or $_.Name -in $GeneratedFileNames
})
foreach ($Root in $SearchRoots) {
    if ($Root.Name -in $CacheDirectoryNames) {
        $CacheDirectories += $Root
        continue
    }
    $CacheDirectories += Get-ChildItem -LiteralPath $Root.FullName -Directory -Recurse -Force -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -in $CacheDirectoryNames
    }
    $GeneratedFiles += Get-ChildItem -LiteralPath $Root.FullName -File -Recurse -Force -ErrorAction SilentlyContinue | Where-Object {
        $_.Extension -in @('.pyc', '.pyo') -or $_.Name -in $GeneratedFileNames
    }
}

foreach ($Directory in ($CacheDirectories | Sort-Object { $_.FullName.Length } -Descending)) {
    if (-not (Test-Path -LiteralPath $Directory.FullName)) { continue }
    $SafePath = Assert-DisposableProjectPath $Directory.FullName
    Remove-Item -LiteralPath $SafePath -Recurse -Force
    $Removed++
}

foreach ($File in $GeneratedFiles) {
    if (-not (Test-Path -LiteralPath $File.FullName)) { continue }
    $SafePath = Assert-DisposableProjectPath $File.FullName
    Remove-Item -LiteralPath $SafePath -Force
    $Removed++
}

$LocalVenv = Join-Path $ProjectRoot '.venv'
if (Test-Path -LiteralPath $LocalVenv) {
    if ($RemoveLocalVenv) {
        $SafePath = Assert-DisposableProjectPath $LocalVenv
        if ($SafePath -ne [System.IO.Path]::GetFullPath($LocalVenv)) {
            throw 'Local virtual-environment path verification failed.'
        }
        Remove-Item -LiteralPath $SafePath -Recurse -Force
        $Removed++
        Write-Host 'Removed the in-repository .venv; setup uses the external environment.'
    } else {
        Write-Warning 'An in-repository .venv remains. Run .\bin\clean.ps1 -RemoveLocalVenv to remove it explicitly.'
    }
}

if ($Removed -eq 0) {
    Write-Host 'Repository is already free of disposable tool caches.'
} else {
    Write-Host "Removed $Removed disposable cache item(s) from the repository."
}
