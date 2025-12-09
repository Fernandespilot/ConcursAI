@echo off
echo ========================================
echo  ConcursAI - Inicio Rapido da API
echo ========================================
echo.
echo Iniciando API FastAPI sem auto-reload...
echo Modelo Llama 3.1 8B sera carregado
echo.

cd /d "%~dp0"
"C:\Users\FabLab Maker\Downloads\FAB\.venv\Scripts\python.exe" -m uvicorn api_fastapi:app --host 0.0.0.0 --port 8000 --no-access-log

pause
