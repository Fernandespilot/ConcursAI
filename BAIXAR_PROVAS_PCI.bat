@echo off
chcp 65001 > nul
echo ============================================================
echo  🔽 BAIXADOR E PROCESSADOR DE PROVAS PCI CONCURSOS
echo ============================================================
echo.
echo Este script vai:
echo   1. Buscar concursos no PCI Concursos
echo   2. Baixar PDFs das provas e gabaritos
echo   3. Processar os PDFs em chunks
echo   4. Indexar no ChromaDB
echo.
echo ============================================================
echo.

cd /d "%~dp0"

python baixar_provas_pci.py

echo.
echo ============================================================
echo  ✅ PROCESSO FINALIZADO
echo ============================================================
pause
