@echo off
title Coleta e Indexacao Automatica - ConcursAI
color 0A

cd /d "%~dp0"

cls
echo ========================================
echo   COLETA E INDEXACAO AUTOMATICA
echo   ConcursAI - Sistema RAG
echo ========================================
echo.
echo Este script vai:
echo   1. Baixar PDFs do PCI Concursos
echo   2. Indexar automaticamente no ChromaDB
echo   3. Deixar pronto para consultas no RAG
echo.
echo ========================================
echo.

echo Escolha uma opcao:
echo.
echo   1. Cebraspe (5 concursos)
echo   2. FCC (5 concursos)
echo   3. FGV (5 concursos)
echo   4. TODAS as bancas (15 concursos total)
echo   5. Personalizar
echo.

set /p opcao="Digite o numero (1-5): "

if "%opcao%"=="1" (
    echo.
    echo [*] Coletando e indexando Cebraspe...
    python coletar_indexar_automatico.py cebraspe 5
) else if "%opcao%"=="2" (
    echo.
    echo [*] Coletando e indexando FCC...
    python coletar_indexar_automatico.py fcc 5
) else if "%opcao%"=="3" (
    echo.
    echo [*] Coletando e indexando FGV...
    python coletar_indexar_automatico.py fgv 5
) else if "%opcao%"=="4" (
    echo.
    echo [*] Coletando e indexando TODAS as bancas...
    python coletar_indexar_automatico.py todas 5
) else if "%opcao%"=="5" (
    echo.
    set /p banca="Digite a banca (cebraspe/fcc/fgv/todas): "
    set /p max="Maximo de concursos (1-20): "
    echo.
    echo [*] Coletando e indexando %banca% (%max% concursos)...
    python coletar_indexar_automatico.py %banca% %max%
) else (
    echo.
    echo [!] Opcao invalida!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   PROCESSO CONCLUIDO!
echo ========================================
echo.
echo Proximos passos:
echo   1. Verifique o log: coleta_automatica.log
echo   2. Veja os PDFs em: editais\
echo   3. Use o sistema RAG para consultas
echo.
pause
