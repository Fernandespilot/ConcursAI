@echo off
chcp 65001 > nul
echo ============================================================
echo  🔧 CORREÇÃO DE DEPENDÊNCIAS - ConcursAI
echo ============================================================
echo.
echo Este script irá corrigir os avisos encontrados nas APIs.
echo.
echo Problemas identificados:
echo   1. HuggingFace Hub versão incompatível
echo   2. LangChain deprecations
echo   3. APScheduler não instalado
echo   4. Ollama servidor offline
echo.
echo ============================================================
echo.

cd /d "%~dp0"

echo 🔄 Etapa 1/4: Corrigindo HuggingFace Hub...
"C:/Users/FabLab Maker/Downloads/FAB/.venv/Scripts/python.exe" -m pip install "huggingface-hub<1.0" --force-reinstall -q
if %ERRORLEVEL% EQU 0 (
    echo ✅ HuggingFace Hub corrigido
) else (
    echo ⚠️ Falha ao corrigir HuggingFace Hub
)
echo.

echo 🔄 Etapa 2/4: Atualizando LangChain Ollama...
"C:/Users/FabLab Maker/Downloads/FAB/.venv/Scripts/python.exe" -m pip install langchain-ollama -U -q
if %ERRORLEVEL% EQU 0 (
    echo ✅ LangChain Ollama atualizado
) else (
    echo ⚠️ Falha ao atualizar LangChain Ollama
)
echo.

echo 🔄 Etapa 3/5: Instalando APScheduler...
"C:/Users/FabLab Maker/Downloads/FAB/.venv/Scripts/python.exe" -m pip install apscheduler -q
if %ERRORLEVEL% EQU 0 (
    echo ✅ APScheduler instalado
) else (
    echo ⚠️ Falha ao instalar APScheduler
)
echo.

echo 🔄 Etapa 4/5: Instalando Scikit-learn para ML...
"C:/Users/FabLab Maker/Downloads/FAB/.venv/Scripts/python.exe" -m pip install scikit-learn joblib -q
if %ERRORLEVEL% EQU 0 (
    echo ✅ Scikit-learn instalado
) else (
    echo ⚠️ Falha ao instalar Scikit-learn
)
echo.

echo 🔄 Etapa 5/5: Verificando Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Ollama está rodando
) else (
    echo ⚠️ Ollama não está rodando
    echo.
    echo Para iniciar Ollama, execute em outro terminal:
    echo   ollama serve
    echo.
)
echo.

echo ============================================================
echo  📊 TESTANDO APIs
echo ============================================================
echo.

echo 🧪 Testando API Dashboard...
"C:/Users/FabLab Maker/Downloads/FAB/.venv/Scripts/python.exe" -c "from api_dashboard import app; print('✅ API Dashboard: OK')" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ API Dashboard funcional
) else (
    echo ❌ API Dashboard com problemas
)
echo.

echo 🧪 Testando API FastAPI...
"C:/Users/FabLab Maker/Downloads/FAB/.venv/Scripts/python.exe" -c "from api_fastapi import app; print('✅ API FastAPI: OK')" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ API FastAPI funcional
) else (
    echo ❌ API FastAPI com problemas
)
echo.

echo ============================================================
echo  ✅ CORREÇÃO CONCLUÍDA!
echo ============================================================
echo.
echo Próximos passos:
echo   1. Se Ollama não está rodando: ollama serve
echo   2. Processar questões: PROCESSAR_QUESTOES_GABARITOS.bat
echo   3. Iniciar dashboard: INICIAR_DASHBOARD.bat
echo   4. Iniciar API: START_API.bat
echo.
echo ============================================================
pause
