@echo off
echo Triggering WTA Completed Callback...
curl -X POST http://localhost:3000/api/v1/wta_completed ^
 -H "Content-Type: application/json" ^
 -d "{\"status\":\"completed\",\"message\":\"mock callback from trigger\"}"
echo Done.
pause
