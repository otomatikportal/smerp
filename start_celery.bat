@echo off
echo Starting Celery Worker and Beat for SMERP Exchange Rates...

REM Start Redis (assuming it's installed and in PATH)
echo Starting Redis...
start "Redis Server" redis-server

REM Wait a moment for Redis to start
timeout /t 3

REM Start Celery Worker
echo Starting Celery Worker...
start "Celery Worker" C:/Users/omer_/Desktop/smerp/.venv/Scripts/python.exe -m celery -A config worker --loglevel=info

REM Start Celery Beat (scheduler)
echo Starting Celery Beat...
start "Celery Beat" C:/Users/omer_/Desktop/smerp/.venv/Scripts/python.exe -m celery -A config beat --loglevel=info

echo All services started!
echo - Redis Server
echo - Celery Worker  
echo - Celery Beat (Scheduler)
echo.
echo Exchange rates will be fetched daily at 5:00 AM
pause
