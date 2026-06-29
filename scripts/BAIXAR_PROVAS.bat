@echo off
chcp 65001 >nul
title Baixar Provas Anteriores (2023-2025)

echo.
echo ========================================================================
echo    BAIXAR PROVAS ANTERIORES - PCI CONCURSOS
echo    Anos: 2023, 2024, 2025
echo ========================================================================
echo.
echo Escolha uma opção:
echo.
echo   1. Cebraspe (15 provas)
echo   2. FCC (15 provas)
echo   3. FGV (15 provas)
echo   4. TODAS as bancas (45 provas total)
echo   5. Verificar provas baixadas
echo   6. Sair
echo.
set /p opcao="Digite o número da opção: "

if "%opcao%"=="1" goto cebraspe
if "%opcao%"=="2" goto fcc
if "%opcao%"=="3" goto fgv
if "%opcao%"=="4" goto todas
if "%opcao%"=="5" goto verificar
if "%opcao%"=="6" goto fim

:cebraspe
echo.
echo [CEBRASPE] Baixando provas...
python scrapers\provas_scraper.py cebraspe 15
goto estatisticas

:fcc
echo.
echo [FCC] Baixando provas...
python scrapers\provas_scraper.py fcc 15
goto estatisticas

:fgv
echo.
echo [FGV] Baixando provas...
python scrapers\provas_scraper.py fgv 15
goto estatisticas

:todas
echo.
echo [TODAS] Baixando provas de todas as bancas...
python scrapers\provas_scraper.py todas 15
goto estatisticas

:verificar
echo.
echo ========================================================================
echo    PROVAS BAIXADAS
echo ========================================================================
echo.
if exist provas\cebraspe (
    echo [CEBRASPE]
    dir provas\cebraspe\*.pdf /b 2>nul | find /c ".pdf"
    echo.
) else (
    echo [CEBRASPE] Nenhuma prova baixada ainda
    echo.
)

if exist provas\fcc (
    echo [FCC]
    dir provas\fcc\*.pdf /b 2>nul | find /c ".pdf"
    echo.
) else (
    echo [FCC] Nenhuma prova baixada ainda
    echo.
)

if exist provas\fgv (
    echo [FGV]
    dir provas\fgv\*.pdf /b 2>nul | find /c ".pdf"
    echo.
) else (
    echo [FGV] Nenhuma prova baixada ainda
    echo.
)
echo.
pause
goto fim

:estatisticas
echo.
echo ========================================================================
echo    ESTATÍSTICAS
echo ========================================================================
echo.
set total=0
for /f %%A in ('dir provas\cebraspe\*.pdf /b 2^>nul ^| find /c ".pdf"') do set ceb=%%A
for /f %%A in ('dir provas\fcc\*.pdf /b 2^>nul ^| find /c ".pdf"') do set fcc_n=%%A
for /f %%A in ('dir provas\fgv\*.pdf /b 2^>nul ^| find /c ".pdf"') do set fgv_n=%%A

echo   Cebraspe: %ceb% PDFs
echo   FCC: %fcc_n% PDFs
echo   FGV: %fgv_n% PDFs
echo.
set /a total=%ceb%+%fcc_n%+%fgv_n%
echo   TOTAL: %total% PDFs baixados
echo.
echo   Diretório: %CD%\provas\
echo ========================================================================
echo.
pause

:fim
echo.
echo Até logo!
timeout /t 2 >nul
exit
