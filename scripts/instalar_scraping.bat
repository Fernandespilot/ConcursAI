@echo off
echo ========================================
echo  Instalando Dependencias do Scraping
echo ========================================
echo.

echo [1/6] Instalando Scrapy...
pip install scrapy --quiet
if %errorlevel% == 0 (
    echo ✓ Scrapy instalado
) else (
    echo ✗ Erro ao instalar Scrapy
)

echo [2/6] Instalando BeautifulSoup4...
pip install beautifulsoup4 --quiet
if %errorlevel% == 0 (
    echo ✓ BeautifulSoup4 instalado
) else (
    echo ✗ Erro ao instalar BeautifulSoup4
)

echo [3/6] Instalando Requests...
pip install requests --quiet
if %errorlevel% == 0 (
    echo ✓ Requests instalado
) else (
    echo ✗ Erro ao instalar Requests
)

echo [4/6] Instalando APScheduler...
pip install APScheduler --quiet
if %errorlevel% == 0 (
    echo ✓ APScheduler instalado
) else (
    echo ✗ Erro ao instalar APScheduler
)

echo [5/6] Instalando lxml...
pip install lxml --quiet
if %errorlevel% == 0 (
    echo ✓ lxml instalado
) else (
    echo ✗ Erro ao instalar lxml
)

echo [6/6] Instalando html5lib...
pip install html5lib --quiet
if %errorlevel% == 0 (
    echo ✓ html5lib instalado
) else (
    echo ✗ Erro ao instalar html5lib
)

echo.
echo ========================================
echo  Testando instalacao...
echo ========================================
echo.

python test_scraping_deps.py

echo.
echo ========================================
echo  Instalacao concluida!
echo ========================================
pause
