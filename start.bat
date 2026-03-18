@echo off
echo Starting all services...
echo.
echo   EnerKey       -^> http://localhost:8000
echo   Pathfinder    -^> http://localhost:8001
echo   Record Box    -^> http://localhost:8002
echo   Salesforce    -^> http://localhost:8003
echo.

start "Salesforce Mock :8003" cmd /k cd /d "%~dp0salesforce_mock" ^& python -m uvicorn main:app --host 0.0.0.0 --port 8003 --reload
timeout /t 2 /nobreak >nul

start "Record Box :8002" cmd /k cd /d "%~dp0recordbox" ^& python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload
timeout /t 2 /nobreak >nul

start "Pathfinder :8001" cmd /k cd /d "%~dp0pathfinder" ^& python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
timeout /t 2 /nobreak >nul

start "EnerKey :8000" cmd /k cd /d "%~dp0enerkey" ^& python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
timeout /t 3 /nobreak >nul

start "" http://localhost:8000
