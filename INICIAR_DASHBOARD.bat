@echo off
chcp 65001 > nul
echo ============================================================
echo  🎯 DASHBOARD ANÁLISE DE BANCAS
echo ============================================================
echo.
echo Iniciando sistema completo:
echo   1. API Backend
echo   2. Dashboard Web
echo.
echo O dashboard será aberto automaticamente no navegador.
echo.
echo ============================================================
echo.

cd /d "%~dp0"

REM Instalar dependências se necessário
pip install flask flask-cors >nul 2>&1

REM Iniciar API em background
echo 🔄 Iniciando API...
start /B python api_dashboard.py

REM Aguardar API iniciar
timeout /t 3 /nobreak >nul

REM Abrir dashboard no navegador
echo 🌐 Abrindo dashboard...
start dashboard_bancas.html

echo.
echo ============================================================
echo  ✅ Sistema iniciado!
echo ============================================================
echo.
echo Dashboard: dashboard_bancas.html
echo API: http://localhost:5000
echo.
echo Pressione qualquer tecla para encerrar...
pause >nul

REM Matar processo Python ao sair
taskkill /F /IM python.exe /FI "WINDOWTITLE eq api_dashboard*" >nul 2>&1
