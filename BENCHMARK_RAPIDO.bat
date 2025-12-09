@echo off
REM ========================================
REM BENCHMARK DO MODELO - TESTE RÁPIDO
REM ========================================

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║           🎯 BENCHMARK RÁPIDO - 10 PERGUNTAS             ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

python benchmark_modelo.py --num 10

echo.
echo ✅ Benchmark concluído! Veja os resultados acima.
echo.
pause
