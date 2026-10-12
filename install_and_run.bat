@echo off
echo ============================================
echo      Sidekick - Install ^& Run
echo ============================================
echo.

echo Installing dependencies...
pip install -r requirements.txt
echo.

echo Starting Sidekick...
pythonw main.pyw
