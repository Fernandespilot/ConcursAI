@echo off
REM ========================================
REM VISUALIZAR MÉTRICAS DO MODELO
REM ========================================

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║           📊 MÉTRICAS DO MODELO - ÚLTIMAS 24H             ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

python visualizar_metricas.py --last-hours 24

echo.
pause
