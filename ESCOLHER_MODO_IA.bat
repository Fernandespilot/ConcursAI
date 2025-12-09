@echo off
echo.
echo ========================================
echo   ESCOLHER MODO DE IA
echo ========================================
echo.
echo Escolha o modo de operacao:
echo.
echo [1] AUTO   - Groq rapido + fallback local (RECOMENDADO)
echo [2] GROQ   - Apenas Groq (ultra rapido, sem fallback)
echo [3] LOCAL  - Apenas modelo local (offline, privado)
echo.
echo [4] Ver configuracao atual
echo [0] Cancelar
echo.
set /p choice="Escolha (0-4): "

if "%choice%"=="0" exit /b 0

if "%choice%"=="4" (
    echo.
    echo === CONFIGURACAO ATUAL ===
    findstr "USE_MODEL=" .env
    echo.
    pause
    exit /b 0
)

set "newmode="
if "%choice%"=="1" set "newmode=auto"
if "%choice%"=="2" set "newmode=groq"
if "%choice%"=="3" set "newmode=local"

if "%newmode%"=="" (
    echo [ERRO] Opcao invalida!
    pause
    exit /b 1
)

echo.
echo Alterando para modo: %newmode%
echo.

REM Substituir linha no .env
setlocal enabledelayedexpansion
(for /f "tokens=*" %%A in (.env) do (
    set "line=%%A"
    if "!line:~0,10!"=="USE_MODEL=" (
        echo USE_MODEL=%newmode%
    ) else (
        echo !line!
    )
)) > .env.tmp
move /y .env.tmp .env > nul

echo ========================================
echo   CONFIGURACAO ATUALIZADA!
echo ========================================
echo.

if "%newmode%"=="auto" (
    echo Modo AUTO ativado:
    echo - Tenta Groq primeiro ^(rapido^)
    echo - Fallback automatico para local
    echo - Nunca fica offline!
)

if "%newmode%"=="groq" (
    echo Modo GROQ ativado:
    echo - Apenas Groq Cloud ^(ultra rapido^)
    echo - Sem fallback local
    echo - Erro se Groq nao disponivel
    echo.
    echo AVISO: Certifique-se que GROQ_API_KEY esta configurada!
)

if "%newmode%"=="local" (
    echo Modo LOCAL ativado:
    echo - Apenas modelo local ^(Llama 8B^)
    echo - 100%% offline e privado
    echo - Respostas mais lentas ^(15-30s^)
)

echo.
echo Reinicie a API para aplicar:
echo    START_API_RAPIDO.bat
echo.
pause
