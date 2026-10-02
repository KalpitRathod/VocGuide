@echo off
echo =====================================================
echo   VocGuide - AI Career Counselling Platform
echo   SIH 2026 - Problem Statement 26241
echo =====================================================
echo.
echo [1/2] Starting Ollama (if not running)...
start /B ollama serve >nul 2>&1
timeout /t 2 >nul

echo [2/2] Starting VocGuide server...
echo.
echo    Open your browser at: http://localhost:5000
echo    Admin Dashboard:      http://localhost:5000/#admin
echo    AI Counsellor:        http://localhost:5000/#counsellor
echo.
echo    Press Ctrl+C to stop the server
echo =====================================================
echo.
python app.py
pause
