@echo off
chcp 65001 >nul
echo Stopping Gamekaren server...
powershell -Command "$p = Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*runssl.py*' }; if ($p) { $p | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host 'Stopped process ID:' $_.ProcessId }; } else { Write-Host 'No matching process found.' }"
echo Done.
pause