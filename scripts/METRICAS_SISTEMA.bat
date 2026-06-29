@echo off
chcp 65001 > nul
echo ============================================================
echo  📊 SISTEMA DE MÉTRICAS AVANÇADAS
echo ============================================================
echo.
echo Este sistema analisa:
echo   • Cobertura de conteúdo por banca e área
echo   • Qualidade da base de conhecimento
echo   • Gaps e pontos de melhoria
echo   • Métricas de completude e diversidade
echo   • Plano de ação para otimização
echo.
echo ============================================================
echo.

cd /d "%~dp0"

python sistema_metricas_avancadas.py

echo.
pause
