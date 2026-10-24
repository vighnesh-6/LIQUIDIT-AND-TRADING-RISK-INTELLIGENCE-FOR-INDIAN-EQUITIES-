@echo off
REM Daily Refresh Task Scheduler Batch Wrapper
REM ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

echo [%DATE% %TIME%] Starting daily refresh pipeline...

REM Change directory to project root
cd /d "%~dp0\.."

REM Activate virtual environment if present
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Run python refresh script
python scripts\daily_refresh.py >> logs\scheduler_%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%.log 2>&1

echo [%DATE% %TIME%] Daily refresh completed with exit code %ERRORLEVEL%.
