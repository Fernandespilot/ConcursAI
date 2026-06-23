@echo off
chcp 65001 > nul
echo ============================================================
echo  🧪 TESTE DOS MODELOS ML
echo ============================================================
echo.
echo Testando:
echo   1. Classificador de Bancas
echo   2. Preditor de Temas
echo.
echo ============================================================
echo.

cd /d "%~dp0"

"C:/Users/FabLab Maker/Downloads/FAB/.venv/Scripts/python.exe" testar_modelos_ml.py

echo.
pause
