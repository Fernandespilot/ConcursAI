@echo off
chcp 65001 > nul
echo ============================================================
echo  🎯 ANÁLISE COMPLETA DE BANCAS
echo  CEBRASPE ^| FGV ^| FCC
echo ============================================================
echo.
echo Este script vai analisar:
echo   • Distribuição de áreas e disciplinas
echo   • Padrões das questões
echo   • Análise de gabaritos (viés de alternativas)
echo   • Palavras-chave mais cobradas
echo   • Complexidade das questões
echo   • Estilo de redação de cada banca
echo   • Comparação entre as 3 bancas
echo.
echo ============================================================
echo.

cd /d "%~dp0"

python analisar_bancas_completo.py

echo.
echo ============================================================
echo  ✅ ANÁLISE FINALIZADA
echo ============================================================
pause
