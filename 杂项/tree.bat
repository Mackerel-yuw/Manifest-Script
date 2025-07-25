@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
set "root=%cd%"

:: 生成 UTF-8 无 BOM 的树形图
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
  "$root = Get-Location;" ^
  "function Show-Tree($path, $prefix) {" ^
    "$items = @(Get-ChildItem $path | Sort-Object { !$_.PSIsContainer }, Name);" ^
    "for ($i = 0; $i -lt $items.Count; $i++) {" ^
      "$last = ($i -eq $items.Count - 1);" ^
      "$name = $items[$i].Name;" ^
      "$line = if ($last) { '└─ ' } else { '├─ ' };" ^
      "$prefix + $line + $name | Out-File -Append -Encoding utf8 tree.txt;" ^
      "if ($items[$i].PSIsContainer) {" ^
        "$next = $prefix + $(if ($last) { '   ' } else { '│  ' });" ^
        "Show-Tree $items[$i].FullName $next;" ^
      "}" ^
    "}" ^
  "}" ^
  "Show-Tree $root ''"
echo 已生成 tree.txt
pause