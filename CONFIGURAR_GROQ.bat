@echo off
echo.
echo ========================================
echo   CONFIGURAR GROQ API - RESPOSTAS ULTRA RAPIDAS!
echo ========================================
echo.
echo 1. Abrindo pagina para obter sua chave gratuita...
start https://console.groq.com/keys
echo.
echo 2. Na pagina:
echo    - Faca login (pode usar Google/GitHub)
echo    - Clique em "Create API Key"
echo    - Copie a chave (comeca com gsk_...)
echo.
echo 3. Cole a chave abaixo:
echo.
set /p GROQ_KEY="GROQ_API_KEY: "
echo.

if "%GROQ_KEY%"=="" (
    echo [ERRO] Chave vazia! Tente novamente.
    pause
    exit /b 1
)

if not "%GROQ_KEY:~0,4%"=="gsk_" (
    echo [AVISO] Chave nao comeca com gsk_, mas vou salvar mesmo assim...
)

echo.
echo Salvando no arquivo .env...

REM Ler .env e substituir linha
setlocal enabledelayedexpansion
set "found=0"
(for /f "tokens=*" %%A in (.env) do (
    set "line=%%A"
    if "!line:~0,13!"=="GROQ_API_KEY=" (
        echo GROQ_API_KEY=%GROQ_KEY%
        set "found=1"
    ) else (
        echo !line!
    )
)) > .env.tmp

if "%found%"=="0" (
    echo. >> .env.tmp
    echo GROQ_API_KEY=%GROQ_KEY% >> .env.tmp
)

move /y .env.tmp .env > nul

echo.
echo ========================================
echo   CONFIGURACAO CONCLUIDA!
echo ========================================
echo.
echo Agora inicie a API:
echo    START_API_RAPIDO.bat
echo.
echo E teste no Dashboard:
echo    http://localhost:8000/dashboard.html
echo.
echo Suas respostas serao ULTRA RAPIDAS! (1-2 segundos)
echo.
pause
