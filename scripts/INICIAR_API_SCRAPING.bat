@echo off
title ConcursAI - API com Scraping
color 0A
echo ========================================
echo   ConcursAI - Iniciando API
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Verificando dependencias...
python -c "import apscheduler; print('✓ APScheduler OK')" 2>nul
if %errorlevel% neq 0 (
    echo ✗ APScheduler nao instalado!
    echo.
    echo Instalando dependencias...
    pip install APScheduler scrapy beautifulsoup4 requests lxml html5lib --quiet
    echo ✓ Dependencias instaladas!
    echo.
)

echo [2/3] Testando scrapers...
python -c "from scrapers.scraper_scheduler import ScraperScheduler; print('✓ Scrapers OK')" 2>nul
if %errorlevel% neq 0 (
    echo ! Aviso: Pode haver problemas com scrapers
    echo ! Continuando mesmo assim...
)

echo [3/3] Iniciando API FastAPI...
echo.
echo ========================================
echo   API rodando em http://localhost:8000
echo   Scraping: http://localhost:8000/scraping/status
echo ========================================
echo.
echo Pressione Ctrl+C para parar
echo.

python api_fastapi.py

pause
