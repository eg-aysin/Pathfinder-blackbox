@echo off
echo Installing dependencies for all services...

cd enerkey
pip install -r requirements.txt
cd ..

cd pathfinder
pip install -r requirements.txt
cd ..

cd recordbox
pip install -r requirements.txt
cd ..

cd salesforce_mock
pip install -r requirements.txt
cd ..

echo.
echo All dependencies installed!
pause
