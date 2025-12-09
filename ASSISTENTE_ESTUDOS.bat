@echo off
chcp 65001 > nul
echo ============================================================
echo  🎓 ASSISTENTE INTELIGENTE DE ESTUDOS
echo ============================================================
echo.
echo Sistema conversacional com IA que:
echo   • Analisa profundamente as 3 bancas
echo   • Recomenda estratégias personalizadas
echo   • Identifica o que mais cai
echo   • Detecta armadilhas e padrões
echo   • Compara estilos das bancas
echo   • Sugere métodos de estudo otimizados
echo.
echo ============================================================
echo.

cd /d "%~dp0"

python assistente_estudos_inteligente.py

pause
