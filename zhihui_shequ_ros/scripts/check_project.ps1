$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$pkg = Join-Path $root "src\zhihui_shequ_sim"

python -m py_compile `
  (Join-Path $pkg "scripts\mission_controller.py") `
  (Join-Path $pkg "scripts\vision_node.py") `
  (Join-Path $pkg "scripts\vision_tools.py")

[xml](Get-Content -LiteralPath (Join-Path $pkg "package.xml")) | Out-Null
[xml](Get-Content -LiteralPath (Join-Path $pkg "launch\simulation.launch")) | Out-Null
[xml](Get-Content -LiteralPath (Join-Path $pkg "urdf\smart_car.xacro")) | Out-Null
[xml](Get-Content -LiteralPath (Join-Path $pkg "worlds\smart_community.world")) | Out-Null

Write-Host "Project static checks passed."
