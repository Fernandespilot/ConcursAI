@echo off
title Coleta de Provas e Gabaritos
color 0B

cd /d "%~dp0"

cls
echo ========================================
echo   COLETA DE PROVAS E GABARITOS
echo   Busca Ampliada - PCI Concursos
echo ========================================
echo.
echo Este script vai buscar MAIS concursos
echo para aumentar chances de encontrar:
echo   - Provas aplicadas
echo   - Gabaritos oficiais
echo   - Cadernos de questoes
echo.
echo ========================================
echo.

set /p confirma="Iniciar coleta ampliada (15 concursos por banca)? (S/N): "

if /i "%confirma%"=="S" (
    echo.
    echo [*] Iniciando coleta ampliada...
    echo [*] Isso vai demorar uns 20-30 minutos
    echo.
    
    python coletar_indexar_automatico.py todas 15
    
    echo.
    echo ========================================
    echo   COLETA CONCLUIDA!
    echo ========================================
    echo.
    echo Verificando resultados...
    echo.
    
    cd editais
    
    echo === PROVAS ===
    dir /b | findstr /i "prova" | find /c /v ""
    
    echo.
    echo === GABARITOS ===
    dir /b | findstr /i "gabarito" | find /c /v ""
    
    echo.
    echo === EDITAIS ===
    dir /b | findstr /i "edital" | find /c /v ""
    
    echo.
    echo Total de arquivos:
    dir *.pdf | find /c ".pdf"
    
    cd..
    
) else (
    echo.
    echo Operacao cancelada.
)

echo.
pause
