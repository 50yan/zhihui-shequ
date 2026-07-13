$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$pkg = Join-Path $root "src\zhihui_shequ_sim"

$pythonFiles = Get-ChildItem -LiteralPath (Join-Path $pkg "scripts") -Filter "*.py"
python -m py_compile $pythonFiles.FullName

[xml](Get-Content -LiteralPath (Join-Path $pkg "package.xml")) | Out-Null

$xmlFiles = @()
$xmlFiles += Get-ChildItem -LiteralPath (Join-Path $pkg "launch") -Filter "*.launch"
$xmlFiles += Get-ChildItem -LiteralPath (Join-Path $pkg "urdf") -Filter "*.xacro"
$xmlFiles += Get-ChildItem -LiteralPath (Join-Path $pkg "worlds") -Filter "*.world"
$xmlFiles += Get-ChildItem -LiteralPath (Join-Path $pkg "tests") -Filter "*.test"
foreach ($file in $xmlFiles) {
  [xml](Get-Content -LiteralPath $file.FullName) | Out-Null
}

$yamlAvailable = python -c "import importlib.util; print('1' if importlib.util.find_spec('yaml') else '0')"
if ($yamlAvailable.Trim() -eq "1") {
  python -m unittest discover -s (Join-Path $pkg "tests") -p "test_*.py"
} else {
  Write-Warning "PyYAML is not installed in this Windows Python; YAML contract tests were skipped."
}

Write-Host "Project static checks passed."
