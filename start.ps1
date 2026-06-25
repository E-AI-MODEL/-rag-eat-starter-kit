$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$pythonCommand = $null
$pythonArgs = @()

if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCommand = "py"
    $pythonArgs = @("-3")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCommand = "python"
} else {
    Write-Error "Python 3 is required, but neither 'py' nor 'python' was found."
    exit 1
}

& $pythonCommand @pythonArgs -m venv .venv

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Could not find the virtual environment Python at $venvPython."
    exit 1
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -e ".[web]"

New-Item -ItemType Directory -Force -Path "knowledge" | Out-Null

if (-not $env:RAGKIT_CORPUS) {
    $env:RAGKIT_CORPUS = "knowledge"
}
if (-not $env:RAGKIT_USER_GROUPS) {
    $env:RAGKIT_USER_GROUPS = "public,support"
}

& $venvPython run.py validate
& $venvPython -m streamlit run web_app.py
