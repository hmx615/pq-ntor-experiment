@echo off
chcp 936 >nul
echo ============================================================
echo Windows Edge Mortal AI Paipu Analyzer
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found, please install Python 3.8+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
pip install selenium webdriver-manager -q

echo [2/3] Checking paipu_list.csv...
if not exist "paipu_list.csv" (
    echo [Error] paipu_list.csv not found
    pause
    exit /b 1
)

echo [3/3] Starting analyzer...
echo.
echo ============================================================
echo Notes:
echo 1. Edge browser will open automatically
echo 2. Wait for captcha to complete automatically
echo 3. Do not operate the browser during analysis
echo 4. Results saved to mortal_results_temp.csv after each game
echo 5. Press Ctrl+C to stop
echo ============================================================
echo.

python win_mortal_analyzer.py --limit 100

echo.
echo Done! Results saved in mortal_results.csv
pause
