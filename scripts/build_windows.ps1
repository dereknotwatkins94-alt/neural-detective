$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Python 3.11+ is required." }
}
$python = ".venv\Scripts\python.exe"
& $python -m pip install -r requirements.txt "pyinstaller>=6.16,<7"
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
& $python -m ml.train_model
if ($LASTEXITCODE -ne 0) { throw "Model training failed." }
& $python -m PyInstaller --noconfirm NeuralDetective.spec
if ($LASTEXITCODE -ne 0) { throw "Build failed." }
Write-Host "Ready: dist\NeuralDetective\NeuralDetective.exe"
Write-Host "Distribute the entire dist\NeuralDetective folder."
