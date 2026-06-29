@echo off
chcp 65001 > nul
echo ============================================================
echo  🎓 PROCESSADOR DE QUESTÕES E GABARITOS
echo ============================================================
echo.
echo Este script vai:
echo   1. Organizar provas e gabaritos baixados
echo   2. Extrair questões das provas
echo   3. Associar com respostas dos gabaritos
echo   4. Criar chunks Q^&A para treinamento
echo   5. Indexar no ChromaDB
echo.
echo ============================================================
echo.

cd /d "%~dp0"

python processar_questoes_gabaritos.py

echo.
echo ============================================================
echo  ✅ PROCESSO FINALIZADO
echo ============================================================
pause
