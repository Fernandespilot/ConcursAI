@echo off
title Teste ConcursAI - Diagnostico
color 0B

cd /d "%~dp0"

cls
echo ========================================
echo    ConcursAI - Diagnostico do Sistema
echo ========================================
echo.

echo [1/4] Verificando Python...
python --version
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    pause
    exit /b 1
)
echo.

echo [2/4] Verificando dependencias principais...
python -c "import fastapi; import chromadb; import sentence_transformers; print('✅ Dependencias OK')"
if errorlevel 1 (
    echo [ERRO] Faltam dependencias! Execute: pip install -r requirements.txt
    pause
    exit /b 1
)
echo.

echo [3/4] Verificando modelo Llama...
if exist "models\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf" (
    echo ✅ Modelo encontrado
) else (
    echo ⚠️ Modelo nao encontrado em models\
)
echo.

echo [4/4] Testando API (5 segundos)...
echo.
echo Iniciando servidor...
timeout /t 2 /nobreak >nul
start /B python api_fastapi.py >api_test.log 2>&1

timeout /t 5 /nobreak

echo.
echo Testando endpoint de status...
curl -s http://localhost:8000/status 2>nul
if errorlevel 1 (
    echo.
    echo ⚠️ API pode estar demorando para iniciar
    echo Verifique o arquivo api_test.log para detalhes
) else (
    echo.
    echo ✅ API respondendo!
)

echo.
echo ========================================
echo    Diagnostico Concluido
echo ========================================
echo.
echo Para iniciar o sistema normalmente, use:
echo    START_API.bat
echo.
echo Para ver logs detalhados:
echo    type api_test.log
echo.

pause
