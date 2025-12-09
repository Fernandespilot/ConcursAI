@echo off
REM Script para iniciar scraping automático em segundo plano
echo ========================================
echo  ConcursAI - Scraping Automático
echo ========================================
echo.

echo [INFO] Iniciando sistema de coleta...
echo.

REM Inicia o scheduler em segundo plano
start /B python scrapers\scraper_scheduler.py

echo [OK] Scheduler iniciado em background!
echo.
echo  - Coleta agendada diariamente
echo  - Logs salvos em: scraper.log
echo  - Para parar: Ctrl+C no terminal ou pela interface
echo.

pause
