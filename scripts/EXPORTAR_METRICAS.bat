@echo off
REM ========================================
REM EXPORTAR MÉTRICAS DO MODELO
REM ========================================

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║           💾 EXPORTAR MÉTRICAS PARA JSON                  ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

python visualizar_metricas.py --export

echo.
echo ✅ Métricas exportadas!
echo.
pause
