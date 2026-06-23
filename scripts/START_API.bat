@echo off
chcp 65001 > nul
title API ConcursAI - FastAPI Server
color 0A

cd /d "%~dp0"

cls
echo ============================================================
echo  🚀 API FASTAPI - ConcursAI
echo ============================================================
echo.
echo  URL: http://localhost:8000
echo  Docs: http://localhost:8000/docs
echo  Redoc: http://localhost:8000/redoc
echo.
echo  Pressione CTRL+C para parar o servidor
echo ============================================================
echo.

"C:/Users/FabLab Maker/Downloads/FAB/.venv/Scripts/python.exe" -m uvicorn api_fastapi:app --host 0.0.0.0 --port 8000 --reload

pause
